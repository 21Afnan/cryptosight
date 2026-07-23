
import json
import numpy as np
import pandas as pd

from cryptosight.utils.db import (
    get_connection,
    fetch_ohlcv,
    create_active_positions_table,
    upsert_active_position,
    delete_active_position,
    fetch_active_position,
    create_simulation_ledger_table,
    insert_simulation_ledger,
    upsert_simulation_stats,
)
from cryptosight.utils.metadata import (
    create_strategy_data,
    create_simulator_config,
    upsert_simulator_config,
    create_simulation_data,
    upsert_simulation_data,
)
from cryptosight.signals.main import run_signals_pipeline
from cryptosight.utils.logger import get_logger

logger = get_logger("SimulatorEngine")


class SimulatorEngine:
    """
    Event-driven sequential simulation engine.
    Processes historical market data candle-by-candle (1-to-1 time basis),
    maintains real-time active position state in PostgreSQL (`simulations.active_positions`),
    streams completed trade ledgers to `simulation_ledgers.<strategy_name>`,
    and records strategy configuration metadata in `metadata.simulation_data`.
    """

    def __init__(self, conn):
        self.logger = logger
        self.conn = conn
        self.exec_config = self.load_simulator_config()
        create_active_positions_table(self.conn)  # ensure table exists once at startup

    def load_simulator_config(self) -> dict:
        """
        Loads global simulator execution parameters from `metadata.simulator_config` (Row #1).
        """
        create_simulator_config(self.conn)
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT initial_balance, position_size_type, position_size_value, commission, slippage
                    FROM metadata.simulator_config
                    ORDER BY config_id ASC
                    LIMIT 1;
                """)
                row = cursor.fetchone()
                if row:
                    config = {
                        "initial_balance": float(row[0]),
                        "position_size_type": str(row[1]),
                        "position_size_value": float(row[2]),
                        "commission": float(row[3]),
                        "slippage": float(row[4]),
                    }
                    self.logger.info(f"Loaded execution config from DB: ${config['initial_balance']:,.2f} initial balance.")
                    return config
                else:
                    self.logger.error("No configuration row found in 'metadata.simulator_config'. Please populate the database config first.")
                    return {}
        except Exception as e:
            self.logger.error(f"Error fetching metadata.simulator_config from DB: {e}")
            return {}

    def fetch_strategies_from_db(self) -> list:
        """
        Queries all strategy definitions directly from PostgreSQL `metadata.strategy_data`.
        """
        create_strategy_data(self.conn)
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT strategy_id, strategy_name, exchange, symbol, target_timeframe,
                           indicators_config, strategy_config,
                           timeframe, start_time, end_time, max_retries, retry_delay
                    FROM metadata.strategy_data
                    ORDER BY strategy_id ASC;
                """)
                rows = cursor.fetchall()
                if rows:
                    strategies = []
                    for r in rows:
                        strat_cfg = r[6] if isinstance(r[6], dict) else (json.loads(r[6]) if isinstance(r[6], str) else {})
                        ind_cfg = r[5] if isinstance(r[5], dict) else (json.loads(r[5]) if isinstance(r[5], str) else {})
                        strategies.append({
                            "strategy_id": int(r[0]),
                            "strategy_name": str(r[1]),
                            "market": {
                                "exchange": str(r[2]),
                                "symbol": str(r[3]),
                                "target_timeframe": str(r[4]),
                                "timeframe": str(r[7]) if r[7] else "1m",
                                "start_time": r[8].isoformat() if r[8] else None,
                                "end_time": r[9].isoformat() if r[9] else None,
                                "max_retries": int(r[10]) if r[10] is not None else 5,
                                "retry_delay": int(r[11]) if r[11] is not None else 3,
                            },
                            "indicators": ind_cfg,
                            "strategy": strat_cfg,
                        })
                    self.logger.info(f"Fetched {len(strategies)} strategy definition(s) directly from 'metadata.strategy_data'.")
                    return strategies
        except Exception as e:
            self.logger.warning(f"Could not fetch strategies from metadata.strategy_data DB: {e}")

        return []

    def merge_data(self, ohlcv_df: pd.DataFrame, signals_df: pd.DataFrame) -> pd.DataFrame:
        """Merges OHLCV price candles and signals 1-to-1 on timestamp index."""
        if ohlcv_df.empty or signals_df.empty:
            return pd.DataFrame()

        # Align index types
        if not isinstance(ohlcv_df.index, pd.DatetimeIndex):
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)
        if not isinstance(signals_df.index, pd.DatetimeIndex):
            signals_df.index = pd.to_datetime(signals_df.index)

        if ohlcv_df.index.tz is not None:
            ohlcv_df.index = ohlcv_df.index.tz_localize(None)
        if signals_df.index.tz is not None:
            signals_df.index = signals_df.index.tz_localize(None)

        df = ohlcv_df.merge(signals_df, left_index=True, right_index=True, how="inner")
        return df

    def run_single_strategy_simulation(self, strat_dict: dict) -> pd.DataFrame:
        """
        Runs the candle-by-candle sequential event loop for a single strategy.
        Tracks active position state in PostgreSQL `simulations.active_positions` (0 duplicacy).
        Saves completed trade ledgers into `simulation_ledgers.<clean_strategy_name>`.
        Upserts configuration settings into `metadata.simulation_data`.
        """
        strategy_id = strat_dict["strategy_id"]
        strategy_name = strat_dict["strategy_name"]
        market_cfg = strat_dict["market"]
        exchange = market_cfg["exchange"]
        symbol = market_cfg["symbol"]
        target_tf = market_cfg["target_timeframe"]
        base_tf = market_cfg.get("timeframe")
        timeframe = base_tf if base_tf else target_tf
        start_time = market_cfg.get("start_time")
        end_time = market_cfg.get("end_time")

        strategy_cfg = strat_dict["strategy"]

        self.logger.info(f"=== Simulating Strategy #{strategy_id}: '{strategy_name}' [{exchange.upper()} {symbol.upper()} {target_tf}] ===")

        # 1. Fetch OHLCV price candles
        ohlcv_df = fetch_ohlcv(self.conn, exchange, symbol, timeframe, start_time, end_time)
        if ohlcv_df.empty:
            self.logger.info(f"No local OHLCV candles found in DB for '{strategy_name}'. Attempting auto-download...")
            try:
                from cryptosight.data.downloader import Downloader
                dl = Downloader(exchange=exchange, symbol=symbol, timeframe=timeframe)
                dl.download(
                    start_time=start_time,
                    end_time=end_time,
                    max_retries=5,
                    retry_delay=3,
                    fill_method="ffill",
                )
                ohlcv_df = fetch_ohlcv(self.conn, exchange, symbol, timeframe, start_time, end_time)
            except Exception as dl_err:
                self.logger.error(f"Auto-download failed for '{strategy_name}': {dl_err}")

        if ohlcv_df.empty:
            self.logger.warning(f"No OHLCV candles available for strategy '{strategy_name}'. Skipping simulation.")
            return pd.DataFrame()

        # 2. Run signals pipeline for this strategy (read-only — no DB writes during simulation)
        full_df = run_signals_pipeline(strat_dict=strat_dict, save_to_db=False)
        if full_df.empty or "signal" not in full_df.columns:
            self.logger.warning(f"No signals generated for strategy '{strategy_name}'. Skipping simulation.")
            return pd.DataFrame()

        signals_df = full_df[["signal"]]

        # 3. Merge candles and signals 1-to-1 on timestamp
        merged_df = self.merge_data(ohlcv_df, signals_df)
        if merged_df.empty:
            self.logger.warning(f"No merged candles for strategy '{strategy_name}'. Skipping simulation.")
            return pd.DataFrame()

        # 4. Extract Take Profit and Stop Loss percentages directly from strategy config
        tp_pct = float(strategy_cfg["take_profit"]) / 100.0
        sl_pct = float(strategy_cfg["stop_loss"]) / 100.0

        # 5. Initialize simulation execution state & resume any active open position from DB
        balance = float(self.exec_config["initial_balance"])
        pos_size_value = float(self.exec_config["position_size_value"])
        comm_rate = float(self.exec_config["commission"])
        slip_rate = float(self.exec_config["slippage"])

        current_position = fetch_active_position(self.conn, strategy_id)
        trade_counter = 0
        completed_trades = []

        # 6. Sequential Event Loop (Candle-by-Candle Iteration)
        for ts, candle in merged_df.iterrows():
            sig = int(candle["signal"])
            high_price = float(candle["high"])
            low_price = float(candle["low"])
            close_price = float(candle["close"])

            # -------------------------------------------------------------
            # CASE A: NO POSITION IS OPEN -> Check for Trade Entry Signal
            # -------------------------------------------------------------
            if current_position is None:
                if sig in (1, -1):
                    trade_counter += 1
                    t_id = f"SIM_{strategy_id}_{trade_counter}"
                    direction = "LONG" if sig == 1 else "SHORT"
                    entry_price = close_price
                    allocated_equity = balance * (pos_size_value / 100.0)
                    quantity = allocated_equity / entry_price

                    if sig == 1:
                        take_profit = entry_price * (1.0 + tp_pct)
                        stop_loss = entry_price * (1.0 - sl_pct)
                    else:
                        take_profit = entry_price * (1.0 - tp_pct)
                        stop_loss = entry_price * (1.0 + sl_pct)

                    unrealized_pnl = 0.0
                    current_position = {
                        "trade_id": t_id,
                        "direction": direction,
                        "entry_time": ts,
                        "entry_price": entry_price,
                        "quantity": quantity,
                        "take_profit": take_profit,
                        "stop_loss": stop_loss,
                        "current_price": close_price,
                        "unrealized_pnl": unrealized_pnl,
                        "status": "OPEN",
                    }

                    # Upsert open trade into simulations.active_positions (PRIMARY KEY strategy_id)
                    upsert_active_position(
                        conn=self.conn,
                        strategy_id=strategy_id,
                        strategy_name=strategy_name,
                        exchange=exchange,
                        symbol=symbol,
                        timeframe=target_tf,
                        trade_id=t_id,
                        direction=direction,
                        entry_time=ts,
                        entry_price=entry_price,
                        quantity=quantity,
                        take_profit=take_profit,
                        stop_loss=stop_loss,
                        current_price=close_price,
                        unrealized_pnl=unrealized_pnl,
                        status="OPEN",
                    )
            # -------------------------------------------------------------
            # CASE B: POSITION IS ALREADY OPEN -> Monitor & Check Exits
            # -------------------------------------------------------------
            else:
                entry_price = current_position["entry_price"]
                quantity = current_position["quantity"]
                direction = current_position["direction"]
                take_profit = current_position["take_profit"]
                stop_loss = current_position["stop_loss"]

                # Update current price & unrealized PnL
                if direction == "LONG":
                    unrealized_pnl = (close_price - entry_price) * quantity
                else:
                    unrealized_pnl = (entry_price - close_price) * quantity

                current_position["current_price"] = close_price
                current_position["unrealized_pnl"] = unrealized_pnl

                # Update state in simulations.active_positions
                upsert_active_position(
                    conn=self.conn,
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=target_tf,
                    trade_id=current_position["trade_id"],
                    direction=direction,
                    entry_time=current_position["entry_time"],
                    entry_price=entry_price,
                    quantity=quantity,
                    take_profit=take_profit,
                    stop_loss=stop_loss,
                    current_price=close_price,
                    unrealized_pnl=unrealized_pnl,
                    status=current_position["status"],
                )

                # Evaluate exit conditions
                exit_triggered = False
                exit_price = close_price
                exit_reason = ""

                if direction == "LONG":
                    if high_price >= take_profit:
                        exit_triggered = True
                        exit_price = take_profit
                        exit_reason = "TAKE_PROFIT"
                    elif low_price <= stop_loss:
                        exit_triggered = True
                        exit_price = stop_loss
                        exit_reason = "STOP_LOSS"
                    elif sig == -1:
                        exit_triggered = True
                        exit_price = close_price
                        exit_reason = "OPPOSITE_SIGNAL"
                else:  # SHORT position
                    if low_price <= take_profit:
                        exit_triggered = True
                        exit_price = take_profit
                        exit_reason = "TAKE_PROFIT"
                    elif high_price >= stop_loss:
                        exit_triggered = True
                        exit_price = stop_loss
                        exit_reason = "STOP_LOSS"
                    elif sig == 1:
                        exit_triggered = True
                        exit_price = close_price
                        exit_reason = "OPPOSITE_SIGNAL"

                # ---------------------------------------------------------
                # TRADE EXIT EXECUTION
                # ---------------------------------------------------------
                if exit_triggered:
                    if direction == "LONG":
                        gross_pnl = (exit_price - entry_price) * quantity
                    else:
                        gross_pnl = (entry_price - exit_price) * quantity

                    turnover = (entry_price + exit_price) * quantity
                    commission_fee = turnover * comm_rate
                    slippage_fee = turnover * slip_rate
                    net_pnl = gross_pnl - commission_fee - slippage_fee
                    perc_pnl = net_pnl / (entry_price * quantity)

                    balance += net_pnl

                    completed_trades.append({
                        "trade_id": current_position["trade_id"],
                        "direction": direction,
                        "entry_time": current_position["entry_time"],
                        "exit_time": ts,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "quantity": quantity,
                        "gross_pnl": gross_pnl,
                        "commission": commission_fee,
                        "slippage": slippage_fee,
                        "net_pnl": net_pnl,
                        "perc_pnl": perc_pnl,
                        "exit_reason": exit_reason,
                        "final_balance": balance,
                    })

                    # Remove active trade from simulations.active_positions
                    delete_active_position(self.conn, strategy_id)
                    current_position = None

        # 7. Save trade ledger to simulation_ledgers.<strategy_name>
        ledger_df = pd.DataFrame(completed_trades)
        if not ledger_df.empty:
            insert_simulation_ledger(
                conn=self.conn,
                exchange=exchange,
                symbol=symbol,
                timeframe=target_tf,
                ledger_df=ledger_df,
                strategy_name=strategy_name,
            )

        # 8. Save per-strategy simulation config settings to metadata.simulation_data
        upsert_simulation_data(
            conn=self.conn,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            exchange=exchange,
            symbol=symbol,
            timeframe=target_tf,
            initial_balance=float(self.exec_config["initial_balance"]),
            position_size_type=str(self.exec_config["position_size_type"]),
            position_size_value=float(self.exec_config["position_size_value"]),
            commission=float(self.exec_config["commission"]),
            slippage=float(self.exec_config["slippage"]),
        )

        # 9. Save per-strategy performance stats & dynamic tabular metrics to simulations.stats
        upsert_simulation_stats(
            conn=self.conn,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            exchange=exchange,
            symbol=symbol,
            timeframe=target_tf,
            initial_balance=float(self.exec_config["initial_balance"]),
            ledger_df=ledger_df,
        )

        self.logger.info(f"Simulation completed for strategy '{strategy_name}': {len(completed_trades)} trade(s) executed. Final Balance: ${balance:,.2f}.")
        return ledger_df

    def run_all_simulations(self) -> dict:
        """
        Executes sequential simulation for all strategies fetched directly from PostgreSQL metadata.strategy_data.
        """
        strategies = self.fetch_strategies_from_db()
        if not strategies:
            self.logger.warning("No strategies found in PostgreSQL metadata.strategy_data.")
            return {}

        self.logger.info(f"Starting simulation pipeline for {len(strategies)} strategy definition(s)...")
        results = {}
        for idx, strat in enumerate(strategies, start=1):
            s_name = strat["strategy_name"]
            self.logger.info(f"[{idx}/{len(strategies)}] Running simulation for: '{s_name}'...")
            try:
                ledger_df = self.run_single_strategy_simulation(strat)
                results[s_name] = ledger_df
            except Exception as e:
                self.logger.error(f"Failed simulation for strategy '{s_name}': {e}")
                results[s_name] = pd.DataFrame()

        return results
