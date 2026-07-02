import sys
import os
from pathlib import Path

# Add project root to sys.path so standalone execution works
sys.path.insert(0, os.path.abspath("../../.."))

from cryptosight.data.downloader import run_pipeline
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config, log_config

logger = get_logger("BinanceMain")


class Main:
    def __init__(self, config_name: str = "config.yaml"):
        config_path = Path(__file__).parent / config_name
        self.cfg = load_config(config_path)
        log_config(logger, self.cfg)

    def main(self):
        """Runs Binance ingestion pipeline for all configured symbols."""
        logger.info("--- Starting Binance Ingestion Pipeline ---")

        for symbol in self.cfg["symbols"]:
            try:
                run_pipeline(
                    exchange=self.cfg["exchange"],
                    symbol=symbol,
                    timeframe=self.cfg["timeframe"],
                    start_time=self.cfg["start_time"],
                    end_time=self.cfg["end_time"],
                    max_retries=self.cfg["max_retries"],
                    retry_delay=self.cfg["retry_delay"],
                    fill_method=self.cfg["fill_method"],
                    target_timeframe=self.cfg["target_timeframe"],
                )
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {e}")

        logger.info("--- Binance Ingestion Pipeline Finished ---")


if __name__ == "__main__":
    pipeline = Main()
    pipeline.main()
