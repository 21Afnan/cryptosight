from pathlib import Path
from cryptosight.data.downloader import Downloader
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config, log_config

logger = get_logger("BybitMain")


class Main:
    def __init__(self, config_name: str = "config.yaml"):
        config_path = Path(__file__).parent / config_name
        self.cfg = load_config(config_path)
        log_config(logger, self.cfg)

    def main(self):
        """Runs Bybit ingestion pipeline for all configured symbols."""
        logger.info("--- Starting Bybit Ingestion Pipeline ---")

        for symbol in self.cfg["symbols"]:
            try:
                dl = Downloader(
                    exchange=self.cfg["exchange"],
                    symbol=symbol,
                    timeframe=self.cfg["timeframe"],
                )
                dl.download(
                    start_time=self.cfg["start_time"],
                    end_time=self.cfg["end_time"],
                    max_retries=self.cfg["max_retries"],
                    retry_delay=self.cfg["retry_delay"],
                    fill_method=self.cfg["fill_method"],
                )
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {e}")

        logger.info("--- Bybit Ingestion Pipeline Finished ---")


if __name__ == "__main__":
    pipeline = Main()
    pipeline.main()
