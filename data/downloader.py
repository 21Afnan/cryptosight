import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import (
    get_connection, create_schema_and_table,
    insert_ohlcv, get_latest_timestamp, get_table_names
)
from cryptosight.data.binance.binance_client import BinanceClient
from cryptosight.data.bybit.bybit_client import BybitClient

logger = get_logger("Downloader")


class Downloader:
    """
    Handles downloading, merging, and resampling of OHLCV candlestick data.

    Usage:
        dl = Downloader("binance", "btc", "1h")
        dl.download(start_time="2026-01-01 00:00:00", end_time="now")
        full_df = dl.get_data(end_time="now")
        original_df, resampled_df = dl.resample(target_timeframe="4h")
    """

    def __init__(self, exchange: str, symbol: str, timeframe: str):
        self.exchange  = exchange.lower().strip()
        self.symbol    = symbol.lower().strip()
        self.timeframe = timeframe

        if self.exchange == "binance":
            self.client = BinanceClient()
        elif self.exchange == "bybit":
            self.client = BybitClient()
        else:
            raise ValueError(f"Unsupported exchange: '{self.exchange}'. Choose 'binance' or 'bybit'.")

    def download(
        self,
        start_time:  str,
        end_time:    str,
        max_retries: int,
        retry_delay: int,
        fill_method: str,
    ) -> None:
        """
        Downloads OHLCV candles from the exchange and saves them to the database.
        Resumes from the latest stored timestamp if data already exists in DB.
        """
        conn = get_connection()
        try:
            create_schema_and_table(conn, self.exchange, self.symbol, self.timeframe)

            latest_ts  = get_latest_timestamp(conn, self.exchange, self.symbol, self.timeframe)
            fetch_from = (
                pd.to_datetime(latest_ts, utc=True).strftime("%Y-%m-%d %H:%M:%S")
                if latest_ts else start_time
            )

            logger.info(f"Downloading {self.symbol.upper()} [{self.timeframe}] | {fetch_from} to {end_time}")

            df = self.client.fetch_candles(
                symbol=self.symbol, timeframe=self.timeframe,
                start_time=fetch_from, end_time=end_time,
                max_retries=max_retries, retry_delay=retry_delay,
            )

            if df.empty:
                logger.info("No new candles returned from exchange.")
                return

            df = df.set_index("timestamp").iloc[:-1]  # drop unclosed live candle

            if df.empty:
                logger.info("No completed candles to save.")
                return
            
            cols=["open", "high", "low", "close"]
            
            # Fill missing values inline
            df["volume"] = df["volume"].fillna(0.0)
            if fill_method == "ffill":
                df[cols] = df[cols].ffill()

            insert_ohlcv(conn, self.exchange, self.symbol, self.timeframe, list(df.itertuples(index=True, name=None)))

        except Exception as e:
            logger.error(f"download() failed: {e}")
            raise
        finally:
            conn.close()

    def get_data(
        self,
        start_time:  str,
        end_time:    str,
        max_retries: int,
        retry_delay: int,
    ) -> pd.DataFrame:
        """
        Returns a complete, clean OHLCV DataFrame by:
          1. Finding the latest timestamp in DB via get_latest_timestamp().
          2. Fetching only the gap (latest_ts to end_time) from the exchange.
          3. Loading all existing DB rows and merging with the new data.
        """
        conn = get_connection()
        try:
            # Step 1 — find where the gap starts
            latest_ts = get_latest_timestamp(conn, self.exchange, self.symbol, self.timeframe)

            if latest_ts:
                fetch_from = pd.to_datetime(latest_ts, utc=True).strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Latest DB timestamp: {fetch_from} | Fetching gap to {end_time}.")
            else:
                logger.warning(f"DB is empty — fetching from start_time: {start_time}.")
                fetch_from = start_time

            # Step 2 — load all stored DB rows
            schema, table = get_table_names(self.exchange, self.symbol, self.timeframe)
            query = f"SELECT timestamp, open, high, low, close, volume FROM {schema}.{table} ORDER BY timestamp ASC;"

            try:
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                db_df = pd.DataFrame(rows, columns=cols)
                if not db_df.empty:
                    db_df["timestamp"] = pd.to_datetime(db_df["timestamp"], utc=True)
                    db_df = db_df.set_index("timestamp")
                    db_df = db_df.astype(float)   # cast Decimal → float for pandas ops
                    logger.info(f"Loaded {len(db_df)} candles from DB.")
            except Exception as e:
                logger.warning(f"Could not load from DB: {e}")
                db_df = pd.DataFrame()

        finally:
            conn.close()

        # Step 3 — fetch the gap from exchange
        end_str = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S") if end_time == "now" else end_time

        new_df = self.client.fetch_candles(
            symbol=self.symbol, timeframe=self.timeframe,
            start_time=fetch_from, end_time=end_str,
            max_retries=max_retries, retry_delay=retry_delay,
        )

        if not new_df.empty:
            new_df = new_df.set_index("timestamp").iloc[:-1]  # drop unclosed live candle
            logger.info(f"Fetched {len(new_df)} new candles from {self.exchange.upper()}.")

        # Step 4 — merge DB + new data
        if db_df.empty and new_df.empty:
            logger.warning("No data available.")
            return pd.DataFrame()
        elif db_df.empty:
            merged_df = new_df
        elif new_df.empty:
            merged_df = db_df
        else:
            merged_df = pd.concat([db_df, new_df])
            merged_df = merged_df[~merged_df.index.duplicated(keep="last")].sort_index()

        # Step 5 — fill missing values
        merged_df["volume"] = merged_df["volume"].fillna(0.0)
        merged_df[["open", "high", "low", "close"]] = merged_df[["open", "high", "low", "close"]].ffill()

        logger.info(f"get_data() ready --> {len(merged_df)} candles ({merged_df.index.min()} to {merged_df.index.max()})")
        return merged_df

    def resample(self, target_timeframe: str, start_time: str, end_time: str, max_retries: int, retry_delay: int) -> tuple:
        original_df = self.get_data(start_time=start_time, end_time=end_time, max_retries=max_retries, retry_delay=retry_delay)

        if original_df.empty:
            logger.warning("No data to resample.")
            return pd.DataFrame(), pd.DataFrame()

        resampled_df = original_df.resample(target_timeframe).agg({
            "open":   "first",
            "high":   "max",
            "low":    "min",
            "close":  "last",
            "volume": "sum",
        })

        logger.info(f"Resampled to [{target_timeframe}] — {len(resampled_df)} candles.")
        return original_df, resampled_df

