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
    upsert_execution_stats,
    insert_account_history,
    upsert_account_stats
)
from cryptosight.signals.main import run_signals_pipeline
from cryptosight.stats.metrices import compute_all_metrics
from cryptosight.execution.client import BybitExecutionClient

logger = get_logger("ExecutionEngine")


class ExecutionEngine:
    """
    Live Execution Engine for Quantitative Strategies.
    Reads simulator_config & strategy_config directly from DB metadata, evaluates signals,
    places Market/Limit orders on Bybit Demo/Live Account, handles position reversals and TP/SL exits,
    and logs active positions, trade history ledgers, and performance stats into dedicated 'execution' DB schema.
    """

    def __init__(self, conn=None):
        self.conn = conn
        self.client = BybitExecutionClient(conn=self.conn)
        logger.info("ExecutionEngine initialized with shared DB connection.")

    def fetch_best_strategies(self, exchange: str = None) -> list:
        """Fetches best high-return strategies (1 per symbol) via BybitExecutionClient."""
        return self.client.fetch_best_strategies(exchange=exchange)

    def parse_config(self, strategy: dict) -> tuple[dict, dict, dict]:
        """Parses and unwraps sim_config, strategy_config, and indicators_config JSON dictionaries from strategy record."""
        sim_cfg = strategy.get("sim_config") or {}
        if isinstance(sim_cfg, str):
            try:
                sim_cfg = json.loads(sim_cfg)
            except Exception:
                sim_cfg = {}
        if isinstance(sim_cfg, dict) and "simulator_config" in sim_cfg:
            sim_cfg = sim_cfg["simulator_config"]
        if not isinstance(sim_cfg, dict):
            sim_cfg = {}

        strat_cfg = strategy.get("strategy_config") or {}
        if isinstance(strat_cfg, str):
            try:
                strat_cfg = json.loads(strat_cfg)
            except Exception:
                strat_cfg = {}

        strat_rules = strat_cfg.get("strategy_config") if isinstance(strat_cfg, dict) and "strategy_config" in strat_cfg else strat_cfg
        if not isinstance(strat_rules, dict):
            strat_rules = {}

        ind_cfg = strategy.get("indicators_config") or {}
        if isinstance(ind_cfg, str):
            try:
                ind_cfg = json.loads(ind_cfg)
            except Exception:
                ind_cfg = {}

        return sim_cfg, strat_rules, ind_cfg

    def calculate_qty(self, allocated: float, close_price: float) -> float:
        """Calculates and rounds order lot size quantity based on Bybit exchange price tiers."""
        raw_qty = allocated / close_price if close_price > 0 else 0.001
        if close_price < 1.0:
            qty = round(raw_qty)          # DOGE, SUI (whole numbers)
        elif close_price < 100.0:
            qty = round(raw_qty, 2)        # SOL, ADA (2 decimals)
        else:
            qty = round(raw_qty, 3)        # BTC, ETH (3 decimals)
        return max(0.001, qty)

    def check_position_exit(self, active_position: dict, close_price: float, signal: str, allow_long: bool, allow_short: bool) -> tuple[bool, str]:
        """Checks active position for TP/SL price hits or opposite direction reversal signals."""
        pos_side = active_position["direction"]
        tp_price = active_position.get("take_profit")
        sl_price = active_position.get("stop_loss")

        # Check Take Profit & Stop Loss
        if pos_side == "BUY":
            if tp_price and close_price >= tp_price:
                return True, "TP_HIT"
            if sl_price and close_price <= sl_price:
                return True, "SL_HIT"
        elif pos_side == "SELL":
            if tp_price and close_price <= tp_price:
                return True, "TP_HIT"
            if sl_price and close_price >= sl_price:
                return True, "SL_HIT"

        # Check Reversal Signal
        if (pos_side == "BUY" and signal == "SELL" and allow_short) or (pos_side == "SELL" and signal == "BUY" and allow_long):
            return True, "REVERSAL_SIGNAL"

        return False, ""

    def close_position_trade(
        self,
        active_position: dict,
        close_price: float,
        close_reason: str,
        candle_time: str,
        slippage: float,
        commission: float,
        current_balance: float,
        strategy_id: str,
        symbol: str
    ) -> tuple[dict, float]:
        """Calculates trade PnL, logs completed trade into ledger, and updates DB positions/ledger tables."""
        pos_side = active_position["direction"]
        entry_price = active_position["entry_price"]
        pos_qty = active_position["quantity"]

        exit_price_filled = close_price * (1.0 - slippage) if pos_side == "BUY" else close_price * (1.0 + slippage)
        gross_pnl = (exit_price_filled - entry_price) * pos_qty if pos_side == "BUY" else (entry_price - exit_price_filled) * pos_qty
        comm_fee = (exit_price_filled * pos_qty) * commission
        net_pnl = gross_pnl - comm_fee
        new_balance = current_balance + net_pnl
        perc_pnl = (net_pnl / (entry_price * pos_qty)) * 100.0 if (entry_price * pos_qty) > 0 else 0.0

        completed_trade = {
            "trade_id": active_position["trade_id"],
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
            "balance": new_balance
        }

        if self.conn:
            try:
                insert_execution_ledger(self.conn, strategy_id, completed_trade)
                insert_account_history(self.conn, strategy_id, symbol, completed_trade)
                close_execution_position(self.conn, strategy_id, {
                    "exit_price": exit_price_filled,
                    "exit_time": candle_time,
                    "exit_reason": close_reason
                })
            except Exception as db_err:
                logger.warning(f"DB position close warning for '{strategy_id}': {db_err}")

        logger.info(f"Closed {pos_side} position for {symbol} @ ${exit_price_filled:.2f} ({close_reason}, Net PnL: ${net_pnl:+.2f}).")
        return completed_trade, new_balance

    def open_position_trade(
        self,
        signal: str,
        close_price: float,
        candle_time: str,
        current_balance: float,
        pos_size_type: str,
        pos_size_val: float,
        tp_price: float,
        sl_price: float,
        strategy_id: str,
        symbol: str,
        exchange: str,
        category: str,
        order_type: str
    ) -> dict:
        """Sizes capital allocation, calculates lot qty, places order on Bybit, and logs open position to DB."""
        if pos_size_type == "fixed_percentage":
            allocated = current_balance * (pos_size_val / 100.0)
        else:
            allocated = min(pos_size_val, current_balance)

        qty = self.calculate_qty(allocated, close_price)

        order_res = self.client.place_order(
            symbol=symbol,
            side="Buy" if signal == "BUY" else "Sell",
            qty=qty,
            exchange=exchange,
            category=category,
            order_type=order_type,
            price=close_price if (order_type and order_type.capitalize() == "Limit") else None,
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

        if self.conn:
            try:
                save_execution_position(self.conn, strategy_id, symbol, active_position)
            except Exception as db_err:
                logger.warning(f"DB save position warning for '{strategy_id}': {db_err}")

        logger.info(f"Opened {signal} position for {symbol} @ ${close_price:.2f} (Bybit OrderID: {order_res.get('order_id')}).")
        return active_position

    def finalize_execution_stats(self, ledger_entries: list, strategy_id: str, symbol: str, initial_balance: float, current_balance: float):
        """Computes performance metrics and updates DB execution.stats & account.stats tables."""
        if ledger_entries and self.conn:
            df_ledger = pd.DataFrame(ledger_entries)
            returns_series = pd.Series(
                df_ledger["perc_pnl"].values / 100.0,
                index=pd.to_datetime(df_ledger["exit_time"])
            )
            metrics_dict = compute_all_metrics(returns_series, is_percentage=False)
            try:
                upsert_execution_stats(self.conn, strategy_id, initial_balance, current_balance, ledger_entries, metrics_dict)
                upsert_account_stats(self.conn, symbol, initial_balance, current_balance, ledger_entries, metrics_dict)
            except Exception as db_err:
                logger.warning(f"DB execution stats update warning for '{strategy_id}': {db_err}")

    def execute_strategy(self, strategy: dict) -> dict:
        """Executes end-to-end pipeline for a single strategy."""
        strategy_id = str(strategy.get("strategy_id"))
        strategy_name = strategy.get("strategy_name")
        symbol = strategy.get("symbol", "").upper()
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

        # Step 2: Extract DB configs dynamically
        sim_config, strat_rules, ind_config = self.parse_config(strategy)
        strat_cfg = strategy.get("strategy_config") or {}

        initial_balance = float(strategy.get("initial_balance"))
        commission = float(strategy.get("commission"))
        slippage = float(strategy.get("slippage"))
        allow_long = bool(strategy.get("allow_long"))
        allow_short = bool(strategy.get("allow_short"))
        pos_size_type = strategy.get("position_size_type")
        pos_size_val = float(strategy.get("position_size_value"))


        tp_val = strat_rules.get("take_profit") or strategy.get("take_profit")
        sl_val = strat_rules.get("stop_loss") or strategy.get("stop_loss")
        tp_pct = float(tp_val) / 100.0 if tp_val else 0.0
        sl_pct = float(sl_val) / 100.0 if sl_val else 0.0
        category = strat_rules.get("category") or strategy.get("category")
        order_type = strat_rules.get("order_type") or strategy.get("order_type")
        exchange = strategy.get("exchange")

        # Step 3: Format strategy dictionary & run signals pipeline
        strat_dict = dict(strategy)
        strat_dict["strategy_config"] = strat_cfg
        strat_dict["indicators_config"] = ind_config
        strat_dict["market"] = {
            "exchange": exchange,
            "symbol": strategy.get("symbol"),
            "timeframe": strategy.get("timeframe") or target_tf,
            "target_timeframe": target_tf,
            "start_time": strat_rules.get("start_time"),
            "end_time": None
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

            # Dynamic TP/SL price calculation
            if signal == "BUY":
                tp_price = close_price * (1.0 + tp_pct) if tp_pct > 0 else None
                sl_price = close_price * (1.0 - sl_pct) if sl_pct > 0 else None
            elif signal == "SELL":
                tp_price = close_price * (1.0 - tp_pct) if tp_pct > 0 else None
                sl_price = close_price * (1.0 + sl_pct) if sl_pct > 0 else None
            else:
                tp_price, sl_price = None, None

            # Check position exit (TP/SL or Reversal)
            if active_position:
                is_close, close_reason = self.check_position_exit(active_position, close_price, signal, allow_long, allow_short)
                if is_close:
                    completed_trade, current_balance = self.close_position_trade(
                        active_position, close_price, close_reason, candle_time,
                        slippage, commission, current_balance, strategy_id, symbol
                    )
                    ledger_entries.append(completed_trade)
                    active_position = None

            # Open new position
            if not active_position and ((signal == "BUY" and allow_long) or (signal == "SELL" and allow_short)):
                active_position = self.open_position_trade(
                    signal, close_price, candle_time, current_balance,
                    pos_size_type, pos_size_val, tp_price, sl_price,
                    strategy_id, symbol, exchange, category, order_type
                )

        # Step 5: Finalize execution stats in DB
        self.finalize_execution_stats(ledger_entries, strategy_id, symbol, initial_balance, current_balance)

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

    def run_pipeline(self, strategy_id: str = None, exchange: str = None, top_n: int = None) -> dict:
        """Runs the live execution pipeline for top strategies."""
        results = {}
        if top_n is None:
            settings = self.client.get_execution_settings()
            top_n = settings.get("top_n", 1)

        if strategy_id:
            strategies = [s for s in self.fetch_best_strategies(exchange) if str(s["strategy_id"]) == str(strategy_id)]
        else:
            all_strats = self.fetch_best_strategies(exchange)
            strategies = all_strats[:top_n] if (top_n and top_n > 0) else all_strats

        logger.info(f"Running Live Execution Engine pipeline for top {len(strategies)} strategy definition(s)...")
        for strat in strategies:
            s_id = str(strat["strategy_id"])
            results[s_id] = self.execute_strategy(strat)

        return results
