import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Always create logs folder at project root — not relative to where you run from
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per log file

def detect_exchange(name: str) -> str:
    """
    Automatically detects if the current execution context is working with Binance or Bybit
    by checking the logger name, command line arguments, environment variables, or active YAML config.
    """
    ctx = (name + " " + " ".join(sys.argv)).lower()
    if "binance" in ctx:
        return "binance"
    if "bybit" in ctx:
        return "bybit"

    env_ex = os.environ.get("EXCHANGE", "").lower()
    if "binance" in env_ex:
        return "binance"
    if "bybit" in env_ex:
        return "bybit"

    try:
        root_dir = Path(__file__).resolve().parent.parent
        if any("backtest" in arg.lower() for arg in sys.argv):
            cfg_paths = [root_dir / "backtesting" / "backt_config.yaml"]
        else:
            cfg_paths = [
                root_dir / "signals" / "strategy_config.yaml",
                root_dir / "backtesting" / "backt_config.yaml",
                root_dir / "indicators" / "tal_Indicators_config.yaml",
                root_dir / "config" / "config.yaml"
            ]
        for cfg_path in cfg_paths:
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    for line in f.read().lower().splitlines():
                        line = line.strip()
                        if line.startswith("exchange:"):
                            if "binance" in line:
                                return "binance"
                            if "bybit" in line:
                                return "bybit"
    except Exception:
        pass
    return None


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger that writes to binance.log, bybit.log, or app.log.
    Automatically consolidates all DB, Backtester, Signals, and Indicator logs
    into the active exchange's log file (binance.log or bybit.log).
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    ex = detect_exchange(name)
    argv_str = " ".join(sys.argv) if hasattr(sys, "argv") else ""
    ctx = (name + " " + argv_str).lower()

    if "nlp" in ctx or "reddit" in ctx or "sentiment" in ctx or "bert" in ctx:
        log_file = LOG_DIR / "nlp.log"
    elif ex == "binance":
        log_file = LOG_DIR / "binance.log"
    elif ex == "bybit":
        log_file = LOG_DIR / "bybit.log"
    elif "db" in ctx:
        log_file = LOG_DIR / "db.log"
    elif "indicators" in ctx:
        log_file = LOG_DIR / "tal_Indicators.log"
    else:
        log_file = LOG_DIR / "app.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if get_logger called multiple times
    if not logger.handlers:
        logger.propagate = False
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File handler — rotates at 5MB, keeps 5 backups
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_BYTES,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler — prints to terminal as well
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger