import yaml
from pathlib import Path
import pandas as pd
import numpy as np
from cryptosight.utils.db import get_connection, fetch_ohlcv
from cryptosight.utils.logger import get_logger
from cryptosight.signals.main import run_signals_pipeline


class BacktestingEngine:
    """
    Vectorized Backtesting Engine.
    Loads configuration from backt_config.yaml and runs fully vectorized simulations.
    """

    def __init__(self, config_path: str = "backt_config.yaml"):
        self.logger = get_logger("Backtester")
        self.config_path = Path(__file__).resolve().parent / config_path
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Loads parameters from the YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def fetch_data(self) -> pd.DataFrame:
        """
        Fetches 1m OHLCV data from PostgreSQL using the fast COPY stream.
        All parameters are read from config.yaml — single source of truth.
        """
        exchange = self.config["exchange"]
        symbol = self.config["symbol"]
        timeframe = self.config["timeframe"]
        start_time = self.config["start_time"]
        end_time = self.config["end_time"]

        if not all([exchange, symbol, timeframe, start_time, end_time]):
            raise ValueError(
                "Missing required config keys: exchange, symbol, timeframe, start_time, end_time"
            )

        self.logger.info(
            f"Fetching {timeframe} data for {exchange.upper()} {symbol.upper()} "
            f"({start_time} to {end_time}) via COPY..."
        )

        conn = get_connection()
        try:
            return fetch_ohlcv(conn, exchange, symbol, timeframe, start_time, end_time)
        finally:
            conn.close()

    def run_signals(self, strategy_config_path: str = None) -> pd.DataFrame:
        """
        Executes the AI Quant signals pipeline.
        Returns a DataFrame containing only the signal column with the timestamp index.
        """
        self.logger.info("Executing vectorized signals pipeline...")
        full_df = run_signals_pipeline(config_path=strategy_config_path)
        # Keeps timestamp as the index and returns only the 'signal' column
        return full_df[["signal"]]

    def merge_data(self, ohlcv_df: pd.DataFrame, signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merges 1-minute OHLCV data with the signal DataFrame.
        Fills missing signal values with 0 (No Signal/Hold).
        """
        self.logger.info("Merging 1-minute OHLCV data with signals...")

        # Ensure indices are datetime with UTC timezone
        if ohlcv_df.index.tz is None:
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index, utc=True)
        if signals_df.index.tz is None:
            signals_df.index = pd.to_datetime(signals_df.index, utc=True)

        # Left join 1m candles with signals
        merged_df = ohlcv_df.join(signals_df[["signal"]], how="left")
        merged_df["signal"] = merged_df["signal"].fillna(0).astype(int)

        return merged_df
    def determine_entries(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 1 & 2: Locates Buy and Sell signals and calculates their Entry Prices.
        Reads execution pricing from the configuration.
        """
        self.logger.info("Determining entry signals and entry prices...")

        entry_method = self.config["entry_price"]

        if entry_method == "next_open":
            entry_price_series = merged_df["open"].shift(-1)
        elif entry_method == "current_close" or entry_method == "close":
            entry_price_series = merged_df["close"]
        else:
            raise ValueError(f"Unsupported entry_price method: '{entry_method}' in config.")

        entries_df = merged_df[merged_df["signal"] != 0]
        entries_df["entry_price"] = entry_price_series.loc[entries_df.index]
        entries_df.dropna(subset=["entry_price"], inplace=True)

        self.logger.info(f"Located {len(entries_df)} entry signals with entry prices.")
        return entries_df

    def calculate_position_size(self, entries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 3: Calculates quantity for each trade based on fixed_percentage sizing.
        """
        self.logger.info("Calculating position sizes...")

        position_type = self.config["position_size"]["type"]
        position_value = self.config["position_size"]["value"]

        if position_type != "fixed_percentage":
            raise ValueError(f"Unsupported position_size type: {position_type}")

        balance = self.config["initial_balance"]
        position_value_amount = balance * (position_value / 100)
        entries_df["quantity"] = position_value_amount / entries_df["entry_price"]

        self.logger.info(f"Position sizing complete using {position_value}% of balance {balance}.")
        return entries_df
    def calculate_tp_sl(self, entries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 4: Calculates Take Profit and Stop Loss price levels for every trade.
        """
        self.logger.info("Calculating TP/SL levels...")

        tp_type = self.config["take_profit"]["type"]
        sl_type = self.config["stop_loss"]["type"]

        if tp_type != "percentage":
            raise ValueError(f"Unsupported take_profit type: {tp_type}")
        if sl_type != "percentage":
            raise ValueError(f"Unsupported stop_loss type: {sl_type}")

        tp_pct = self.config["take_profit"]["value"] / 100
        sl_pct = self.config["stop_loss"]["value"] / 100

        is_long = entries_df["signal"] == 1

        entries_df["take_profit"] = np.where(
            is_long,
            entries_df["entry_price"] * (1 + tp_pct),
            entries_df["entry_price"] * (1 - tp_pct),
        )
        entries_df["stop_loss"] = np.where(
            is_long,
            entries_df["entry_price"] * (1 - sl_pct),
            entries_df["entry_price"] * (1 + sl_pct),
        )

        self.logger.info("TP/SL levels calculated.")
        return entries_df

    



if __name__ == "__main__":
    print("=" * 55)
    print("           RUNNING BACKTEST ENGINE TEST")
    print("=" * 55)

    # Initialize the engine
    engine = BacktestingEngine()

    # 1. Fetch 1m OHLCV Data
    ohlcv_df = engine.fetch_data()

    # 2. Run signals
    signals_df = engine.run_signals()

    if ohlcv_df.empty:
        print("[FAILED] Could not retrieve OHLCV data.")
    elif signals_df.empty:
        print("[FAILED] Could not retrieve signals.")
    else:
        # 3. Merge OHLCV and signals
        merged_df = engine.merge_data(ohlcv_df, signals_df)
        print(f"\n[SUCCESS] Successfully merged data: {len(merged_df)} rows.")

        # 4. Determine Entries and Entry Prices (Step 1 & 2)
        entries_df = engine.determine_entries(merged_df)
        print(f"\n[SUCCESS] Located {len(entries_df)} potential trade entries.")
        print("\n--- Last 10 potential entries with Entry Prices (Open(t+1)) ---")
        print(entries_df[["open", "signal", "entry_price"]].tail(10))
    print("=" * 55)
