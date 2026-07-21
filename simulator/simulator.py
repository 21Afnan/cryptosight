import os
import json
import yaml
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import (
    get_connection,
    create_simulations_schema_and_tables,
    save_simulation_position,
    close_simulation_position,
    insert_simulation_ledger,
    upsert_simulation_stats
)
from cryptosight.utils.metadata import (
    create_strategy_data,
    create_simulator_config,
    fetch_simulator_config,
    upsert_simulator_config,
    generate_strategy_id
)
from cryptosight.signals.main import run_signals_pipeline
from cryptosight.data.downloader import Downloader
from cryptosight.stats.metrices import compute_all_metrics

logger = get_logger("SimulatorEngine")


class SimulatorEngine:
    """
    Class-based Quantitative Simulation Engine.
    Encapsulates strategy discovery, database configuration loading, 1m candle-signal alignment,
    sequential execution, live position state management, trade ledger logging, and stats reporting.
    """

    def __init__(self, conn=None):
        self.conn = conn or get_connection()
        create_strategy_data(self.conn)
        create_simulator_config(self.conn)
        try:
            with self.conn.cursor() as cur:
                cur.execute("UPDATE metadata.simulator_config SET enabled = TRUE WHERE enabled IS NULL OR enabled = FALSE;")
                # Persist start_time and end_time into strategy_config JSON in metadata.strategy_data
                cur.execute("""
                    UPDATE metadata.strategy_data
                    SET strategy_config = strategy_config || '{"start_time": "2026-07-19 00:00:00", "end_time": "now"}'::jsonb
                    WHERE NOT (strategy_config ? 'start_time');
                """)
                self.conn.commit()
        except Exception as e:
            logger.warning(f"Could not bulk-update strategy_data metadata in DB: {e}")

    def fetch_strategies(self) -> list:
        """Discovers all strategies and their simulator configs in a single SQL JOIN query."""
        strategies = []
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        s.strategy_id, s.exchange, s.symbol, s.target_timeframe, s.strategy_config, s.indicators_config,
                        c.enabled, c.initial_balance, c.position_size_type, c.position_size_value,
                        c.commission, c.slippage, c.allow_long, c.allow_short
                    FROM metadata.strategy_data s
                    LEFT JOIN metadata.simulator_config c ON s.strategy_id = c.strategy_id;
                """)
                rows = cur.fetchall()
                for r in rows:
                    (s_id, ex, sym, tf, strat_cfg, ind_cfg,
                     enabled, init_bal, pos_type, pos_val, comm, slip, allow_l, allow_s) = r

                    if isinstance(strat_cfg, str):
                        strat_cfg = json.loads(strat_cfg)
                    if isinstance(ind_cfg, str):
                        ind_cfg = json.loads(ind_cfg)

                    is_enabled = enabled if enabled is not None else True
                    
                    sim_config = {
                        "strategy_id": s_id,
                        "enabled": is_enabled,
                        "initial_balance": float(init_bal) if init_bal is not None else 10000.0,
                        "position_size": {
                            "type": pos_type if pos_type else "fixed_percentage",
                            "value": float(pos_val) if pos_val is not None else 10.0
                        },
                        "commission": float(comm) if comm is not None else 0.0005,
                        "slippage": float(slip) if slip is not None else 0.0002,
                        "allow_long": allow_l if allow_l is not None else True,
                        "allow_short": allow_s if allow_s is not None else True
                    }

                    # Automatically persist enabled = True in metadata.simulator_config if not previously recorded
                    if enabled is None:
                        upsert_simulator_config(self.conn, s_id, sim_config)

                    strategies.append({
                        "strategy_id": s_id,
                        "exchange": ex,
                        "symbol": sym,
                        "target_timeframe": tf,
                        "strategy_config": strat_cfg or {},
                        "indicators_config": ind_cfg or {},
                        "sim_config": sim_config
                    })
        except Exception as error:
            logger.error(f"Error fetching strategy definitions from metadata: {error}")
            return []

        if not strategies:
            logger.error("No strategy records found in database.")
            
        return strategies

    def calculate_position_size(self, balance: float, pos_type: str, pos_value: float, entry_price: float) -> float:
        """Calculates trade quantity based on balance and sizing mode."""
        if entry_price <= 0 or balance <= 0:
            return 0.0
        if pos_type == "fixed_percentage":
            allocated = balance * (pos_value / 100.0)
        else:
            allocated = min(pos_value, balance)
        return max(0.0, allocated / entry_price)

    def check_entry_signal(self, signal: int, allow_long: bool, allow_short: bool) -> str:
        """Evaluates raw signal integer against directional execution rules."""
        if signal == 1 and allow_long:
            return "LONG"
        elif signal == -1 and allow_short:
            return "SHORT"
        return None

    def evaluate_exit_conditions(self, position: dict, close_p: float, high_p: float, low_p: float, signal: int) -> tuple:
        """Evaluates Take Profit, Stop Loss, and Opposite Signal rules for active position."""
        direction = position["direction"]
        tp_price = position["take_profit"]
        sl_price = position["stop_loss"]

        if direction == "LONG":
            if high_p >= tp_price:
                return True, tp_price, "Take Profit"
            if low_p <= sl_price:
                return True, sl_price, "Stop Loss"
            if signal == -1:
                return True, close_p, "Opposite Signal"
        elif direction == "SHORT":
            if low_p <= tp_price:
                return True, tp_price, "Take Profit"
            if high_p >= sl_price:
                return True, sl_price, "Stop Loss"
            if signal == 1:
                return True, close_p, "Opposite Signal"

        return False, close_p, None

    def execute_entry(
        self,
        balance: float,
        direction: str,
        close_p: float,
        timestamp,
        pos_type: str,
        pos_value: float,
        tp_pct: float,
        sl_pct: float,
        slippage: float,
        commission: float
    ) -> tuple:
        """Executes order entry applying slippage and entry fees."""
        if direction == "LONG":
            entry_price = close_p * (1.0 + slippage)
            entry_slippage = close_p * slippage
            tp_price = close_p * (1.0 + tp_pct)
            sl_price = close_p * (1.0 - sl_pct)
        else:
            entry_price = close_p * (1.0 - slippage)
            entry_slippage = close_p * slippage
            tp_price = close_p * (1.0 - tp_pct)
            sl_price = close_p * (1.0 + sl_pct)

        quantity = self.calculate_position_size(balance, pos_type, pos_value, entry_price)
        if quantity <= 0:
            return None, balance

        entry_val = entry_price * quantity
        entry_comm = entry_val * commission
        new_balance = balance - entry_comm

        position = {
            "direction": direction,
            "entry_time": timestamp,
            "entry_price": entry_price,
            "quantity": quantity,
            "take_profit": tp_price,
            "stop_loss": sl_price,
            "current_price": close_p,
            "unrealized_pnl": 0.0,
            "status": "Open",
            "entry_comm": entry_comm,
            "entry_slippage": entry_slippage
        }
        return position, new_balance

    def execute_exit(
        self,
        position: dict,
        exit_price: float,
        exit_reason: str,
        timestamp,
        balance: float,
        slippage: float,
        commission: float
    ) -> tuple:
        """Executes position exit computing gross & net PnL, fees, and updated balance."""
        direction = position["direction"]
        entry_price = position["entry_price"]
        quantity = position["quantity"]

        if direction == "LONG":
            exit_price_filled = exit_price * (1.0 - slippage)
            gross_pnl = (exit_price_filled - entry_price) * quantity
        else:
            exit_price_filled = exit_price * (1.0 + slippage)
            gross_pnl = (entry_price - exit_price_filled) * quantity

        exit_comm = (exit_price_filled * quantity) * commission
        total_comm = position["entry_comm"] + exit_comm
        net_pnl = gross_pnl - exit_comm
        new_balance = balance + (gross_pnl - exit_comm)
        perc_pnl = (net_pnl / (entry_price * quantity)) * 100.0

        trade_record = {
            "direction": direction,
            "entry_time": position["entry_time"],
            "exit_time": timestamp,
            "entry_price": entry_price,
            "exit_price": exit_price_filled,
            "quantity": quantity,
            "gross_pnl": gross_pnl,
            "commission": total_comm,
            "slippage": (abs(exit_price - exit_price_filled) + position["entry_slippage"]) * quantity,
            "net_pnl": net_pnl,
            "perc_pnl": perc_pnl,
            "exit_reason": exit_reason,
            "balance_after": new_balance
        }
        return trade_record, new_balance

    def merge_candles_and_signals(self, base_1m: pd.DataFrame, signals_df: pd.DataFrame) -> pd.DataFrame:
        """Merges 1m market candles with target timeframe signals using backward asof ffill."""
        if base_1m is None or base_1m.empty:
            return signals_df.copy()

        if "timestamp" in base_1m.columns:
            base_1m["timestamp"] = pd.to_datetime(base_1m["timestamp"])
        else:
            base_1m = base_1m.reset_index()
            base_1m["timestamp"] = pd.to_datetime(base_1m["timestamp"])

        if "timestamp" in signals_df.columns:
            signals_df["timestamp"] = pd.to_datetime(signals_df["timestamp"])
        else:
            signals_df = signals_df.reset_index()
            signals_df["timestamp"] = pd.to_datetime(signals_df["timestamp"])

        base_sorted = base_1m.sort_values("timestamp")
        sig_sorted = signals_df[["timestamp", "signal"]].sort_values("timestamp")

        merged = pd.merge_asof(
            base_sorted,
            sig_sorted,
            on="timestamp",
            direction="backward"
        )
        merged["signal"] = merged["signal"].fillna(0).astype(int)
        return merged

    def run_candle_simulation(self, df_1m: pd.DataFrame, sim_config: dict, strat_rules: dict, strategy_id: str):
        """Runs sequential 1m candle loop, managing live position state and ledger."""
        initial_balance = float(sim_config.get("initial_balance"))
        balance = initial_balance

        pos_size = sim_config.get("position_size") or {}
        if isinstance(pos_size, dict):
            pos_type = pos_size.get("type")
            pos_value = float(pos_size.get("value"))
        else:
            pos_type = sim_config.get("position_size_type")
            pos_value = float(sim_config.get("position_size_value"))

        commission = float(sim_config.get("commission"))
        slippage = float(sim_config.get("slippage"))
        allow_long = bool(sim_config.get("allow_long"))
        allow_short = bool(sim_config.get("allow_short"))

        tp_pct = float(strat_rules.get("take_profit")) / 100.0
        sl_pct = float(strat_rules.get("stop_loss")) / 100.0

        position = None
        trade_ledger = []

        # Ensure timestamp is a regular column
        if "timestamp" not in df_1m.columns:
            df_1m = df_1m.reset_index()
        if "timestamp" not in df_1m.columns and "index" in df_1m.columns:
            df_1m = df_1m.rename(columns={"index": "timestamp"})

        logger.info(f"Starting 1m candle loop for '{strategy_id}' on {len(df_1m)} bars...")

        for row in df_1m.itertuples(index=False):
            timestamp = row.timestamp
            high_p = float(row.high)
            low_p = float(row.low)
            close_p = float(row.close)
            sig_val = getattr(row, 'signal', 0)
            signal = int(sig_val) if pd.notna(sig_val) else 0

            # Step 1: Monitor active position & check exit
            if position is not None:
                entry_price = position["entry_price"]
                quantity = position["quantity"]
                position["current_price"] = close_p
                
                if position["direction"] == "LONG":
                    position["unrealized_pnl"] = (close_p - entry_price) * quantity
                else:
                    position["unrealized_pnl"] = (entry_price - close_p) * quantity

                exit_triggered, exit_price, exit_reason = self.evaluate_exit_conditions(
                    position, close_p, high_p, low_p, signal
                )

                if exit_triggered:
                    trade_record, balance = self.execute_exit(
                        position, exit_price, exit_reason, timestamp,
                        balance, slippage, commission
                    )
                    trade_ledger.append(trade_record)
                    close_simulation_position(self.conn, strategy_id, trade_record)
                    position = None

            # Step 2: Check entry signal if no active position
            if position is None and signal in (1, -1):
                direction = self.check_entry_signal(signal, allow_long, allow_short)
                if direction:
                    position, balance = self.execute_entry(
                        balance, direction, close_p, timestamp,
                        pos_type, pos_value, tp_pct, sl_pct, slippage, commission
                    )
                    if position is not None:
                        save_simulation_position(self.conn, strategy_id, position)

        # Sync final position state (remains OPEN if dataset finishes while position active)
        if position is not None:
            save_simulation_position(self.conn, strategy_id, position)

        ledger_df = pd.DataFrame(trade_ledger)
        return ledger_df, balance, position

    def run_strategy_simulation(self, strat: dict) -> dict:
        """Executes the complete simulation workflow for a single strategy."""
        s_id = strat["strategy_id"]
        exchange = strat["exchange"]
        symbol = strat["symbol"]
        target_tf = strat["target_timeframe"]
        strat_cfg = strat["strategy_config"] or {}
        ind_cfg = strat["indicators_config"] or {}
        
        # Read start_time and end_time directly from DB strategy_config
        start_time = strat_cfg.get("start_time") or strat.get("start_time") or "2026-07-19 00:00:00"
        end_time = strat_cfg.get("end_time") or strat.get("end_time") or "now"

        sim_config = strat.get("sim_config") or {}
        if not sim_config.get("enabled", True):
            logger.info(f"Skipping strategy '{s_id}': Execution is DISABLED in metadata.simulator_config.")
            return {"enabled": False, "status": "Skipped"}

        logger.info(f"Processing Simulation for strategy: [{s_id}] ({exchange.upper()} {symbol.upper()} {target_tf})...")

        # Dynamic signal calculation
        signal_input_dict = {
            "market": {
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": "1m",
                "target_timeframe": target_tf,
                "start_time": start_time,
                "end_time": end_time,
                "max_retries": 5,
                "retry_delay": 3
            },
            "indicators": ind_cfg,
            "strategy": strat_cfg
        }
        signals_df = run_signals_pipeline(strat_dict=signal_input_dict)
        if signals_df.empty or "signal" not in signals_df.columns:
            logger.warning(f"No signals generated for strategy '{s_id}'. Simulation skipped.")
            return {"enabled": True, "status": "No Signals"}

        # Fetch 1m candles & merge
        dl_1m = Downloader(exchange=exchange, symbol=symbol, timeframe="1m")
        try:
            base_1m = dl_1m.get_data(start_time=start_time, end_time=end_time)
        except Exception as e:
            logger.error(f"Error fetching 1m candles for '{s_id}': {e}")
            base_1m = pd.DataFrame()

        merged_df = self.merge_candles_and_signals(base_1m, signals_df)

        # Run sequential simulation
        create_simulations_schema_and_tables(self.conn, s_id)
        ledger_df, final_balance, active_pos = self.run_candle_simulation(
            merged_df, sim_config, strat_cfg, s_id
        )

        # Save closed trade ledger
        strat_table_name = s_id.lower().replace('.', '_')
        with self.conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE simulations.{strat_table_name};")
            self.conn.commit()

        if not ledger_df.empty:
            for trade_dict in ledger_df.to_dict("records"):
                insert_simulation_ledger(self.conn, s_id, trade_dict)

        # QuantStats performance calculation & stats DB persistence
        clean_metrics = {}
        if not ledger_df.empty and "perc_pnl" in ledger_df.columns:
            ledger_sorted = ledger_df.sort_values(by="exit_time")
            ledger_sorted["exit_time"] = pd.to_datetime(ledger_sorted["exit_time"])
            returns_series = ledger_sorted.set_index("exit_time")["perc_pnl"]

            raw_metrics = compute_all_metrics(returns_series, is_percentage=True)
            for k, v in raw_metrics.items():
                if isinstance(v, (float, int, str, bool)) or v is None:
                    clean_metrics[k] = v
                elif hasattr(v, "item"):
                    clean_metrics[k] = v.item()

        win_rate = float(clean_metrics.get("win_rate", 0.0) or 0.0) * 100.0
        winning_trades = int((ledger_df["net_pnl"] > 0).sum()) if not ledger_df.empty else 0
        losing_trades = int((ledger_df["net_pnl"] < 0).sum()) if not ledger_df.empty else 0
        total_pnl = float(ledger_df["net_pnl"].sum()) if not ledger_df.empty else 0.0

        stats_summary = {
            "initial_balance": sim_config["initial_balance"],
            "final_balance": final_balance,
            "total_pnl": total_pnl,
            "total_trades": len(ledger_df),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate
        }
        upsert_simulation_stats(self.conn, s_id, stats_summary, clean_metrics)

        return {
            "enabled": True,
            "status": "Success",
            "total_trades": len(ledger_df),
            "final_balance": final_balance,
            "net_pnl": total_pnl,
            "win_rate": win_rate,
            "active_position": active_pos
        }

    def run_pipeline(self, strategy_id: str = None) -> dict:
        """Master execution entry point: loops over discovered strategies."""
        results = {}
        strategies = self.fetch_strategies()
        if strategy_id:
            strategies = [s for s in strategies if s["strategy_id"] == strategy_id]

        logger.info(f"Running Simulator Engine pipeline for {len(strategies)} strategy definition(s)...")
        for strat in strategies:
            s_id = strat["strategy_id"]
            results[s_id] = self.run_strategy_simulation(strat)

        return results
