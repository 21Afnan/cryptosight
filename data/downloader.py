import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import (
    get_connection, create_schema_and_table,
    insert_ohlcv, get_latest_timestamp, get_earliest_timestamp, get_table_names
)
from cryptosight.data.binance.binance_client import BinanceClient
from cryptosight.data.bybit.bybit_client import BybitClient
from cryptosight.utils.config import normalize_timestamp
from cryptosight.utils.metadata import upsert_market_data

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
        Resumes from the latest stored timestamp if data already exists in DB,
        and fetches historical gaps if start_time is earlier than the earliest DB timestamp.
        """
        conn = get_connection()
        try:
            create_schema_and_table(conn, self.exchange, self.symbol, self.timeframe)

            latest_ts   = get_latest_timestamp(conn, self.exchange, self.symbol, self.timeframe)
            earliest_ts = get_earliest_timestamp(conn, self.exchange, self.symbol, self.timeframe)

            # Check if start_time is earlier than stored earliest_ts
            if earliest_ts and start_time:
                req_start_dt = pd.to_datetime(start_time, utc=True)
                earliest_dt = pd.to_datetime(earliest_ts, utc=True)
                if req_start_dt < earliest_dt:
                    logger.info(f"Historical gap detected ({start_time} to {earliest_ts}). Downloading historical gap...")
                    hist_df = self.client.fetch_candles(
                        symbol=self.symbol, timeframe=self.timeframe,
                        start_time=start_time, end_time=pd.to_datetime(earliest_ts, utc=True).strftime("%Y-%m-%d %H:%M:%S"),
                        max_retries=max_retries, retry_delay=retry_delay,
                    )
                    if not hist_df.empty:
                        hist_df = hist_df.set_index("timestamp")
                        cols = ["open", "high", "low", "close"]
                        hist_df["volume"] = hist_df["volume"].fillna(0.0)
                        if fill_method == "ffill":
                            hist_df[cols] = hist_df[cols].ffill().bfill()
                        insert_ohlcv(conn, self.exchange, self.symbol, self.timeframe, list(hist_df.itertuples(index=True, name=None)))

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

            if not df.empty:
                df = df.set_index("timestamp")
                if (not end_time or end_time == "now") and len(df) > 1:
                    df = df.iloc[:-1]  # drop unclosed live candle when fetching up to 'now'

                if not df.empty:
                    cols = ["open", "high", "low", "close"]
                    df["volume"] = df["volume"].fillna(0.0)
                    if fill_method == "ffill":
                        df[cols] = df[cols].ffill().bfill()

                    insert_ohlcv(conn, self.exchange, self.symbol, self.timeframe, list(df.itertuples(index=True, name=None)))

            upsert_market_data(conn, self.exchange, self.symbol, self.timeframe)

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
        Returns a complete, clean OHLCV DataFrame by checking both historical start_time gaps and forward end_time gaps.
        """
        conn = get_connection()
        try:
            latest_ts   = get_latest_timestamp(conn, self.exchange, self.symbol, self.timeframe)
            earliest_ts = get_earliest_timestamp(conn, self.exchange, self.symbol, self.timeframe)

            # Check if start_time is earlier than DB earliest_ts
            if earliest_ts and start_time:
                req_start_dt = pd.to_datetime(start_time, utc=True)
                earliest_dt  = pd.to_datetime(earliest_ts, utc=True)
                if req_start_dt < earliest_dt:
                    logger.info(f"Fetching historical gap prior to DB: {start_time} to {earliest_ts}")
                    hist_df = self.client.fetch_candles(
                        symbol=self.symbol, timeframe=self.timeframe,
                        start_time=start_time, end_time=pd.to_datetime(earliest_ts, utc=True).strftime("%Y-%m-%d %H:%M:%S"),
                        max_retries=max_retries, retry_delay=retry_delay,
                    )
                    if not hist_df.empty:
                        hist_df = hist_df.set_index("timestamp")
                        cols = ["open", "high", "low", "close"]
                        hist_df["volume"] = hist_df["volume"].fillna(0.0)
                        insert_ohlcv(conn, self.exchange, self.symbol, self.timeframe, list(hist_df.itertuples(index=True, name=None)))

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
        end_str = normalize_timestamp(end_time)

        new_df = self.client.fetch_candles(
            symbol=self.symbol, timeframe=self.timeframe,
            start_time=fetch_from, end_time=end_str,
            max_retries=max_retries, retry_delay=retry_delay,
        )

        if not new_df.empty:
            new_df = new_df.set_index("timestamp")
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

        # Step 5 — drop last candle (always unclosed / still forming)
        if len(merged_df) > 1:
            merged_df = merged_df.iloc[:-1].copy()
            logger.info("Dropped last candle (unclosed/live).")
        else:
            merged_df = merged_df.copy()

        # Step 6 — fill missing values
        merged_df["volume"] = merged_df["volume"].fillna(0.0)
        merged_df[["open", "high", "low", "close"]] = merged_df[["open", "high", "low", "close"]].ffill().bfill()

        # Step 7 — slice to requested start_time and end_time range
        if start_time:
            start_dt = pd.to_datetime(start_time, utc=True)
            merged_df = merged_df[merged_df.index >= start_dt].copy()
        if end_time and end_time != "now":
            end_dt = pd.to_datetime(end_time, utc=True)
            merged_df = merged_df[merged_df.index <= end_dt].copy()

        logger.info(f"get_data() ready --> {len(merged_df)} candles ({merged_df.index.min()} to {merged_df.index.max()})")
        return merged_df

    def resample(self, target_timeframe: str, start_time: str, end_time: str, max_retries: int, retry_delay: int) -> tuple:
        original_df = self.get_data(start_time=start_time, end_time=end_time, max_retries=max_retries, retry_delay=retry_delay)

        if original_df.empty:
            logger.warning("No data to resample.")
            return pd.DataFrame(), pd.DataFrame()

        # Convert crypto minute abbreviation ('5m') to pandas frequency ('5min')
        pandas_freq = target_timeframe
        if target_timeframe.endswith("m") and not target_timeframe.endswith("min"):
            pandas_freq = target_timeframe[:-1] + "min"

        resampled_df = original_df.resample(pandas_freq).agg({
            "open":   "first",
            "high":   "max",
            "low":    "min",
            "close":  "last",
            "volume": "sum",
        })

        logger.info(f"Resampled to [{target_timeframe}] — {len(resampled_df)} candles.")

        # Save resampled data to DB (uncomment to enable)
        # conn = get_connection()
        # try:
        #     create_schema_and_table(conn, self.exchange, self.symbol, target_timeframe)
        #     insert_ohlcv(conn, self.exchange, self.symbol, target_timeframe, list(resampled_df.itertuples(index=True, name=None)))
        #     logger.info(f"Saved resampled [{target_timeframe}] data to DB.")
        # finally:
        #     conn.close()

        return original_df, resampled_df

