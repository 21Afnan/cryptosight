import time
import pandas as pd
from binance import Client
from cryptosight.utils.logger import get_logger

logger = get_logger("BinanceClient")


class BinanceClient:
    """
    Fetches historical OHLCV candles from Binance Spot/Futures.
    No API keys needed for public market data.
    """

    def __init__(self):
        self.client = Client()

    def fetch_candles(
        self,
        symbol:      str,
        timeframe:   str,
        start_time:  str,
        end_time:    str,
        max_retries: int,
        retry_delay: int,
    ) -> pd.DataFrame:

        binance_symbol = f"{symbol.upper()}USDT"

        # Binance does not understand "now" — convert it to a real UTC string
        end_str = (
            pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S")
            if end_time == "now"
            else end_time
        )

        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"Fetching {binance_symbol} | {timeframe} | {start_time} → {end_str}")

                # Binance library handles all pagination internally
                raw_klines = self.client.get_historical_klines(
                    symbol=binance_symbol,
                    interval=timeframe,
                    start_str=start_time,
                    end_str=end_str
                )

                if not raw_klines:
                    logger.info("No candles returned.")
                    return pd.DataFrame()

                # Binance returns 12 fields per candle — we only need 6
                # Using named keys so column order is always explicit and clear
                candles = [
                    {
                        "timestamp": int(k[0]),     # open time in milliseconds
                        "open":      float(k[1]),
                        "high":      float(k[2]),
                        "low":       float(k[3]),
                        "close":     float(k[4]),
                        "volume":    float(k[5]),   # base asset volume (e.g. BTC)
                    }
                    for k in raw_klines
                ]

                df = pd.DataFrame(candles)
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

                logger.info(f"Done. Total candles: {len(df)}")
                return df

            except Exception as e:
                retries += 1
                logger.warning(f"Attempt {retries}/{max_retries} failed: {e}")
                if retries < max_retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Binance fetch failed.")
                    raise
