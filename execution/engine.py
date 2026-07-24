"""
Core Execution Engine for Cryptosight Live/Demo Trading.
Handles signal generation, position tracking, TP/SL reconciliation, signal reversals,
and execution ledger & stats calculations.
"""

import pandas as pd
from cryptosight.utils.db import (
    get_connection,
    upsert_execution_active_position,
    delete_execution_active_position,
    insert_execution_ledger,
    upsert_execution_stats,
    get_table_names,
)
from cryptosight.utils.metadata import fetch_simulator_config
from cryptosight.execution.selector import get_best_strategy
from cryptosight.execution.bybit_executor import BybitExecutor
from cryptosight.signals.main import run_signals_pipeline
from cryptosight.utils.logger import get_logger

logger = get_logger("ExecutionEngine")


def get_latest_signal_and_price(strategy: dict) -> tuple:
    """
    Fetches latest candle signal and price via signals pipeline.
    Returns (latest_signal, latest_close_price).
    """
    df_signals = run_signals_pipeline(strat_dict=strategy, save_to_db=False)
    if df_signals is None or df_signals.empty or "signal" not in df_signals.columns:
        logger.error(f"Signals pipeline returned invalid DataFrame for '{strategy['strategy_name']}'.")
        return 0, 0.0

    latest_row = df_signals.iloc[-1]
    latest_close = float(latest_row["close"])
    latest_signal = int(latest_row["signal"])
    logger.info(f"Latest Bar '{strategy['strategy_name']}': Signal={latest_signal}, Close Price=${latest_close:,.2f}.")

    return latest_signal, latest_close


def calculate_position_quantity(conn, strategy: dict, current_price: float, wallet_balance: float) -> tuple:
    """
    Calculates trade position quantity, Take Profit price, and Stop Loss price.
    """
    sim_cfg = fetch_simulator_config(conn)
    initial_bal = float(sim_cfg["initial_balance"])
    pos_type = str(sim_cfg["position_size_type"]).lower()
    pos_val = float(sim_cfg["position_size_value"])

    capital = wallet_balance if wallet_balance > 0 else initial_bal
    allocated_usd = capital * (pos_val / 100.0) if pos_type in ("percent", "percentage") else pos_val
    quantity = round(allocated_usd / current_price, 4) if current_price > 0 else 0.0

    strat_cfg = strategy["strategy_config"]
    tp_pct = float(strat_cfg.get("tp", strat_cfg.get("take_profit")))
    sl_pct = float(strat_cfg.get("sl", strat_cfg.get("stop_loss")))

    return quantity, tp_pct, sl_pct


def record_closed_trade(conn, strategy: dict, order_id: str, direction: str, entry_price: float, exit_price: float, quantity: float, pnl: float, commission: float, exit_reason: str):
    """
    Helper to log closed trade into execution_ledgers and directly update execution.stats.
    """
    strategy_id = strategy["strategy_id"]
    strategy_name = strategy["strategy_name"]
    symbol = strategy["symbol"]

    now = pd.Timestamp.now()
    gross_pnl = float(pnl + commission)
    net_pnl = float(pnl)
    cost_basis = entry_price * quantity if (entry_price * quantity) > 0 else 1.0
    return_pct = float(net_pnl / cost_basis * 100.0)

    # 1. Insert trade record into execution_ledgers.<strategy_name>
    insert_execution_ledger(
        conn=conn,
        strategy_name=strategy_name,
        order_id=order_id,
        entry_time=now,
        exit_time=now,
        direction=direction,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        gross_pnl=gross_pnl,
        commission=commission,
        net_pnl=net_pnl,
        return_pct=return_pct,
        exit_reason=exit_reason,
    )

    # 2. Delete position from active positions table
    delete_execution_active_position(conn, strategy_id)

    # 3. Read execution ledger and directly calculate & update execution.stats
    import re
    clean_strat = re.sub(r'[^a-zA-Z0-9_]', '_', strategy_name.lower().strip())
    schema_name = "execution_ledgers"
    table_name = clean_strat
    query_sql = f"SELECT * FROM {schema_name}.{table_name};"

    try:
        df_ledger = pd.read_sql_query(query_sql, conn)
        sim_cfg = fetch_simulator_config(conn)
        initial_balance = float(sim_cfg["initial_balance"])

        upsert_execution_stats(
            conn=conn,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            exchange=strategy["exchange"],
            symbol=symbol,
            timeframe=strategy["timeframe"],
            initial_balance=initial_balance,
            ledger_df=df_ledger,
        )
    except Exception as err:
        logger.warning(f"Could not compute and upsert execution.stats for strategy #{strategy_id}: {err}")


