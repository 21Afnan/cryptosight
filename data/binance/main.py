import sys
import yaml
from pathlib import Path

# Add project root to sys.path to resolve 'utils' imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.downloader import download_exchange_data
from utils.logger import get_logger

logger = get_logger("BinanceMain")

def main(exchange: str, symbols: list, timeframe: str, start_time: str, end_time: str, max_retries: int, retry_delay: int):
    """
    Main runner for Binance ingestion.
    """
    logger.info(f"--- Starting Binance Ingestion Pipeline ---")
    
    # Run downloader for each configured symbol
    for symbol in symbols:
        try:
            download_exchange_data(
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
        except Exception as e:
            logger.error(f"Failed to process symbol {symbol}: {e}")

    logger.info("--- Binance Ingestion Pipeline Finished ---")

if __name__ == "__main__":
    # Load configuration from config.yaml
    config_path = Path(__file__).resolve().parent / "config.yaml"
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
        
    main(
        exchange=config.get("exchange"),
        symbols=config.get("symbols", []),
        timeframe=config.get("timeframe"),
        start_time=config.get("start_time"),
        end_time=config.get("end_time"),
        max_retries=config.get("max_retries", 5),
        retry_delay=config.get("retry_delay", 3)
    )
