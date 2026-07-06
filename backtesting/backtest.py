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

    def determine_exits(self, merged_df: pd.DataFrame, entries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 4 (Part 2): Determines the exit price and exit time for each trade entry.
        Scans future 1-minute candles to detect where TP or SL is hit first.
        """
        self.logger.info("Determining exit prices and times...")

        ohlcv_times = merged_df.index
        ohlcv_highs = merged_df["high"].values
        ohlcv_lows = merged_df["low"].values
        ohlcv_closes = merged_df["close"].values

        # Map timestamps to integer indices for fast slicing
        time_to_idx = {t: i for i, t in enumerate(ohlcv_times)}

        exit_prices = []
        exit_times = []
        exit_reasons = []

        for entry_time, row in entries_df.iterrows():
            entry_price = row["entry_price"]
            tp_price = row["take_profit"]
            sl_price = row["stop_loss"]
            direction = int(row["signal"])  # 1 for Long, -1 for Short

            # Find starting index of the trade (execution starts at t+1 candle index)
            start_idx = time_to_idx[entry_time] + 1
            if start_idx >= len(ohlcv_times):
                # No data after entry, exit immediately at entry_price
                exit_prices.append(entry_price)
                exit_times.append(entry_time)
                exit_reasons.append("end_of_data")
                continue

            # Slice future candles
            highs_slice = ohlcv_highs[start_idx:]
            lows_slice = ohlcv_lows[start_idx:]

            # Vectorized search for SL and TP hits
            if direction == 1:  # Long
                tp_hits = highs_slice >= tp_price
                sl_hits = lows_slice <= sl_price
            else:  # Short
                tp_hits = lows_slice <= tp_price
                sl_hits = highs_slice >= sl_price

            tp_indices = np.where(tp_hits)[0]
            sl_indices = np.where(sl_hits)[0]

            tp_first_idx = tp_indices[0] if len(tp_indices) > 0 else len(highs_slice)
            sl_first_idx = sl_indices[0] if len(sl_indices) > 0 else len(highs_slice)

            # Determine which occurred first
            if tp_first_idx == len(highs_slice) and sl_first_idx == len(highs_slice):
                # Neither hit, exit at last candle close
                exit_offset = len(highs_slice) - 1
                exit_price = ohlcv_closes[-1]
                exit_reason = "end_of_data"
            elif tp_first_idx < sl_first_idx:
                exit_offset = tp_first_idx
                exit_price = tp_price
                exit_reason = "take_profit"
            elif sl_first_idx < tp_first_idx:
                exit_offset = sl_first_idx
                exit_price = sl_price
                exit_reason = "stop_loss"
            else:
                # Both hit in the same candle -> assume SL hit for conservatism
                exit_offset = tp_first_idx
                exit_price = sl_price
                exit_reason = "stop_loss_same_candle"

            exit_idx = start_idx + exit_offset
            exit_prices.append(exit_price)
            exit_times.append(ohlcv_times[exit_idx])
            exit_reasons.append(exit_reason)

        # Assign calculated exits to entries_df
        entries_df = entries_df.copy()
        entries_df["exit_price"] = exit_prices
        entries_df["exit_time"] = exit_times
        entries_df["exit_reason"] = exit_reasons

        self.logger.info(f"Exits determined for {len(entries_df)} trades.")
        return entries_df

    
    
    def calculate_fees_and_pnl(self, entries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 5 & 6: Calculates commission, slippage, and net PnL for each trade.
        """
        self.logger.info("Calculating PnL, commissions, and slippage...")

        commission_rate = self.config["commission"]
        slippage_rate = self.config["slippage"]

        # Calculate transaction values
        entry_value = entries_df["entry_price"] * entries_df["quantity"]
        exit_value = entries_df["exit_price"] * entries_df["quantity"]

        # Step 5: Apply commission and slippage (both Entry and Exit)
        entries_df["commission"] = (entry_value * commission_rate) + (exit_value * commission_rate)
        entries_df["slippage"] = (entry_value * slippage_rate) + (exit_value * slippage_rate)

        # Step 6: Calculate Profit and Loss
        is_long = entries_df["signal"] == 1
        entries_df["gross_pnl"] = np.where(
            is_long,
            (entries_df["exit_price"] - entries_df["entry_price"]) * entries_df["quantity"],
            (entries_df["entry_price"] - entries_df["exit_price"]) * entries_df["quantity"]
        )

        entries_df["net_pnl"] = entries_df["gross_pnl"] - entries_df["commission"] - entries_df["slippage"]
        
        # Calculate Percentage Net PnL (net_pnl as a percentage of initial trade investment)
        entries_df["perc_pnl"] = (entries_df["net_pnl"] / (entries_df["entry_price"] * entries_df["quantity"])) * 100

        return entries_df

    def update_balance(self, entries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 7: Updates the account balance after every completed trade.
        Calculates a running cumulative sum of PnL starting from initial_balance.
        """
        self.logger.info("Updating account balances after trades...")
        
        initial_balance = self.config["initial_balance"]
        
        # Vectorized cumulative sum of Net PnL added to the initial balance
        entries_df["balance"] = initial_balance + entries_df["net_pnl"].cumsum()
        
        return entries_df

    def run_pipeline(self) -> pd.DataFrame:
        """
        Runs the complete backtesting pipeline step-by-step:
        1. Fetch raw candles (fetch_data)
        2. Fetch generated signals (run_signals)
        3. Merge candles with signals (merge_data)
        4. Locate entries and calculate entry prices (determine_entries)
        5. Calculate initial position size/quantities (calculate_position_size)
        6. Calculate TP/SL target price levels (calculate_tp_sl)
        7. Locate when and where trades exited (determine_exits)
        8. Apply commissions, slippage, and calculate net PnL (calculate_fees_and_pnl)
        9. Update running account balances (update_balance)
        10. Save the final trade ledger to backtest_ledger.csv.
        """
        self.logger.info("Executing step-by-step backtesting pipeline...")

        # Step 1: Fetch OHLCV price candles
        ohlcv_df = self.fetch_data()

        # Step 2: Fetch strategy signals
        signals_df = self.run_signals()

        # Step 3: Merge OHLCV and signals together
        merged_df = self.merge_data(ohlcv_df, signals_df)

        # Step 4: Find entry locations and execution prices
        entries_df = self.determine_entries(merged_df)

        # Step 5: Calculate initial position sizes
        entries_df = self.calculate_position_size(entries_df)

        # Step 6: Calculate target Stop Loss and Take Profit prices
        entries_df = self.calculate_tp_sl(entries_df)

        # Step 7: Find exit times and exit prices
        entries_df = self.determine_exits(merged_df, entries_df)

        # Step 8: Apply fee frictions (commissions, slippage) and calculate Net PnL
        entries_df = self.calculate_fees_and_pnl(entries_df)

        # Step 9: Update the account balance after each trade
        ledger_df = self.update_balance(entries_df)

        # Step 10: Clean up columns and save trade ledger to CSV
        # Remove commission, slippage, gross_pnl, and dollar net_pnl from final ledger output
        cols_to_drop = ["commission", "slippage", "gross_pnl", "net_pnl"]
        ledger_df.drop(columns=[c for c in cols_to_drop if c in ledger_df.columns], inplace=True)

        output_csv = Path(__file__).resolve().parent / "backtest_ledger.csv"
        ledger_df.to_csv(output_csv)
        self.logger.info(f"Successfully saved trade ledger CSV to: {output_csv}")

        return ledger_df


if __name__ == "__main__":
    print("=" * 55)
    print("           RUNNING BACKTEST ENGINE PIPELINE")
    print("=" * 55)

    # Initialize the engine
    engine = BacktestingEngine()

    # Run the step-by-step pipeline
    ledger = engine.run_pipeline()

    print("\n" + "=" * 45)
    print("          BACKTEST RESULTS SHOWCASE")
    print("=" * 45)
    print(f"Total entries processed:  {len(ledger)}")
    print(f"Initial balance:          ${engine.config['initial_balance']:.2f}")
    if not ledger.empty:
        final_balance = ledger["balance"].iloc[-1]
        net_profit = final_balance - engine.config['initial_balance']
        print(f"Final balance:            ${final_balance:.2f}")
        print(f"Net profit:               ${net_profit:.2f}")
        print("\n--- Last 5 rows of backtest ledger ---")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(ledger[["signal", "entry_price", "take_profit", "stop_loss", "exit_price", "exit_reason", "perc_pnl", "balance"]].tail(5))
    print("=" * 55)

    