def run_execution_cycle():
    """
    Master execution function executed periodically by Windows runner.
    """
    conn = get_connection()
    if not conn:
        logger.error("Could not establish PostgreSQL connection.")
        return

    try:
        strategy = get_best_strategy(conn)
        if not strategy:
            logger.warning("No enabled strategy available in DB.")
            return

        strategy_id = strategy["strategy_id"]
        strategy_name = strategy["strategy_name"]
        symbol = strategy["symbol"]

        executor = BybitExecutor(conn)
        wallet = executor.get_wallet_balance("USDT")
        bybit_pos = executor.get_open_position(symbol)

        # 1. Reconcile TP/SL hit on Bybit
        if not bybit_pos:
            closed_pnl_data = executor.get_closed_pnl(symbol)
            if closed_pnl_data:
                logger.info(f"Reconciling closed trade on Bybit: PnL=${closed_pnl_data['closed_pnl']:,.2f}, Reason={closed_pnl_data['exit_reason']}.")
                record_closed_trade(
                    conn=conn,
                    strategy=strategy,
                    order_id=closed_pnl_data["order_id"],
                    direction="LONG" if "buy" in str(closed_pnl_data.get("exit_type", "")).lower() else "SHORT",
                    entry_price=closed_pnl_data["entry_price"],
                    exit_price=closed_pnl_data["exit_price"],
                    quantity=closed_pnl_data["quantity"],
                    pnl=closed_pnl_data["closed_pnl"],
                    commission=closed_pnl_data["commission"],
                    exit_reason=closed_pnl_data["exit_reason"],
                )

        # 2. Get latest candle signal and price
        signal, current_price = get_latest_signal_and_price(strategy)

        # 3. New Entry Logic (No Position Open)
        if not bybit_pos:
            if signal != 0:
                direction = "LONG" if signal == 1 else "SHORT"
                quantity, tp_pct, sl_pct = calculate_position_quantity(conn, strategy, current_price, wallet["available_balance"])

                tp_price = current_price * (1 + tp_pct) if direction == "LONG" else current_price * (1 - tp_pct)
                sl_price = current_price * (1 - sl_pct) if direction == "LONG" else current_price * (1 + sl_pct)

                order = executor.place_market_order(
                    symbol=symbol,
                    direction=direction,
                    quantity=quantity,
                    take_profit=tp_price,
                    stop_loss=sl_price,
                )

                if order:
                    upsert_execution_active_position(
                        conn=conn,
                        strategy_id=strategy_id,
                        order_id=order["order_id"],
                        exchange=strategy["exchange"],
                        symbol=symbol,
                        timeframe=strategy["timeframe"],
                        direction=direction,
                        entry_price=current_price,
                        quantity=quantity,
                        mark_price=current_price,
                        liq_price=None,
                        take_profit=tp_price,
                        stop_loss=sl_price,
                        unrealized_pnl=0.0,
                    )
                    logger.info(f"Opened New Position: {direction} {quantity} {symbol} at ${current_price:,.2f}.")

        # 4. Signal Reversal Logic (Position Currently Open)
        else:
            current_dir = bybit_pos["direction"]
            is_reversal = (current_dir == "LONG" and signal == -1) or (current_dir == "SHORT" and signal == 1)

            if is_reversal:
                logger.info(f"Signal Reversal: Closing {current_dir} and opening opposite position...")
                if executor.close_position(symbol=symbol, direction=current_dir, quantity=bybit_pos["quantity"]):
                    closed_pnl_data = executor.get_closed_pnl(symbol)
                    pnl = closed_pnl_data["closed_pnl"] if closed_pnl_data else bybit_pos["unrealized_pnl"]
                    exit_price = closed_pnl_data["exit_price"] if closed_pnl_data else current_price
                    order_id = closed_pnl_data["order_id"] if closed_pnl_data else "REVERSAL_ORDER"

                    record_closed_trade(
                        conn=conn,
                        strategy=strategy,
                        order_id=order_id,
                        direction=current_dir,
                        entry_price=bybit_pos["entry_price"],
                        exit_price=exit_price,
                        quantity=bybit_pos["quantity"],
                        pnl=pnl,
                        commission=bybit_pos["order_value"] * 0.0006,
                        exit_reason="SIGNAL_REVERSAL",
                    )

                    new_dir = "LONG" if signal == 1 else "SHORT"
                    quantity, tp_pct, sl_pct = calculate_position_quantity(conn, strategy, current_price, wallet["available_balance"])

                    tp_price = current_price * (1 + tp_pct) if new_dir == "LONG" else current_price * (1 - tp_pct)
                    sl_price = current_price * (1 - sl_pct) if new_dir == "LONG" else current_price * (1 + sl_pct)

                    new_order = executor.place_market_order(
                        symbol=symbol,
                        direction=new_dir,
                        quantity=quantity,
                        take_profit=tp_price,
                        stop_loss=sl_price,
                    )

                    if new_order:
                        upsert_execution_active_position(
                            conn=conn,
                            strategy_id=strategy_id,
                            order_id=new_order["order_id"],
                            exchange=strategy["exchange"],
                            symbol=symbol,
                            timeframe=strategy["timeframe"],
                            direction=new_dir,
                            entry_price=current_price,
                            quantity=quantity,
                            mark_price=current_price,
                            liq_price=None,
                            take_profit=tp_price,
                            stop_loss=sl_price,
                            unrealized_pnl=0.0,
                        )
                        logger.info(f"Position Flipped: New {new_dir} {quantity} {symbol} at ${current_price:,.2f}.")

            else:
                upsert_execution_active_position(
                    conn=conn,
                    strategy_id=strategy_id,
                    order_id=bybit_pos.get("order_id", "ACTIVE_ORDER"),
                    exchange=strategy["exchange"],
                    symbol=symbol,
                    timeframe=strategy["timeframe"],
                    direction=current_dir,
                    entry_price=bybit_pos["entry_price"],
                    quantity=bybit_pos["quantity"],
                    mark_price=bybit_pos["mark_price"],
                    liq_price=bybit_pos["liq_price"],
                    take_profit=bybit_pos["take_profit"],
                    stop_loss=bybit_pos["stop_loss"],
                    unrealized_pnl=bybit_pos["unrealized_pnl"],
                )
                logger.info(f"Position Active: {current_dir} {bybit_pos['quantity']} {symbol} | Mark: ${bybit_pos['mark_price']:,.2f} | Unrel PnL: ${bybit_pos['unrealized_pnl']:,.2f}.")

    except Exception as error:
        conn.rollback()
        logger.error(f"Error in execution engine cycle: {error}")
    finally:
        conn.close()
