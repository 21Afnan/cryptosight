import yaml
import os
import pandas as pd
from pathlib import Path
from logging import Logger
from dotenv import load_dotenv

def load_environment() -> Path:
    """
    Loads environment variables from the .env file located at the cryptosight root.
    Returns the path to the loaded .env file.
    """
    current_dir = Path(__file__).resolve().parent
    env_path = current_dir.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    return env_path

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
    logger.info(f"Target Timeframe : {config.get('target_timeframe')}")


def normalize_timestamp(timestamp_str: str) -> str:
    """
    Converts 'now' (or None/empty) into a standard UTC string: 'YYYY-MM-DD HH:MM:SS'.
    Passes valid historical date strings through untouched.
    """
    if not timestamp_str or timestamp_str.lower().strip() == "now":
        return pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S")
    return timestamp_str


def get_ml_artifacts_dir(asset_type: str) -> Path:
    """
    Returns the resolved path to the specific subfolder inside local repository's
    'ml/artifacts/' directory based on asset_type, creating it if it doesn't exist.
    """
    mapping = {
        "config": "configs",
        "model": "models",
        "preprocessor": "preprocessors",
        "scaler": "preprocessors",
        "metadata": "metadata",
        "report": "reports"
    }
    subfolder = mapping.get(asset_type.lower().strip(), "metadata")
    
    # Resolve relative to the cryptosight project root directory
    root_dir = Path(__file__).resolve().parent.parent
    artifacts_dir = root_dir / "ml" / "artifacts" / subfolder
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir


def save_config_artifact(config_data: dict, filename: str, asset_type: str = "config") -> Path:
    """
    Saves a configuration or metadata dictionary as a YAML file to the designated
    subfolder inside the local repository's 'ml/artifacts/' directory.
    """
    target_dir = get_ml_artifacts_dir(asset_type)
    target_path = target_dir / filename
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)
        return target_path
    except Exception as e:
        print(f"Warning: Failed to save config YAML artifact to {target_path}: {e}")
        return None


