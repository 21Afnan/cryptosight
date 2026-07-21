import json
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import (
    get_connection,
    create_simulations_schema_and_tables,
    save_simulation_position,
    insert_simulation_ledger
)
from cryptosight.utils.metadata import (
    create_strategy_data,
    create_simulator_config
)
from cryptosight.signals.main import run_signals_pipeline
from cryptosight.execution.bybit_executor import BybitExecutor

logger = get_logger("ExecutionEngine")


class ExecutionEngine:
    """
    Class-based Quantitative Live Execution Engine for Bybit Futures.
    Fetches 100% of strategy parameters, rules, risk settings, leverage, and sizing
    directly from PostgreSQL metadata tables without hardcoded default values.
    """

    def __init__(self, conn=None):
        self.conn = conn or get_connection()
        create_strategy_data(self.conn)
        create_simulator_config(self.conn)
        self.executor = BybitExecutor()

    def fetch_strategies(self) -> list:
        """Discovers all strategies and their database configurations in a single SQL JOIN query."""
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

                    sim_config = {
                        "strategy_id": s_id,
                        "enabled": enabled,
                        "initial_balance": float(init_bal) if init_bal is not None else None,
                        "position_size": {
                            "type": pos_type,
                            "value": float(pos_val) if pos_val is not None else None
                        },
                        "commission": float(comm) if comm is not None else None,
                        "slippage": float(slip) if slip is not None else None,
                        "allow_long": allow_l,
                        "allow_short": allow_s
                    }

                    strategies.append({
                        "strategy_id": s_id,
                        "exchange": ex,
                        "symbol": sym,
                        "target_timeframe": tf,
                        "strategy_config": strat_cfg or {},
                        "indicators_config": ind_cfg or {},
                        "sim_config": sim_config
                    })
            return strategies
        except Exception as e:
            logger.error(f"Error fetching strategy definitions from metadata: {e}")
            return []

    def calculate_position_size(self, balance: float, pos_type: str, pos_value: float, close_price: float) -> float:
        """Calculates trade coin quantity dynamically from balance and database sizing settings."""
        if close_price <= 0 or balance <= 0 or not pos_type or pos_value is None:
            return 0.0
        if pos_type == "fixed_percentage":
            allocated_usd = balance * (pos_value / 100.0)
        else:
            allocated_usd = pos_value
        return allocated_usd / close_price

    def sync_exchange_closed_trades(self, strategy_id: str, symbol: str) -> None:
        """Queries Bybit V5 API for actual closed trades and syncs them into PostgreSQL ledger tables."""
        closed_records = self.executor.get_closed_pnl(symbol=symbol, limit=20)
        if not closed_records:
            return

        strat_table_name = strategy_id.lower().replace('.', '_')
        create_simulations_schema_and_tables(self.conn, strategy_id)

        for trade in closed_records:
            try:
                side = trade.get("side", "")
                direction = "LONG" if side.lower() in ("buy", "long") else "SHORT"
                entry_p = float(trade.get("avgEntryPrice", 0.0))
                exit_p = float(trade.get("avgExitPrice", 0.0))
                qty = float(trade.get("qty", 0.0))
                closed_pnl = float(trade.get("closedPnl", 0.0))
                exec_type = trade.get("execType", "BybitExit")

                perc_pnl = ((exit_p - entry_p) / entry_p * 100.0) if entry_p > 0 else 0.0
                if direction == "SHORT":
                    perc_pnl = -perc_pnl

                trade_dict = {
                    "direction": direction,
                    "entry_time": pd.to_datetime(int(trade.get("createdTime", 0)), unit="ms", utc=True),
                    "exit_time": pd.to_datetime(int(trade.get("updatedTime", 0)), unit="ms", utc=True),
                    "entry_price": entry_p,
                    "exit_price": exit_p,
                    "quantity": qty,
                    "gross_pnl": closed_pnl,
                    "commission": 0.0,
                    "slippage": 0.0,
                    "net_pnl": closed_pnl,
                    "perc_pnl": perc_pnl,
                    "exit_reason": exec_type,
                    "balance_after": 0.0
                }
                insert_simulation_ledger(self.conn, strategy_id, trade_dict)
            except Exception as e:
                logger.warning(f"Could not sync closed trade row to DB: {e}")

    def execute_strategy(self, strat: dict) -> dict:
        """Executes live strategy signals and order management for a single strategy."""
        s_id = strat["strategy_id"]
        exchange = strat["exchange"]
        symbol = strat["symbol"]
        target_tf = strat["target_timeframe"]
        strat_cfg = strat["strategy_config"] or {}
        ind_cfg = strat["indicators_config"] or {}
        sim_cfg = strat["sim_config"] or {}

        if not sim_cfg.get("enabled"):
            logger.info(f"Skipping strategy '{s_id}': Execution is DISABLED in metadata.")
            return {"enabled": False, "status": "Skipped"}

        logger.info(f"Executing Live Strategy: [{s_id}] ({exchange.upper()} {symbol.upper()} {target_tf})...")

        # Step 1: Sync exchange closed trades into DB
        self.sync_exchange_closed_trades(s_id, symbol)

        # Step 2: Query current active positions from Bybit
        active_bybit_positions = self.executor.get_open_positions(symbol)
        has_active_bybit_position = len(active_bybit_positions) > 0

        # Step 3: Run dynamic signal pipeline for current candle
        signal_input_dict = {
            "market": {
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": "1m",
                "target_timeframe": target_tf,
                "start_time": strat_cfg.get("start_time"),
                "end_time": strat_cfg.get("end_time"),
                "max_retries": 5,
                "retry_delay": 3
            },
            "indicators": ind_cfg,
            "strategy": strat_cfg
        }
        signals_df = run_signals_pipeline(strat_dict=signal_input_dict)
        if signals_df.empty or "signal" not in signals_df.columns:
            logger.warning(f"No signals generated for '{s_id}'. Execution skipped.")
            return {"enabled": True, "status": "No Signals"}

        latest_row = signals_df.iloc[-1]
        sig_val = latest_row.get("signal", 0)
        signal = int(sig_val) if pd.notna(sig_val) else 0
        close_price = float(latest_row.get("close", 0.0))

        logger.info(f"Strategy '{s_id}' latest candle signal: {signal} at price: ${close_price:.2f}")

        # Step 4: Handle Order Execution if signal arrives & no active trade open
        if not has_active_bybit_position and signal in (1, -1):
            allow_long = sim_cfg.get("allow_long")
            allow_short = sim_cfg.get("allow_short")

            if signal == 1 and allow_long:
                direction = "LONG"
                side = "Buy"
            elif signal == -1 and allow_short:
                direction = "SHORT"
                side = "Sell"
            else:
                return {"enabled": True, "status": "Signal Disallowed"}

            wallet_balance = self.executor.get_wallet_balance(coin="USDT")
            balance = wallet_balance if wallet_balance > 0 else sim_cfg.get("initial_balance")
            if not balance:
                logger.warning(f"No wallet balance available for '{s_id}'. Order skipped.")
                return {"enabled": True, "status": "No Balance"}

            pos_size = sim_cfg.get("position_size") or {}
            pos_type = pos_size.get("type")
            pos_value = pos_size.get("value")

            qty = self.calculate_position_size(balance, pos_type, pos_value, close_price)
            if qty <= 0:
                logger.warning(f"Calculated trade quantity is 0 for '{s_id}'. Order skipped.")
                return {"enabled": True, "status": "Zero Quantity"}

            tp_val = strat_cfg.get("take_profit")
            sl_val = strat_cfg.get("stop_loss")
            tp_pct = float(tp_val) / 100.0 if tp_val is not None else 0.0
            sl_pct = float(sl_val) / 100.0 if sl_val is not None else 0.0

            if direction == "LONG":
                tp_price = close_price * (1.0 + tp_pct) if tp_pct > 0 else 0.0
                sl_price = close_price * (1.0 - sl_pct) if sl_pct > 0 else 0.0
            else:
                tp_price = close_price * (1.0 - tp_pct) if tp_pct > 0 else 0.0
                sl_price = close_price * (1.0 + sl_pct) if sl_pct > 0 else 0.0

            # Submit order to Bybit with exchange-level TP & SL
            order_res = self.executor.place_order(
                symbol=symbol,
                side=side,
                qty=qty,
                take_profit=tp_price,
                stop_loss=sl_price
            )

            # Save live open position to PostgreSQL simulations.positions
            pos_dict = {
                "direction": direction,
                "entry_time": latest_row.name if hasattr(latest_row, "name") else pd.Timestamp.now(tz="UTC"),
                "entry_price": close_price,
                "quantity": qty,
                "take_profit": tp_price,
                "stop_loss": sl_price,
                "current_price": close_price,
                "unrealized_pnl": 0.0,
                "status": "Open",
                "entry_comm": 0.0,
                "entry_slippage": 0.0
            }
            save_simulation_position(self.conn, s_id, pos_dict)
            return {"enabled": True, "status": f"Executed {direction}", "order": order_res}

        return {"enabled": True, "status": "Holding / Idle", "active_bybit_position": has_active_bybit_position}

    def run_pipeline(self, strategy_id: str = None) -> dict:
        """Master execution pipeline iterating over all strategies in metadata."""
        all_strats = self.fetch_strategies()
        if strategy_id:
            all_strats = [s for s in all_strats if s["strategy_id"] == strategy_id]

        logger.info(f"Running Live Execution Engine pipeline for {len(all_strats)} strategy definition(s)...")
        results = {}
        for strat in all_strats:
            s_id = strat["strategy_id"]
            results[s_id] = self.execute_strategy(strat)
        return results