def run_pipeline(
    exchange: str,
    symbol: str,
    timeframe: str,
    start_time: str,
    end_time: str,
    max_retries: int,
    retry_delay: int,
    fill_method: str,
    target_timeframe: str,
):
    """
    One-stop Master Pipeline Function:
    Creates Downloader object internally and runs download, get_data, or resample in a single call.
    """
    dl = Downloader(exchange=exchange, symbol=symbol, timeframe=timeframe)
    logger.info(f"Running master pipeline for {dl.exchange.upper()} | {dl.symbol.upper()} [{dl.timeframe}]")

    # 1. DOWNLOAD & SAVE TO DB (Active by default)
    dl.download(
        start_time=start_time,
        end_time=end_time,
        max_retries=max_retries,
        retry_delay=retry_delay,
        fill_method=fill_method,
    )

    # 2. GET FULL MERGED DATA IN MEMORY (Uncomment below to use)
    # df = dl.get_data(start_time=start_time, end_time=end_time, max_retries=max_retries, retry_delay=retry_delay)
    # return df

    # 3. RESAMPLE TO TARGET TIMEFRAME (save_to_db is handled inside resample() now)
    # orig_df, resampled_df = dl.resample(target_timeframe=target_timeframe, start_time=start_time, end_time=end_time, max_retries=max_retries, retry_delay=retry_delay)
    # return resampled_df
