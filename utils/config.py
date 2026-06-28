import yaml
import pandas as pd
from pathlib import Path
from logging import Logger

def load_config(config_path: Path | str) -> dict:
    """
    Loads and parses YAML config from the given path.
    Ensures symbols is wrapped in a list if it's a single string and
    sets standard default values for optional parameters.
    """
    path = Path(config_path)
    config = yaml.safe_load(path.read_text()) or {}
    
    # Safety check - wrap single string symbol in list
    symbols = config.get("symbols", [])
    if isinstance(symbols, str):
        config["symbols"] = [symbols]
    elif symbols is None:
        config["symbols"] = []


    return config

def log_config(logger: Logger, config: dict) -> None:
    """
    Logs configuration parameter details.
    """
    logger.info("=== Config Loaded ===")
    logger.info(f"Exchange   : {config.get('exchange')}")
    logger.info(f"Symbols    : {config.get('symbols')}")
    logger.info(f"Timeframe  : {config.get('timeframe')}")
    logger.info(f"Start Time : {config.get('start_time')}")
    logger.info(f"End Time   : {config.get('end_time')}")
    logger.info(f"Fill Method: {config.get('fill_method')}")
    logger.info(f"Max Retries: {config.get('max_retries')}")
    logger.info(f"Retry Delay: {config.get('retry_delay')}")


def normalize_timestamp(timestamp_str: str) -> str:
    """
    Converts 'now' (or None/empty) into a standard UTC string: 'YYYY-MM-DD HH:MM:SS'.
    Passes valid historical date strings through untouched.
    """
    if not timestamp_str or timestamp_str.lower().strip() == "now":
        return pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S")
    return timestamp_str
