import os
import json
import uuid
import pandas as pd
from datetime import datetime
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import (
    create_execution_schema_and_tables,
    save_execution_position,
    close_execution_position,
    insert_execution_ledger,
    upsert_execution_stats
)
from cryptosight.signals.main import run_signals_pipeline
from cryptosight.stats.metrices import compute_all_metrics
from cryptosight.execution.client import BybitExecutionClient

logger = get_logger("ExecutionEngine")


class ExecutionEngine:
    """
    Live Execution Engine for Quantitative Strategies.
    Reads simulator_config & strategy_config directly from DB metadata, evaluates signals,
    places Market/Limit orders on Bybit Demo Account, handles position reversals and TP/SL exits,
    and logs active positions, trade history ledgers, and performance stats into dedicated 'execution' DB schema.
    """

    def __init__(self, conn=None):
        self.conn = conn
        self.client = BybitExecutionClient(conn=self.conn)
        logger.info("ExecutionEngine initialized with shared DB connection.")

    def fetch_best_strategies(self, exchange: str = "bybit") -> list:
        """Fetches best high-return strategies (1 per symbol) via BybitExecutionClient."""
        return self.client.fetch_best_strategies(exchange=exchange)

    def execute_strategy(self, strategy: dict, order_type: str = "Market") -> dict:
        """
        Executes end-to-end pipeline for a single strategy:
        1. Verifies/creates dedicated 'execution' schema tables (execution.positions, execution.strat_<id>, execution.stats).
        2. Format strategy dictionary with valid market config for run_signals_pipeline.
        3. Evaluates candle bars for entries, exits (TP/SL), and opposite direction reversals.
        4. Executes Market/Limit orders on Bybit Demo Account.
        5. Syncs positions in execution.positions, ledgers in execution.strat_<id>, and performance in execution.stats.
        """
        strategy_id = str(strategy.get("strategy_id"))
        strategy_name = strategy.get("strategy_name")
        symbol = strategy.get("symbol").upper()
        target_tf = strategy.get("target_timeframe")
        if not symbol.endswith("USDT"):
            symbol = f"{symbol}USDT"

        logger.info(f"=== Running Execution Engine for Strategy [{strategy_id}] '{strategy_name}' ({symbol} {target_tf}) ===")

        # Step 1: Create dedicated 'execution' schema tables
        if self.conn:
            try:
                create_execution_schema_and_tables(self.conn, strategy_id)
            except Exception as db_err:
                logger.warning(f"Execution schema creation warning for '{strategy_id}': {db_err}")

        # Step 2: Extract DB simulator_config and strategy rules dynamically
        sim_config = strategy.get("sim_config") or {}
        strat_cfg = strategy.get("strategy_config") or {}
        if isinstance(strat_cfg, str):
            try:
                strat_cfg = json.loads(strat_cfg)
            except Exception:
                strat_cfg = {}

        strat_rules = strat_cfg.get("strategy_config") if isinstance(strat_cfg, dict) and "strategy_config" in strat_cfg else strat_cfg
        if not isinstance(strat_rules, dict):
            strat_rules = {}

        initial_balance = float(sim_config.get("initial_balance") or 10000.0)
        commission = float(sim_config.get("commission") or 0.0006)
        slippage = float(sim_config.get("slippage") or 0.0001)
        allow_long = bool(sim_config.get("allow_long", True))
        allow_short = bool(sim_config.get("allow_short", True))
        
        pos_size_type = sim_config.get("position_size", {}).get("type") if isinstance(sim_config.get("position_size"), dict) else sim_config.get("position_size_type")
        pos_size_val = float((sim_config.get("position_size", {}).get("value") if isinstance(sim_config.get("position_size"), dict) else sim_config.get("position_size_value")) or 100.0)

        # TP / SL percentages directly from DB strategy config (e.g. 2.0 -> 2%, 1.0 -> 1%)
        tp_pct = float(strat_rules.get("take_profit") or 0.0) / 100.0
        sl_pct = float(strat_rules.get("stop_loss") or 0.0) / 100.0

        # Step 3: Format strategy dictionary & run signals pipeline
        strat_dict = dict(strategy)
        strat_dict["strategy_config"] = strat_cfg
        strat_dict["market"] = {
            "exchange": strategy.get("exchange", "bybit"),
            "symbol": strategy.get("symbol"),
            "timeframe": strategy.get("timeframe") or target_tf or "1m",
            "target_timeframe": target_tf,
            "start_time": strat_rules.get("start_time"),
            "end_time": strat_rules.get("end_time")
        }

        df_signals = run_signals_pipeline(strat_dict=strat_dict)

        if df_signals.empty or "signal" not in df_signals.columns:
            logger.error(f"Signal evaluation failed for strategy {strategy_id}.")
            return {"status": "Failed", "reason": "Signal generation failed"}

        # Step 4: Iterate candles & evaluate live signals, reversals, and TP/SL exits
        active_position = None
        ledger_entries = []
        current_balance = initial_balance

        for i, row in df_signals.iterrows():
            candle_time = str(row.name) if hasattr(row, "name") else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            close_price = float(row.get("close", 0.0))
            
            # Robust Signal parsing (handles integer 1/-1 as well as string BUY/SELL/LONG/SHORT)
            raw_sig = row.get("signal", 0)
            try:
                sig_val = int(raw_sig) if pd.notna(raw_sig) else 0
            except Exception:
                sig_val = 0
            sig_str = str(raw_sig).upper()

            if sig_val == 1 or sig_str in ("BUY", "LONG", "1"):
                signal = "BUY"
            elif sig_val == -1 or sig_str in ("SELL", "SHORT", "-1"):
                signal = "SELL"
            else:
                signal = "HOLD"

            # Dynamic TP/SL price calculation from DB strategy config
            if signal == "BUY":
                tp_price = close_price * (1.0 + tp_pct) if tp_pct > 0 else None
                sl_price = close_price * (1.0 - sl_pct) if sl_pct > 0 else None
            elif signal == "SELL":
                tp_price = close_price * (1.0 - tp_pct) if tp_pct > 0 else None
                sl_price = close_price * (1.0 + sl_pct) if sl_pct > 0 else None
            else:
                tp_price, sl_price = None, None

            # Check active position TP/SL hit or reversal
            if active_position:
                pos_side = active_position["direction"]
                entry_price = active_position["entry_price"]
                pos_qty = active_position["quantity"]
                trade_id = active_position["trade_id"]
                is_close = False
                close_reason = ""

                # Check TP/SL hit
                if pos_side == "BUY":
                    if active_position["take_profit"] and close_price >= active_position["take_profit"]:
                        is_close, close_reason = True, "TP_HIT"
                    elif active_position["stop_loss"] and close_price <= active_position["stop_loss"]:
                        is_close, close_reason = True, "SL_HIT"
                elif pos_side == "SELL":
                    if active_position["take_profit"] and close_price <= active_position["take_profit"]:
                        is_close, close_reason = True, "TP_HIT"
                    elif active_position["stop_loss"] and close_price >= active_position["stop_loss"]:
                        is_close, close_reason = True, "SL_HIT"

                # Check Opposite Direction Reversal Signal
                if (pos_side == "BUY" and signal == "SELL" and allow_short) or (pos_side == "SELL" and signal == "BUY" and allow_long):
                    is_close, close_reason = True, "REVERSAL_SIGNAL"

                if is_close:
                    exit_price_filled = close_price * (1.0 - slippage) if pos_side == "BUY" else close_price * (1.0 + slippage)
                    gross_pnl = (exit_price_filled - entry_price) * pos_qty if pos_side == "BUY" else (entry_price - exit_price_filled) * pos_qty
                    comm_fee = (exit_price_filled * pos_qty) * commission
                    net_pnl = gross_pnl - comm_fee
                    current_balance += net_pnl
                    perc_pnl = (net_pnl / (entry_price * pos_qty)) * 100.0 if (entry_price * pos_qty) > 0 else 0.0

                    completed_trade = {
                        "trade_id": trade_id,
                        "entry_time": active_position["entry_time"],
                        "exit_time": candle_time,
                        "direction": pos_side,
                        "entry_price": entry_price,
                        "exit_price": exit_price_filled,
                        "quantity": pos_qty,
                        "gross_pnl": gross_pnl,
                        "commission": comm_fee,
                        "slippage": slippage,
                        "net_pnl": net_pnl,
                        "perc_pnl": perc_pnl,
                        "exit_reason": close_reason,
                        "balance": current_balance
                    }
                    ledger_entries.append(completed_trade)

                    # Update dedicated execution schema DB tables
                    if self.conn:
                        try:
                            insert_execution_ledger(self.conn, strategy_id, completed_trade)
                            close_execution_position(self.conn, strategy_id, {
                                "exit_price": exit_price_filled,
                                "exit_time": candle_time,
                                "exit_reason": close_reason
                            })
                        except Exception as db_err:
                            logger.warning(f"DB position close warning for '{strategy_id}': {db_err}")

                    logger.info(f"Closed {pos_side} position for {symbol} @ ${exit_price_filled:.2f} ({close_reason}, Net PnL: ${net_pnl:+.2f}).")
                    active_position = None

            # Open new trade signal
            if not active_position and ((signal == "BUY" and allow_long) or (signal == "SELL" and allow_short)):
                # Position sizing from DB simulator_config
                if pos_size_type == "fixed_percentage":
                    allocated = current_balance * (pos_size_val / 100.0)
                else:
                    allocated = min(pos_size_val, current_balance)
                qty = max(0.001, allocated / close_price)

                # Execute order on Bybit Demo Account
                order_res = self.client.place_order(
                    symbol=symbol,
                    side="Buy" if signal == "BUY" else "Sell",
                    order_type=order_type,
                    qty=qty,
                    price=close_price if order_type.capitalize() == "Limit" else None,
                    category="linear",
                    take_profit=tp_price,
                    stop_loss=sl_price
                )

                trade_id = str(uuid.uuid4())[:8]
                active_position = {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "direction": signal,
                    "entry_time": candle_time,
                    "entry_price": close_price,
                    "quantity": qty,
                    "take_profit": tp_price,
                    "stop_loss": sl_price,
                    "current_price": close_price,
                    "unrealized_pnl": 0.0,
                    "status": "Open",
                    "bybit_order_id": order_res.get("order_id")
                }

                # Save active position in execution.positions DB table
                if self.conn:
                    try:
                        save_execution_position(self.conn, strategy_id, symbol, active_position)
                    except Exception as db_err:
                        logger.warning(f"DB save position warning for '{strategy_id}': {db_err}")

                logger.info(f"Opened {signal} position for {symbol} @ ${close_price:.2f} (Bybit OrderID: {order_res.get('order_id')}).")

        # Step 5: Compute performance metrics & update execution.stats
        if ledger_entries and self.conn:
            df_ledger = pd.DataFrame(ledger_entries)
            metrics_dict = compute_all_metrics(df_ledger, initial_balance=initial_balance)
            try:
                upsert_execution_stats(self.conn, strategy_id, initial_balance, current_balance, ledger_entries, metrics_dict)
            except Exception as db_err:
                logger.warning(f"DB execution stats update warning for '{strategy_id}': {db_err}")

        total_trades = len(ledger_entries)
        total_pnl = current_balance - initial_balance
        logger.info(f"=== Strategy [{strategy_id}] Finished: Total Trades={total_trades}, Net PnL=${total_pnl:+.2f} ===")
        return {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "total_trades": total_trades,
            "initial_balance": initial_balance,
            "final_balance": current_balance,
            "total_pnl": total_pnl
        }

    def run_pipeline(self, strategy_id: str = None, exchange: str = "bybit", order_type: str = "Market") -> dict:
        """Runs the live execution pipeline for all top unique-symbol Bybit strategies."""
        results = {}
        if strategy_id:
            strategies = [s for s in self.fetch_best_strategies(exchange) if str(s["strategy_id"]) == str(strategy_id)]
        else:
            strategies = self.fetch_best_strategies(exchange)

        logger.info(f"Running Live Execution Engine pipeline for {len(strategies)} top strategy definition(s)...")
        for strat in strategies:
            s_id = str(strat["strategy_id"])
            results[s_id] = self.execute_strategy(strat, order_type=order_type)

        return results
