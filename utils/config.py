import yaml
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
