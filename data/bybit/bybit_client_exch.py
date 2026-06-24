import sys
import time
import pandas as pd
from pybit.unified_trading import HTTP
from cryptosight.utils.logger import get_logger

logger = get_logger("BybitClient")

class BybitClient:
    """
    Bybit Client focusing strictly on data fetching.
    """
    
    def __init__(self):
        # Initialize sync HTTP session (testnet=False for mainnet)
        self.session = HTTP(testnet=False)

    def fetch_raw_candles(self, symbol: str, timeframe: str, start_time: str, end_time: str = "now", max_retries: int = 5, retry_delay: int = 3) -> list:
        # Convert start and end times to millisecond timestamps using pandas
        dt_start = pd.to_datetime(start_time, format="%Y-%m-%d %H:%M:%S", utc=True)
        since = int(dt_start.value // 10**6)
        
        if not end_time or end_time == "now":
            end_limit = int(time.time() * 1000)
        else:
            dt_end = pd.to_datetime(end_time, format="%Y-%m-%d %H:%M:%S", utc=True)
            end_limit = int(dt_end.value // 10**6)
            
        # Dynamically convert timeframe (e.g. "1m" -> "1", "1h" -> "60", "1d" -> "D")
        interval = timeframe.lower()
        if "m" in interval:
            interval = interval.replace("m", "")
        elif "h" in interval:
            interval = str(int(interval.replace("h", "")) * 60)
        elif "d" in interval:
            interval = "D"
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        bybit_symbol = f"{symbol.upper()}USDT"
        logger.info(f"Fetching historical candles for {bybit_symbol} from {start_time} to {end_time}...")
        
        all_candles = []
        while since < end_limit:
            retries = 0
            response = None
            while retries < max_retries:
                try:
                    response = self.session.get_kline(
                        category="spot",
                        symbol=bybit_symbol,
                        interval=interval,
                        start=since,
                        end=end_limit,
                        limit=1000
                    )
                    if response.get("retCode") != 0:
                        raise ValueError(f"Bybit API error: {response.get('retMsg')}")
                    break
                except Exception as e:
                    retries += 1
                    logger.warning(f"Error fetching from Bybit (Attempt {retries}/{max_retries}): {e}")
                    if retries < max_retries:
                        time.sleep(retry_delay)
                    else:
                        logger.error("Max retries reached. Bybit data fetch failed.")
                        raise e
            
            klines = response.get("result", {}).get("list", [])
            if not klines:
                break
                
            # Bybit returns newest first; reverse it
            klines.reverse()
            batch = []
            for k in klines:
                batch.append([
                    int(k[0]),     # Timestamp in ms
                    float(k[1]),   # Open
                    float(k[2]),   # High
                    float(k[3]),   # Low
                    float(k[4]),   # Close
                    float(k[5])    # Volume
                ])
            all_candles.extend(batch)
            
            last_ts = batch[-1][0]
            # Exit loop if we stop advancing
            if last_ts <= since:
                break
            since = last_ts + 1
            time.sleep(0.05)
            
        logger.info(f"Fetched {len(all_candles)} raw candles from Bybit.")
        return all_candles

if __name__ == "__main__":
    bybit_client = BybitClient()
    try:
        # Fetch some candles from a specific range to test
        test_candles = bybit_client.fetch_raw_candles(
            symbol="BTC", 
            timeframe="1m", 
            start_time="2026-06-20 00:00:00", 
            end_time="2026-06-21 00:00:00",
            max_retries=3,
            retry_delay=2
        )
        if test_candles:
            logger.info(f"Sample candle: {test_candles[0]}")
            logger.info(f"Last candle: {test_candles[-1]}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
