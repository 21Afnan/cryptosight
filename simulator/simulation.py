import os
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import get_connection, fetch_ohlcv
from cryptosight.signals.main import run_pipeline_from_config



class SimulatorEngine:
    """
    Sequential Event-Driven Trading Simulator Engine.
    Processes market data minute-by-minute to emulate live paper trading.
    """
    def __init__(self, config_path: str = "config.yaml"):
        self.current_dir = Path(__file__).resolve().parent
        self.config_path = self.current_dir / config_path
        self.config = self.load_config()
        self.logger = get_logger("Simulator")
        
        # Output file paths
        self.positions_csv = self.current_dir / "simulator_positions.csv"
        self.ledger_csv = self.current_dir / "simulator_ledger.csv"
        self.input_csv = self.current_dir / "simulator_input.csv"

        
        # Initialize engine state
        self.balance = self.config.get("initial_balance")
        self.initial_balance = self.balance



    def load_config(self) -> dict:
        """Loads configuration from yaml."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def fetch_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        1. Fetches target timeframe strategy signals.
        2. Fetches 1-minute OHLCV candles from PostgreSQL for the simulated timeframe.
        """
        self.logger.info("Executing signals pipeline...")
        # Override signal config market values to match simulator config
        overrides = {
            "start_time": self.config.get("start_time"),
            "end_time": self.config.get("end_time"),
            "symbol": self.config.get("symbol"),
            "exchange": self.config.get("exchange"),
        }
        
        # Run strategy signals pipeline
        signals_df = run_pipeline_from_config(market_overrides=overrides)
        
        if signals_df.empty:
            self.logger.error("No signals generated.")
            return pd.DataFrame(), pd.DataFrame()

        # Fetch 1m price data for SL/TP evaluation
        exchange = self.config["exchange"]
        symbol = self.config["symbol"]
        timeframe = self.config["timeframe"]
        start_time = self.config["start_time"]
        end_time = self.config["end_time"]

        self.logger.info(f"Fetching {timeframe} price data for {exchange.upper()} {symbol.upper()} via DB COPY...")
        conn = get_connection()
        try:
            ohlcv_df = fetch_ohlcv(conn, exchange, symbol, timeframe, start_time, end_time)
        finally:
            conn.close()

        return ohlcv_df, signals_df

    def merge_data(self, ohlcv_df: pd.DataFrame, signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Left-joins the 1-minute price candles with the target signals.
        Signals only exist on timeframe boundaries (e.g. start of hour).
        Others are filled with 0.
        """
        if ohlcv_df.empty:
            return pd.DataFrame()
            
        if signals_df.empty or "signal" not in signals_df.columns:
            merged_df = ohlcv_df.copy()
            merged_df["signal"] = 0
            return merged_df

        # Ensure datetime indices with UTC
        if ohlcv_df.index.tz is None:
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index, utc=True)
        if isinstance(signals_df.index, pd.DatetimeIndex) and signals_df.index.tz is None:
            signals_df.index = pd.to_datetime(signals_df.index, utc=True)

        merged_df = ohlcv_df.join(signals_df[["signal"]], how="left")
        merged_df["signal"] = merged_df["signal"].fillna(0).astype(int)

        return merged_df

    def save_position(self, position: dict):
        """Saves/overwrites the active position in simulator_positions.csv."""
        df = pd.DataFrame([position])
        cols = ["trade_id", "direction", "entry_time", "entry_price", "quantity", "take_profit", "stop_loss", "current_price", "unrealized_pnl", "status"]
        df_cols = [c for c in cols if c in df.columns]
        df[df_cols].to_csv(self.positions_csv, index=False)

    def clear_position(self):
        """Clears the active position by writing header-only CSV."""
        cols = ["trade_id", "direction", "entry_time", "entry_price", "quantity", "take_profit", "stop_loss", "current_price", "unrealized_pnl", "status"]
        df = pd.DataFrame(columns=cols)
        df.to_csv(self.positions_csv, index=False)

    def append_to_ledger(self, trade: dict):
        """Appends a completed trade to simulator_ledger.csv."""
        df = pd.DataFrame([trade])
        # If file doesn't exist, write headers; otherwise append
        if not self.ledger_csv.exists():
            df.to_csv(self.ledger_csv, index=False)
        else:
            df.to_csv(self.ledger_csv, mode="a", header=False, index=False)
        self.logger.info(f"Trade ledger updated. Net PnL: {trade['net_pnl']:.2f}")

    def save_signals_input(self, merged_df: pd.DataFrame):
        """Saves the aligned OHLCV and signals data to simulator_input.csv."""
        if not merged_df.empty:
            merged_df.to_csv(self.input_csv)
            self.logger.info(f"Aligned signals and OHLCV data saved to: {self.input_csv}")

    def run_simulation(self):
        """
        Executes the sequential candle-by-candle simulation.
        Processes minute-by-minute checking SL/TP and opposite direction signals.
        """
        ohlcv_df, signals_df = self.fetch_data()
        if ohlcv_df.empty:
            self.logger.error("No price data loaded. Aborting simulation.")
            return
            
        merged_df = self.merge_data(ohlcv_df, signals_df)
        self.save_signals_input(merged_df)
        self.logger.info(f"Starting sequential simulation over {len(merged_df)} 1-minute bars...")

        
        # Reset output states
        self.clear_position()
        if self.ledger_csv.exists():
            try:
                os.remove(self.ledger_csv)
            except Exception as e:
                self.logger.warning(f"Could not remove old ledger CSV: {e}")
            
        active_position = None
        trade_id_counter = 0
        cumulative_pnl = 0.0
        
        commission_rate = self.config.get("commission", 0.0005)
        slippage_rate = self.config.get("slippage", 0.0002)
        allow_long = self.config.get("allow_long", True)
        allow_short = self.config.get("allow_short", True)
        
        # Iterate sequentially (one minute at a time)
        for timestamp, row in merged_df.iterrows():
            open_price = float(row["open"])
            high_price = float(row["high"])
            low_price = float(row["low"])
            close_price = float(row["close"])
            signal = int(row["signal"])
            
            # A. If position is open, check exits (TP/SL first, then Opposite Signal)
            if active_position is not None:
                direction = active_position["direction"]
                take_profit = active_position["take_profit"]
                stop_loss = active_position["stop_loss"]
                quantity = active_position["quantity"]
                entry_price = active_position["entry_price"]
                entry_time = active_position["entry_time"]
                entry_signal = active_position["signal"]
                
                exit_price = None
                exit_reason = None
                
                # Check TP/SL boundaries inside the 1m candle
                if direction == "Long":
                    if low_price <= stop_loss and high_price >= take_profit:
                        # Conservatively assume SL is hit first if both are hit
                        exit_price = stop_loss
                        exit_reason = "stop_loss_same_candle"
                    elif low_price <= stop_loss:
                        exit_price = stop_loss
                        exit_reason = "stop_loss"
                    elif high_price >= take_profit:
                        exit_price = take_profit
                        exit_reason = "take_profit"
                else:  # Short
                    if high_price >= stop_loss and low_price <= take_profit:
                        exit_price = stop_loss
                        exit_reason = "stop_loss_same_candle"
                    elif high_price >= stop_loss:
                        exit_price = stop_loss
                        exit_reason = "stop_loss"
                    elif low_price <= take_profit:
                        exit_price = take_profit
                        exit_reason = "take_profit"
                
                # Check Opposite Signal if TP/SL wasn't hit
                if exit_price is None and signal != 0:
                    if (direction == "Long" and signal == -1) or (direction == "Short" and signal == 1):
                        exit_price = open_price
                        exit_reason = "opposite_signal"
                
                # Handle trade closing
                if exit_price is not None:
                    entry_val = entry_price * quantity
                    exit_val = exit_price * quantity
                    fee = (entry_val * commission_rate) + (exit_val * commission_rate)
                    slippage = (entry_val * slippage_rate) + (exit_val * slippage_rate)
                    
                    if direction == "Long":
                        gross_pnl = (exit_price - entry_price) * quantity
                    else:
                        gross_pnl = (entry_price - exit_price) * quantity
                        
                    net_pnl = gross_pnl - fee - slippage
                    self.balance += net_pnl
                    cumulative_pnl += net_pnl
                    perc_pnl = (net_pnl / entry_val) * 100
                    
                    completed_trade = {
                        "entry_time": entry_time,
                        "direction": direction,
                        "signal": entry_signal,
                        "entry_price": entry_price,
                        "quantity": quantity,
                        "take_profit": take_profit,
                        "stop_loss": stop_loss,
                        "exit_price": exit_price,
                        "exit_time": timestamp,
                        "exit_reason": exit_reason,
                        "status": "Completed",
                        "net_pnl": net_pnl,
                        "perc_pnl": perc_pnl,
                        "cumulative_pnl": cumulative_pnl,
                        "balance": self.balance
                    }
                    self.append_to_ledger(completed_trade)
                    self.clear_position()
                    active_position = None
            
            # B. If no active position (or was just closed), check for new signal
            if active_position is None and signal != 0:
                if (signal == 1 and allow_long) or (signal == -1 and allow_short):
                    entry_price = open_price
                    position_size_val = self.config["position_size"]["value"]
                    pos_size_amount = self.balance * (position_size_val / 100)
                    quantity = pos_size_amount / entry_price
                    
                    tp_pct = self.config["take_profit"]["value"] / 100
                    sl_pct = self.config["stop_loss"]["value"] / 100
                    
                    if signal == 1:
                        take_profit = entry_price * (1 + tp_pct)
                        stop_loss = entry_price * (1 - sl_pct)
                        direction = "Long"
                    else:
                        take_profit = entry_price * (1 - tp_pct)
                        stop_loss = entry_price * (1 + sl_pct)
                        direction = "Short"
                    
                    trade_id_counter += 1
                    active_position = {
                        "trade_id": f"T_{trade_id_counter}",
                        "direction": direction,
                        "entry_time": timestamp,
                        "entry_price": entry_price,
                        "quantity": quantity,
                        "take_profit": take_profit,
                        "stop_loss": stop_loss,
                        "current_price": entry_price,
                        "unrealized_pnl": 0.0,
                        "status": "Open",
                        "signal": signal
                    }
                    self.save_position(active_position)
                    self.logger.info(f"[{timestamp}] Opened {direction} trade at {entry_price:.2f}")

            
            # C. Update current active position state at every minute close
            if active_position is not None:
                active_position["current_price"] = close_price
                if active_position["direction"] == "Long":
                    active_position["unrealized_pnl"] = (close_price - active_position["entry_price"]) * active_position["quantity"]
                else:
                    active_position["unrealized_pnl"] = (active_position["entry_price"] - close_price) * active_position["quantity"]
                
                # Keep active file updated
                self.save_position(active_position)
        
        self.logger.info("Simulation loop completed.")
        self.print_summary()

    def print_summary(self):
        """Prints overall simulation performance summary."""
        print("\n" + "=" * 45)
        print("          SIMULATOR RUN SUMMARY")
        print("=" * 45)
        print(f"Initial Balance:  ${self.initial_balance:.2f}")
        print(f"Final Balance:    ${self.balance:.2f}")
        print(f"Total PnL:        ${self.balance - self.initial_balance:.2f}")
        
        if self.ledger_csv.exists():
            ledger_df = pd.read_csv(self.ledger_csv)
            total_trades = len(ledger_df)
            winning_trades = (ledger_df["net_pnl"] > 0).sum()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            print(f"Total Trades:     {total_trades}")
            print(f"Win Rate:         {win_rate:.2f}%")
        else:
            print("Total Trades:     0")
        print("=" * 45)


