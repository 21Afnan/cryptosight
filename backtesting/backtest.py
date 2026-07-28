import yaml
from pathlib import Path
import pandas as pd
import numpy as np
from cryptosight.utils.db import (
    get_connection, fetch_ohlcv,
    create_backtest_schema_and_table, insert_backtest_ledger,
    create_signals_schema_and_table, insert_signals,
)
from cryptosight.utils.metadata import upsert_strategy_data
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

    def run_single_strategy(self, strat_dict: dict, run_id: int = None) -> pd.DataFrame:
        """
        Runs the backtest pipeline for a single strategy definition dictionary.
        Preserves strategy_name, market parameters, indicators, and TP/SL.
        run_id: when provided, ledger is stored in backtests.<slug>_run_<run_id>
        so each request keeps its own isolated trade history.
        """
        import re
        market_cfg = strat_dict.get("market") or {}
        exchange = market_cfg.get("exchange")
        symbol = market_cfg.get("symbol")
        base_tf = market_cfg.get("timeframe")
        target_tf = market_cfg.get("target_timeframe")
        start_time = market_cfg.get("start_time")
        end_time = market_cfg.get("end_time")

        strategy_name = strat_dict.get("strategy_name")
        strategy_cfg = strat_dict.get("strategy") or {}
        indicator_cfg = strat_dict.get("indicators") or {}

        self.logger.info(f"=== Backtesting Strategy: '{strategy_name}' [{str(exchange).upper()} {str(symbol).upper()} {target_tf}] ===")

        # 1. Fetch OHLCV price candles
        conn = get_connection()
        try:
            ohlcv_df = fetch_ohlcv(conn, exchange, symbol, base_tf, start_time, end_time)
        finally:
            conn.close()

        if ohlcv_df.empty:
            self.logger.warning(f"No OHLCV candles found for strategy '{strategy_name}'. Skipping.")
            return pd.DataFrame()

        # 2. Run signals pipeline for this strategy dictionary
        full_df = run_signals_pipeline(strat_dict=strat_dict)
        if full_df.empty or "signal" not in full_df.columns:
            self.logger.warning(f"No signals generated for strategy '{strategy_name}'. Skipping.")
            return pd.DataFrame()

        # ALWAYS Register Strategy Metadata into metadata.strategy_data
        strat_id_num = None
        try:
            conn = get_connection()
            try:
                create_signals_schema_and_table(conn, exchange, symbol, target_tf)
                insert_signals(conn, exchange, symbol, target_tf, full_df)
            except Exception as sig_err:
                self.logger.warning(f"Could not insert raw signals into DB for '{strategy_name}': {sig_err}")

            strat_id_num = upsert_strategy_data(
                conn=conn,
                exchange=exchange,
                symbol=symbol,
                target_timeframe=target_tf,
                indicators_config=indicator_cfg,
                strategy_config=strategy_cfg,
                strategy_name=strategy_name,
            )
            conn.close()
        except Exception as e:
            self.logger.warning(f"Could not save strategy metadata to DB for '{strategy_name}': {e}")

        signals_df = full_df[["signal"]]

        # 3. Merge candles with signals
        merged_df = self.merge_data(ohlcv_df, signals_df)

        # 4. Locate trade entries and execution prices
        entries_df = self.determine_entries(merged_df)
        if entries_df.empty:
            self.logger.info(f"No trade entry triggers for strategy '{strategy_name}'.")
            if strat_id_num:
                try:
                    conn = get_connection()
                    from cryptosight.utils.metadata import upsert_backtest_data
                    upsert_backtest_data(
                        conn=conn,
                        strategy_id=strat_id_num,
                        backtest_config=self.config,
                        ledger_df=pd.DataFrame(),
                    )
                    conn.close()
                except Exception as meta_err:
                    self.logger.warning(f"Could not save empty backtest metadata for '{strategy_name}': {meta_err}")
            return pd.DataFrame()

        # 5. Position sizing
        entries_df = self.calculate_position_size(entries_df)

        # 6. Calculate TP/SL target levels directly from strategy configuration with safe fallbacks
        tp_val = strategy_cfg.get("take_profit") if isinstance(strategy_cfg, dict) else None
        sl_val = strategy_cfg.get("stop_loss") if isinstance(strategy_cfg, dict) else None

        if tp_val is None:
            tp_cfg = self.config.get("take_profit")
            tp_val = tp_cfg.get("value", 1.0) if isinstance(tp_cfg, dict) else 1.0
        if sl_val is None:
            sl_cfg = self.config.get("stop_loss")
            sl_val = sl_cfg.get("value", 0.5) if isinstance(sl_cfg, dict) else 0.5

        tp_pct = float(tp_val) / 100.0 if float(tp_val) > 0.05 else float(tp_val)
        sl_pct = float(sl_val) / 100.0 if float(sl_val) > 0.05 else float(sl_val)

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

        # 7. Locate trade exits
        entries_df = self.determine_exits(merged_df, entries_df)

        # 8. Apply fee frictions & calculate net PnL
        entries_df = self.calculate_fees_and_pnl(entries_df)

        # 9. Account balance updates
        ledger_df = self.update_balance(entries_df)

        # 10. Columns formatting
        cols_to_drop = ["commission", "slippage", "gross_pnl"]
        ledger_df.drop(columns=[c for c in cols_to_drop if c in ledger_df.columns], inplace=True)
        desired_order = ["direction", "signal", "entry_price", "quantity", "take_profit", "stop_loss", "exit_price", "exit_time", "exit_reason", "status", "net_pnl", "perc_pnl", "cumulative_pnl", "balance"]
        ordered_cols = [c for c in desired_order if c in ledger_df.columns] + [c for c in ledger_df.columns if c not in desired_order]
        ledger_df = ledger_df[ordered_cols]

        # 11. Save backtest ledger & backtest metadata
        try:
            conn = get_connection()
            clean_table = re.sub(r'[^a-zA-Z0-9_]', '_', str(strategy_name)).lower()
            clean_table = re.sub(r'_+', '_', clean_table).strip('_')

            create_backtest_schema_and_table(
                conn,
                exchange=exchange,
                symbol=symbol,
                timeframe=base_tf,
                strategy_id=clean_table,
                run_id=run_id,
            )
            insert_backtest_ledger(
                conn,
                exchange=exchange,
                symbol=symbol,
                timeframe=base_tf,
                ledger_df=ledger_df,
                strategy_id=clean_table,
                run_id=run_id,
            )

            if strat_id_num:
                from cryptosight.utils.metadata import upsert_backtest_data
                upsert_backtest_data(
                    conn=conn,
                    strategy_id=strat_id_num,
                    backtest_config=self.config,
                    ledger_df=ledger_df,
                )

                # ── Compute stats + charts → store in backtests.stats ──────────
                try:
                    from cryptosight.stats.metrices import compute_all_metrics
                    from cryptosight.stats.plots import generate_all_plots
                    from cryptosight.utils.db import upsert_backtest_stats, create_backtest_stats_table

                    # Mark as running before computation
                    create_backtest_stats_table(conn)
                    upsert_backtest_stats(conn, strategy_id=strat_id_num, status="running")

                    # compute_all_metrics expects a returns series (perc_pnl column)
                    returns_series = ledger_df["perc_pnl"].dropna()

                    metrics_dict = {}
                    charts_dict  = {}

                    if not returns_series.empty:
                        metrics_dict = compute_all_metrics(returns_series, is_percentage=True)
                        # Enrich metrics with key trade stats not in QuantStats
                        total = len(ledger_df)
                        wins  = int((ledger_df["net_pnl"] > 0).sum())
                        metrics_dict["total_trades"]  = total
                        metrics_dict["win_rate"]       = round(wins / total, 4) if total else 0.0
                        metrics_dict["net_pnl"]        = float(ledger_df["net_pnl"].sum())
                        metrics_dict["final_balance"]  = float(ledger_df["balance"].iloc[-1]) if not ledger_df.empty else 0.0

                    try:
                        _, charts_dict = generate_all_plots(returns_series, is_percentage=True)
                    except Exception as chart_err:
                        self.logger.warning(f"Charts generation skipped for '{strategy_name}': {chart_err}")

                    upsert_backtest_stats(
                        conn,
                        strategy_id=strat_id_num,
                        status="completed",
                        metrics=metrics_dict,
                        charts=charts_dict,
                    )
                    
                    self.logger.info(f"backtests.stats populated for strategy_id={strat_id_num} ('{strategy_name}')")

                except Exception as stats_err:
                    self.logger.warning(f"Could not compute/store stats for '{strategy_name}': {stats_err}")
                    try:
                        upsert_backtest_stats(conn, strategy_id=strat_id_num, status="failed")
                    except Exception:
                        pass

            conn.close()
            self.logger.info(f"Backtest completed & saved to DB for strategy '{strategy_name}' (ID #{strat_id_num}).")
        except Exception as e:
            self.logger.warning(f"Could not save backtest ledger to DB for '{strategy_name}': {e}")

        return ledger_df

    def run_all_strategies(self, strategy_config_path: str = None) -> dict:
        """
        Loops through ALL strategies in strategy_config.yaml, executing a vectorized backtest for each.
        Returns a dictionary mapping strategy_name -> ledger_df.
        """
        import os
        if strategy_config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            strategy_config_path = os.path.join(current_dir, "..", "signals", "strategy_config.yaml")

        if not os.path.exists(strategy_config_path):
            self.logger.error(f"Strategy configuration file not found at: {strategy_config_path}")
            return {}

        with open(strategy_config_path, "r", encoding="utf-8") as f:
            strat_file = yaml.safe_load(f) or {}

        strat_list = strat_file.get("strategies", [])
        if not strat_list or not isinstance(strat_list, list):
            self.logger.info("No 'strategies' list found in config. Running single strategy pipeline...")
            ledger = self.run_pipeline()
            s_name = strat_file.get("strategy_name", "Default Strategy")
            return {s_name: ledger}

        self.logger.info(f"Discovered {len(strat_list)} strategy definition(s). Starting multi-strategy backtest...")
        all_results = {}
        for idx, s in enumerate(strat_list, start=1):
            s_name = s.get("strategy_name", f"Strategy_{idx}")
            self.logger.info(f"[{idx}/{len(strat_list)}] Backtesting Strategy: '{s_name}'...")
            try:
                ledger = self.run_single_strategy(s)
                all_results[s_name] = ledger
            except Exception as e:
                self.logger.error(f"Failed backtest for strategy '{s_name}': {e}")

        return all_results

    def run_signals(self, strategy_config_path: str = None) -> pd.DataFrame:
        """
        Executes the AI Quant signals pipeline for standalone backward compatibility.
        """
        full_df = run_signals_pipeline(config_path=strategy_config_path)
        if full_df.empty or "signal" not in full_df.columns:
            return pd.DataFrame(columns=["signal"])
        return full_df[["signal"]]

    def merge_data(self, ohlcv_df: pd.DataFrame, signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merges 1-minute OHLCV data with the signal DataFrame.
        Fills missing signal values with 0 (No Signal/Hold).
        """
        # If no signals generated or signals_df is empty, fill all OHLCV bars with 0 (Hold)
        if signals_df.empty or "signal" not in signals_df.columns:
            merged_df = ohlcv_df.copy()
            merged_df["signal"] = 0
            return merged_df

        # Ensure indices are datetime with UTC timezone
        if ohlcv_df.index.tz is None:
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index, utc=True)
        if isinstance(signals_df.index, pd.DatetimeIndex) and signals_df.index.tz is None:
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

        if entry_method == "next_open" or entry_method == "open":
            # Since signals from signals/main.py are ALREADY shifted by 1 bar (condition on T -> signal on T+1),
            # this row is ALREADY the execution bar (T+1). We take this row's open price directly!
            entry_price_series = merged_df["open"]
        elif entry_method == "current_close" or entry_method == "close":
            entry_price_series = merged_df["close"]
        else:
            raise ValueError(f"Unsupported entry_price method: '{entry_method}' in config.")

        entries_df = merged_df[merged_df["signal"] != 0].copy()
        entries_df["direction"] = np.where(entries_df["signal"] == 1, "Long", "Short")
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
        statuses = []
        valid_indices = []
        last_exit_time = None
        max_open = self.config.get("max_open_positions", 1)

        for entry_time, row in entries_df.iterrows():
            if max_open == 1 and last_exit_time is not None:
                if entry_time <= last_exit_time:
                    self.logger.debug(f"Skipping signal at {entry_time} — previous trade open until {last_exit_time}")
                    continue

            entry_price = row["entry_price"]
            tp_price = row["take_profit"]
            sl_price = row["stop_loss"]
            direction = int(row["signal"])  # 1 for Long, -1 for Short

            # Since signals are already shifted by 1 bar in main.py, entry_time IS the execution bar!
            # We start checking for TP/SL from this exact entry candle itself (no +1 delay).
            start_idx = time_to_idx[entry_time]
            if start_idx >= len(ohlcv_times):
                # No data after entry, exit immediately at entry_price
                exit_prices.append(entry_price)
                exit_times.append(entry_time)
                exit_reasons.append("end_of_data")
                statuses.append("Ongoing")
                valid_indices.append(entry_time)
                last_exit_time = entry_time
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
                status = "Ongoing"
            elif tp_first_idx < sl_first_idx:
                exit_offset = tp_first_idx
                exit_price = tp_price
                exit_reason = "take_profit"
                status = "Completed"
            elif sl_first_idx < tp_first_idx:
                exit_offset = sl_first_idx
                exit_price = sl_price
                exit_reason = "stop_loss"
                status = "Completed"
            else:
                # Both hit in the same candle -> assume SL hit for conservatism
                exit_offset = tp_first_idx
                exit_price = sl_price
                exit_reason = "stop_loss_same_candle"
                status = "Completed"

            exit_idx = start_idx + exit_offset
            calc_exit_time = ohlcv_times[exit_idx]
            
            exit_prices.append(exit_price)
            exit_times.append(calc_exit_time)
            exit_reasons.append(exit_reason)
            statuses.append(status)
            valid_indices.append(entry_time)
            last_exit_time = calc_exit_time

        # Assign calculated exits only to non-overlapping trades
        entries_df = entries_df.loc[valid_indices].copy()
        entries_df["exit_price"] = exit_prices
        entries_df["exit_time"] = exit_times
        entries_df["exit_reason"] = exit_reasons
        entries_df["status"] = statuses

        self.logger.info(f"Exits determined for {len(entries_df)} non-overlapping trades.")
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
        entries_df["cumulative_pnl"] = entries_df["net_pnl"].cumsum()
        entries_df["balance"] = initial_balance + entries_df["cumulative_pnl"]
        
        return entries_df

    def run_pipeline(self, external_signals_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Runs the complete backtesting pipeline step-by-step:
        1. Fetch raw candles (fetch_data)
        2. Fetch generated signals (run_signals or external_signals_df)
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
        if external_signals_df is not None:
            self.logger.info("Using external ML signals for backtesting...")
            signals_df = external_signals_df
        else:
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

        # Step 10: Clean up columns
        # Remove commission, slippage, and gross_pnl from final ledger output (keep net_pnl)
        cols_to_drop = ["commission", "slippage", "gross_pnl"]
        ledger_df.drop(columns=[c for c in cols_to_drop if c in ledger_df.columns], inplace=True)

        desired_order = ["direction", "signal", "entry_price", "quantity", "take_profit", "stop_loss", "exit_price", "exit_time", "exit_reason", "status", "net_pnl", "perc_pnl", "cumulative_pnl", "balance"]
        ordered_cols = [c for c in desired_order if c in ledger_df.columns] + [c for c in ledger_df.columns if c not in desired_order]
        ledger_df = ledger_df[ordered_cols]

        strat_id = getattr(self, "strategy_id", f"{self.config['exchange'].lower()}_{self.config['symbol'].lower()}_{self.config['timeframe'].lower()}")

        # Step 11: Save ledger to PostgreSQL (backtests.{strategy_id})
        try:
            conn = get_connection()
            create_backtest_schema_and_table(
                conn,
                exchange=self.config["exchange"],
                symbol=self.config["symbol"],
                timeframe=self.config["timeframe"],
                strategy_id=strat_id,
            )
            insert_backtest_ledger(
                conn,
                exchange=self.config["exchange"],
                symbol=self.config["symbol"],
                timeframe=self.config["timeframe"],
                ledger_df=ledger_df,
                strategy_id=strat_id,
            )
            
            # Save high-level backtest config & summary results to metadata.backtest_data
            try:
                db_id = getattr(self, "strategy_db_id", None)
                if db_id is not None:
                    from cryptosight.utils.metadata import upsert_backtest_data
                    upsert_backtest_data(
                        conn=conn,
                        strategy_id=db_id,
                        backtest_config=self.config,
                        ledger_df=ledger_df,
                    )
                else:
                    self.logger.warning("Skipping metadata.backtest_data upsert — strategy_db_id is None.")
            except Exception as meta_err:
                self.logger.warning(f"Could not save backtest metadata (non-fatal): {meta_err}")

            conn.close()
            self.logger.info(f"Backtest ledger saved to DB table 'backtests.{strat_id}'.")
        except Exception as e:
            self.logger.warning(f"Could not save backtest ledger to DB (non-fatal): {e}")

        # Step 12: Save physical CSV and return DataFrame cleanly
        csv_path = Path(__file__).resolve().parent / "backtest_ledger.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_df.to_csv(csv_path)
        return ledger_df


if __name__ == "__main__":
    print("=" * 65)
    print("        RUNNING MULTI-STRATEGY BACKTEST ENGINE PIPELINE")
    print("=" * 65)

    engine = BacktestingEngine()
    results = engine.run_all_strategies()

    print("\n" + "=" * 65)
    print("                 MULTI-STRATEGY BACKTEST SUMMARY")
    print("=" * 65)
    print(f"Total Strategies Tested: {len(results)}")
    print(f"Initial Account Balance: ${engine.config.get('initial_balance', 10000.0):,.2f}\n")

    for s_name, ledger in results.items():
        if ledger is not None and not ledger.empty:
            final_bal = ledger["balance"].iloc[-1]
            net_pnl = final_bal - engine.config.get("initial_balance", 10000.0)
            win_count = (ledger["net_pnl"] > 0).sum()
            win_rate = (win_count / len(ledger) * 100.0) if len(ledger) > 0 else 0.0
            print(f" • Strategy: '{s_name}'")
            print(f"   - Trades Executed: {len(ledger)}")
            print(f"   - Win Rate:        {win_rate:.2f}%")
            print(f"   - Net PnL:         ${net_pnl:+,.2f}")
            print(f"   - Final Balance:   ${final_bal:,.2f}")
            print("-" * 55)
        else:
            print(f" • Strategy: '{s_name}' -> 0 trades executed or insufficient market data.")
            print("-" * 55)
    print("=" * 65)

    




