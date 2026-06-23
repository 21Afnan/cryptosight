import os
import sys
import time
from pathlib import Path

# Add project root to path to resolve 'utils' imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from binance import Client
from utils.logger import get_logger

logger = get_logger("BinanceClient")

class BinanceClient:
    """
    Binance client using the native python-binance library.
    """
    
    def __init__(self):
        # Initialize the sync client (no API keys needed for public historical klines)
        self.client = Client()
        
    def fetch_raw_candles(self, symbol: str, timeframe: str, start_time: str, end_time: str , max_retries: int, retry_delay: int ) -> list:
        """
        Fetches historical candles from Binance with retry logic.
        - symbol: 'BTC' -> converted to 'BTCUSDT'
        - timeframe: '1m', '1h', etc.
        - start_time: '2023-06-23 00:00:00'
        - end_time: 'now' or a specific date string
        """
        # Format symbol for Binance Spot API (e.g., BTC/USDT -> BTCUSDT)
        binance_symbol = symbol.upper().replace("/", "")
        if not binance_symbol.endswith("USDT") and "USDT" not in binance_symbol:
            binance_symbol = f"{binance_symbol}USDT"
        
        # If end_time is "now", we pass None to let python-binance fetch up to the latest candle
        end_str = None if end_time == "now" else end_time
        
        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"Fetching historical candles for {binance_symbol} from {start_time} to {end_time}...")
                
                # get_historical_klines automatically handles string dates and pagination
                raw_klines = self.client.get_historical_klines(
                    symbol=binance_symbol,
                    interval=timeframe,
                    start_str=start_time,
                    end_str=end_str
                )
                
                if not raw_klines:
                    return []
                
                # Format to list of list containing: [timestamp_ms, open, high, low, close, volume]
                processed_candles = []
                for k in raw_klines:
                    processed_candles.append([
                        int(k[0]),        # Open time (ms)
                        float(k[1]),      # Open
                        float(k[2]),      # High
                        float(k[3]),      # Low
                        float(k[4]),      # Close
                        float(k[5])       # Volume
                    ])
                    
                logger.info(f"Fetched {len(processed_candles)} raw candles from Binance.")
                return processed_candles
                
            except Exception as e:
                retries += 1
                logger.warning(f"Error fetching from Binance (Attempt {retries}/{max_retries}): {e}")
                if retries < max_retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Binance data fetch failed.")
                    raise e

if __name__ == "__main__":
    # Simple self-test setup
    binance_client = BinanceClient()
    try:
        # Fetch some candles from a specific range to test
        test_candles = binance_client.fetch_raw_candles(
            symbol="BTC", 
            timeframe="1h", 
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
