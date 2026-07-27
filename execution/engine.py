"""
Core Execution Engine for Cryptosight Live/Demo Trading.
Handles signal generation, position tracking, TP/SL reconciliation, signal reversals,
and execution ledger & stats calculations.
"""

import math
import pandas as pd
from cryptosight.utils.db import (
    get_connection,
    upsert_execution_active_position,
    delete_execution_active_position,
    insert_execution_ledger,
    upsert_execution_stats,
    get_table_names,
    ingest_account_executions,
    ingest_account_closed_pnl,
    ingest_account_transaction_log,
    get_ingestion_state,
    update_ingestion_state,
    create_execution_active_positions_table,
    create_execution_stats_table,
    create_simulation_stats_table,
)
from cryptosight.utils.metadata import fetch_simulator_config, fetch_execution_config, create_strategy_data
from cryptosight.execution.selector import get_top_strategies
from cryptosight.execution.bybit_executor import BybitExecutor
from cryptosight.signals.main import run_signals_pipeline
from cryptosight.utils.logger import get_logger
from cryptosight.execution.account_stats import run_account_stats_cycle

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


def calculate_position_quantity(conn, strategy: dict, current_price: float, wallet_balance: float, executor=None) -> tuple:
    """
    Calculates trade position quantity, Take Profit price, and Stop Loss price.

    BUG 1 FIX: Sizing is based on metadata.execution_config.reference_balance,
    NOT live wallet equity. This keeps position sizing consistent per-strategy
    across a shared multi-strategy account, instead of one strategy's PnL
    shrinking/growing another strategy's position size via a shared live balance.
    The live `wallet_balance` parameter is used ONLY as an insufficient-funds
    guard: if the calculated order value exceeds the live available balance,
    the order is skipped (quantity forced to 0.0) rather than placed anyway.

    Rounds quantity down to nearest valid multiple of symbol's lot size step (qtyStep)
    and checks against minimum order quantity (minOrderQty).
    """
    exec_cfg = fetch_execution_config(conn)
    reference_balance = float(exec_cfg["reference_balance"])
    pos_type = str(exec_cfg["position_size_type"]).lower()
    pos_val = float(exec_cfg["position_size_value"])

    symbol = strategy.get("symbol", "BTCUSDT")
    qty_step = 0.001
    min_order_qty = 0.001

    if executor:
        info = executor.get_instrument_info(symbol)
        qty_step = info.get("qty_step", 0.001)
        min_order_qty = info.get("min_order_qty", 0.001)

    capital = reference_balance
    if capital <= 0:
        logger.warning(f"Reference balance is {capital} (<= 0), cannot size position. Returning 0 quantity.")
        quantity = 0.0
    else:
        allocated_usd = capital * (pos_val / 100.0) if pos_type in ("percent", "percentage") else pos_val
        raw_qty = allocated_usd / current_price if current_price > 0 else 0.0
        if qty_step > 0:
            quantity = math.floor(raw_qty / qty_step) * qty_step
            precision = max(0, -int(math.floor(math.log10(qty_step)))) if qty_step < 1 else 4
            quantity = round(quantity, precision)
        else:
            quantity = round(raw_qty, 4)

        if quantity < min_order_qty:
            logger.warning(f"Computed quantity {quantity} is below symbol minimum {min_order_qty}, skipping entry.")
            quantity = 0.0

    # BUG 1 FIX: Insufficient live-funds guard (reference_balance sizes the trade,
    # live wallet_balance only blocks it if the exchange can't actually cover it).
    if quantity > 0:
        order_value = quantity * current_price
        if order_value > float(wallet_balance):
            logger.warning(
                f"Insufficient live balance to open calculated position size for "
                f"'{strategy.get('strategy_name')}': order value ${order_value:,.2f} exceeds "
                f"live available balance ${wallet_balance:,.2f}. Setting quantity to 0."
            )
            quantity = 0.0

    strat_cfg = strategy.get("strategy_config", {})
    tp_val = strat_cfg.get("tp") if strat_cfg.get("tp") is not None else strat_cfg.get("take_profit")
    sl_val = strat_cfg.get("sl") if strat_cfg.get("sl") is not None else strat_cfg.get("stop_loss")

    if tp_val is None or sl_val is None:
        missing_key = "tp/take_profit" if tp_val is None else "sl/stop_loss"
        err_msg = (
            f"Strategy '{strategy.get('strategy_name')}' (ID #{strategy.get('strategy_id')}) missing "
            f"required risk config '{missing_key}' in strategy_config."
        )
        logger.error(err_msg)
        raise ValueError(err_msg)

    tp_pct = float(tp_val) / 100.0
    sl_pct = float(sl_val) / 100.0

    return quantity, tp_pct, sl_pct


def get_active_position_record(conn, strategy_id: int) -> dict:
    """
    Fetches OUR OWN stored active position record for a strategy directly from execution.active_positions.
    """
    query_sql = (
        "SELECT order_id, direction, entry_price, quantity, entry_time "
        "FROM execution.active_positions WHERE strategy_id = %s;"
    )
    try:
        df = pd.read_sql_query(query_sql, conn, params=(strategy_id,))
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "order_id": row["order_id"],
            "direction": row["direction"],
            "entry_price": float(row["entry_price"]),
            "quantity": float(row["quantity"]) if "quantity" in row and row["quantity"] is not None else 0.0,
            "entry_time": row["entry_time"],
        }
    except Exception as err:
        logger.warning(f"Could not fetch stored active position for strategy #{strategy_id}: {err}")
        return None


def to_utc_ms(t):
    if t is None:
        return 0
    if isinstance(t, (int, float)):
        return int(t)
    try:
        ts = pd.Timestamp(t)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        return int(ts.timestamp() * 1000)
    except Exception:
        return 0


def find_best_closed_pnl_match(closed_pnl_records: list, ref_entry_price: float, start_time=None, tolerance_pct: float = 0.005) -> dict:
    """
    BUG 4 FIX: Selects the closed_pnl record with the SMALLEST entry_price
    difference within tolerance and time window.
    """
    if not closed_pnl_records:
        return None

    start_ms = to_utc_ms(start_time)
    candidates = []
    for item in closed_pnl_records:
        item_time = item.get("updated_time") or item.get("created_time") or 0
        if start_ms > 0 and item_time < (start_ms - 60000):
            continue
        if ref_entry_price and ref_entry_price > 0:
            entry_diff_pct = abs(item["entry_price"] - ref_entry_price) / ref_entry_price
            if entry_diff_pct <= tolerance_pct:
                candidates.append((entry_diff_pct, item))

    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    # Return latest closed PnL record from Bybit if within time window
    return closed_pnl_records[0] if closed_pnl_records else None


def record_closed_trade(conn, strategy: dict, executor, entry_order_id: str, exit_order_id: str, direction: str, entry_price: float, exit_price: float, quantity: float, pnl: float, commission: float, exit_reason: str, entry_time=None, exit_time=None):
    """
    Helper to log closed trade into execution_ledgers and directly update execution.stats.
    STEP 5 FIX: Receives entry_order_id and exit_order_id explicitly, deduping against exit_order_id.
    BUG 2 FIX: Now accepts `executor` to fetch live post-trade wallet equity and
    stores it as balance_after in the ledger row.
    """
    strategy_id = strategy["strategy_id"]
    strategy_name = strategy["strategy_name"]
    symbol = strategy["symbol"]

    def to_utc_timestamp(t):
        if t is None:
            return pd.Timestamp.now(tz="UTC")
        if isinstance(t, pd.Timestamp) or hasattr(t, "tzinfo"):
            ts = pd.Timestamp(t)
            return ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")
        if isinstance(t, (int, float)):
            return pd.Timestamp(t, unit='ms', tz='UTC')
        ts = pd.Timestamp(t)
        return ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")

    final_entry = to_utc_timestamp(entry_time)
    final_exit = to_utc_timestamp(exit_time)

    gross_pnl = float(pnl + commission)
    net_pnl = float(pnl)
    cost_basis = entry_price * quantity if (entry_price * quantity) > 0 else 1.0
    return_pct = float(net_pnl / cost_basis * 100.0)

    import re
    clean_strat = re.sub(r'[^a-zA-Z0-9_]', '_', strategy_name.lower().strip())
    schema_name = "execution_ledgers"
    table_name = clean_strat

    # STEP 5: Duplicate check against exit_order_id
    try:
        dup_check_sql = f"SELECT 1 FROM {schema_name}.{table_name} WHERE exit_order_id = %s LIMIT 1;"
        existing = pd.read_sql_query(dup_check_sql, conn, params=(exit_order_id,))
        if not existing.empty:
            logger.info(f"Exit order '{exit_order_id}' already recorded in ledger for '{strategy_name}'; skipping duplicate insert.")
            delete_execution_active_position(conn, strategy_id)
            return
    except Exception as err:
        logger.warning(f"Could not check for duplicate ledger entry for exit order '{exit_order_id}': {err}")

    # BUG 2 FIX: Fetch live post-trade wallet equity for balance_after.
    exec_cfg = fetch_execution_config(conn)
    reference_balance = float(exec_cfg["reference_balance"])

    balance_after = reference_balance + net_pnl  # fallback default
    try:
        wallet_after = executor.get_wallet_balance("USDT")
        if wallet_after.get("fetch_ok", False):
            balance_after = wallet_after["total_equity"]
        else:
            logger.warning(
                f"Live wallet balance fetch failed after closing trade for strategy #{strategy_id} "
                f"('{strategy_name}'); using computed fallback balance_after=${balance_after:,.2f} "
                f"(reference_balance + net_pnl)."
            )
    except Exception as err:
        logger.warning(
            f"Error fetching live wallet balance after closing trade for strategy #{strategy_id}: {err}. "
            f"Using computed fallback balance_after=${balance_after:,.2f}."
        )

    # 1. Insert trade record into execution_ledgers.<strategy_name>
    insert_execution_ledger(
        conn=conn,
        strategy_name=strategy_name,
        entry_order_id=entry_order_id,
        exit_order_id=exit_order_id,
        entry_time=final_entry,
        exit_time=final_exit,
        direction=direction,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        gross_pnl=gross_pnl,
        commission=commission,
        net_pnl=net_pnl,
        return_pct=return_pct,
        exit_reason=exit_reason,
        balance_after=balance_after,
    )

    # 2. Delete position from active positions table
    delete_execution_active_position(conn, strategy_id)

    # 3. Read execution ledger and directly calculate & update execution.stats
    query_sql = f"SELECT * FROM {schema_name}.{table_name};"

    try:
        df_ledger = pd.read_sql_query(query_sql, conn)

        upsert_execution_stats(
            conn=conn,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            exchange=strategy["exchange"],
            symbol=symbol,
            timeframe=strategy["timeframe"],
            initial_balance=reference_balance,
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
        # Initialize required tables before the selector runs
        create_strategy_data(conn)
        create_execution_active_positions_table(conn)
        create_execution_stats_table(conn)
        create_simulation_stats_table(conn)

        strategies = get_top_strategies(conn, limit=10)
        if not strategies:
            logger.warning("No enabled strategy available in DB.")
            return

        executor = BybitExecutor(conn)

        for strategy in strategies:
            strategy_id = strategy["strategy_id"]
            strategy_name = strategy["strategy_name"]
            symbol = strategy["symbol"]

            if str(strategy["exchange"]).lower() != "bybit":
                logger.warning(f"Exchange '{strategy['exchange']}' is not yet supported for execution. Skipping this cycle for strategy #{strategy_id}.")
                continue

            wallet = executor.get_wallet_balance("USDT")
            if not wallet.get("fetch_ok", False):
                logger.error(f"Wallet balance fetch failed for strategy '{strategy_name}'. Skipping cycle to prevent unsafe position sizing.")
                continue

            bybit_pos = executor.get_open_position(symbol)

            # 1. Reconcile TP/SL hit on Bybit
            if not bybit_pos:
                stored_position = get_active_position_record(conn, strategy_id)

                if stored_position and stored_position.get("order_id"):
                    closed_pnl_records = executor.get_closed_pnl(symbol, start_time=stored_position["entry_time"])

                    matched_record = find_best_closed_pnl_match(
                        closed_pnl_records, stored_position["entry_price"], stored_position["entry_time"]
                    )

                    if matched_record:
                        exit_reason = matched_record.get("exit_reason") or "TP_SL_RECONCILED"
                        exit_order_id = matched_record["order_id"]
                        exit_price = float(matched_record["exit_price"])
                        quantity = float(matched_record.get("quantity") or stored_position.get("quantity", 0.0))
                        pnl = float(matched_record["closed_pnl"])
                        commission = float(matched_record["commission"])
                        exit_time = matched_record.get("updated_time") or matched_record.get("created_time")
                        logger.info(f"Reconciling closed trade on Bybit: PnL=${pnl:,.2f}, Reason={exit_reason}, ExitOrderID={exit_order_id}.")

                        record_closed_trade(
                            conn=conn,
                            strategy=strategy,
                            executor=executor,
                            entry_order_id=stored_position["order_id"],
                            exit_order_id=exit_order_id,
                            direction=stored_position["direction"],
                            entry_price=stored_position["entry_price"],
                            exit_price=exit_price,
                            quantity=quantity,
                            pnl=pnl,
                            commission=commission,
                            exit_reason=exit_reason,
                            entry_time=stored_position["entry_time"],
                            exit_time=exit_time,
                        )
                    else:
                        logger.warning(
                            f"Strategy #{strategy_id} ({symbol}): No closed PnL record returned from Bybit API yet."
                        )
                else:
                    logger.warning(
                        f"Strategy #{strategy_id} ({symbol}): No open position on Bybit and no stored active_position record in DB."
                    )

            # 2. Get latest candle signal and price
            signal, current_price = get_latest_signal_and_price(strategy)

            # 3. New Entry Logic (No Position Open)
            if not bybit_pos:
                if signal != 0:
                    direction = "LONG" if signal == 1 else "SHORT"
                    # STEP 9: Validates TP/SL internally
                    quantity, tp_pct, sl_pct = calculate_position_quantity(conn, strategy, current_price, wallet["available_balance"], executor=executor)

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
                        # BUG 3 FIX: confirm actual fill price/qty from Bybit instead of
                        # trusting the pre-trade signal candle's current_price/estimated quantity.
                        filled_pos = executor.wait_for_position_fill(symbol, direction)
                        if filled_pos:
                            actual_entry_price = filled_pos["entry_price"]
                            actual_quantity = filled_pos["quantity"]
                        else:
                            logger.warning(
                                f"Fill confirmation failed for {symbol} {direction} (strategy #{strategy_id}); "
                                f"falling back to estimated entry_price/quantity, which may be inaccurate."
                            )
                            actual_entry_price = current_price
                            actual_quantity = quantity

                        entry_time = pd.Timestamp.now()
                        upsert_execution_active_position(
                            conn=conn,
                            strategy_id=strategy_id,
                            strategy_name=strategy_name,
                            order_id=order["order_id"],
                            exchange=strategy["exchange"],
                            symbol=symbol,
                            timeframe=strategy["timeframe"],
                            direction=direction,
                            entry_time=entry_time,
                            entry_price=actual_entry_price,
                            quantity=actual_quantity,
                            mark_price=actual_entry_price,
                            liq_price=None,
                            take_profit=tp_price,
                            stop_loss=sl_price,
                            unrealized_pnl=0.0,
                            status="OPEN"
                        )
                        logger.info(f"Opened New Position: {direction} {actual_quantity} {symbol} at ${actual_entry_price:,.2f}.")

            # 4. Signal Reversal Logic (Position Currently Open)
            else:
                current_dir = bybit_pos["direction"]
                is_reversal = (current_dir == "LONG" and signal == -1) or (current_dir == "SHORT" and signal == 1)

                if is_reversal:
                    logger.info(f"Signal Reversal: Closing {current_dir} and opening opposite position...")
                    if executor.close_position(symbol=symbol, direction=current_dir, quantity=bybit_pos["quantity"]):
                        stored_pos = get_active_position_record(conn, strategy_id)
                        entry_order_id = stored_pos["order_id"] if (stored_pos and stored_pos.get("order_id")) else bybit_pos.get("order_id", "UNKNOWN_ENTRY")

                        closed_pnl_records = executor.get_closed_pnl(symbol, start_time=stored_pos.get("entry_time") if stored_pos else None)

                        # BUG 4 FIX: best-match selection instead of first-match break
                        closed_pnl_data = None
                        if closed_pnl_records and stored_pos and stored_pos.get("entry_time"):
                            start_ms = int(pd.Timestamp(stored_pos["entry_time"]).timestamp() * 1000)
                            closed_pnl_data = find_best_closed_pnl_match(
                                closed_pnl_records, bybit_pos["entry_price"], start_ms
                            )

                        pnl = closed_pnl_data["closed_pnl"] if closed_pnl_data else bybit_pos["unrealized_pnl"]
                        exit_price = closed_pnl_data["exit_price"] if closed_pnl_data else current_price

                        # STEP 4 FIX: Unique fallback for exit_order_id
                        unique_fallback = f"REVERSAL_{strategy_id}_{int(pd.Timestamp.now().timestamp() * 1000)}"
                        exit_order_id = closed_pnl_data["order_id"] if closed_pnl_data else unique_fallback

                        # BUG 5 FIX: bound the commission lookup window with an explicit end_time
                        # to prevent double-counting fees from a subsequent trade.
                        if closed_pnl_data:
                            commission = closed_pnl_data["commission"]
                        else:
                            end_time_ms = int(pd.Timestamp.now().timestamp() * 1000)
                            commission = executor.get_position_real_commission(
                                symbol,
                                start_time=stored_pos.get("entry_time") if stored_pos else None,
                                end_time=end_time_ms,
                            )

                        # STEP 5 FIX: Pass entry_order_id and exit_order_id
                        record_closed_trade(
                            conn=conn,
                            strategy=strategy,
                            executor=executor,
                            entry_order_id=entry_order_id,
                            exit_order_id=exit_order_id,
                            direction=current_dir,
                            entry_price=bybit_pos["entry_price"],
                            exit_price=exit_price,
                            quantity=bybit_pos["quantity"],
                            pnl=pnl,
                            commission=commission,
                            exit_reason="SIGNAL_REVERSAL",
                            entry_time=stored_pos.get("entry_time") if stored_pos else None,
                            exit_time=closed_pnl_data.get("updated_time") if closed_pnl_data else None,
                        )

                        new_dir = "LONG" if signal == 1 else "SHORT"
                        # Refresh wallet snapshot post-close before sizing the new position
                        wallet_post_close = executor.get_wallet_balance("USDT")
                        available_for_sizing = wallet_post_close["available_balance"] if wallet_post_close.get("fetch_ok", False) else wallet["available_balance"]

                        quantity, tp_pct, sl_pct = calculate_position_quantity(conn, strategy, current_price, available_for_sizing, executor=executor)

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
                            # BUG 3 FIX: confirm actual fill price/qty from Bybit
                            filled_pos = executor.wait_for_position_fill(symbol, new_dir)
                            if filled_pos:
                                actual_entry_price = filled_pos["entry_price"]
                                actual_quantity = filled_pos["quantity"]
                            else:
                                logger.warning(
                                    f"Fill confirmation failed for {symbol} {new_dir} (strategy #{strategy_id}, reversal); "
                                    f"falling back to estimated entry_price/quantity, which may be inaccurate."
                                )
                                actual_entry_price = current_price
                                actual_quantity = quantity

                            entry_time = pd.Timestamp.now()
                            upsert_execution_active_position(
                                conn=conn,
                                strategy_id=strategy_id,
                                strategy_name=strategy_name,
                                order_id=new_order["order_id"],
                                exchange=strategy["exchange"],
                                symbol=symbol,
                                timeframe=strategy["timeframe"],
                                direction=new_dir,
                                entry_time=entry_time,
                                entry_price=actual_entry_price,
                                quantity=actual_quantity,
                                mark_price=actual_entry_price,
                                liq_price=None,
                                take_profit=tp_price,
                                stop_loss=sl_price,
                                unrealized_pnl=0.0,
                                status="OPEN"
                            )
                            logger.info(f"Position Flipped: New {new_dir} {actual_quantity} {symbol} at ${actual_entry_price:,.2f}.")

                else:
                    # STEP 2 FIX: Do NOT overwrite order_id with "ACTIVE_ORDER". Reuse stored order_id.
                    # STEP 3 FIX: Do NOT reset entry_time to now(). Reuse stored entry_time.
                    stored_pos = get_active_position_record(conn, strategy_id)
                    order_id = stored_pos["order_id"] if (stored_pos and stored_pos.get("order_id")) else bybit_pos.get("order_id")
                    entry_time = stored_pos["entry_time"] if (stored_pos and stored_pos.get("entry_time")) else pd.Timestamp.now()

                    upsert_execution_active_position(
                        conn=conn,
                        strategy_id=strategy_id,
                        strategy_name=strategy_name,
                        order_id=order_id,
                        exchange=strategy["exchange"],
                        symbol=symbol,
                        timeframe=strategy["timeframe"],
                        direction=current_dir,
                        entry_time=entry_time,
                        entry_price=bybit_pos["entry_price"],
                        quantity=bybit_pos["quantity"],
                        mark_price=bybit_pos["mark_price"],
                        liq_price=bybit_pos["liq_price"],
                        take_profit=bybit_pos["take_profit"],
                        stop_loss=bybit_pos["stop_loss"],
                        unrealized_pnl=bybit_pos["unrealized_pnl"],
                        status="OPEN"
                    )
                    logger.info(f"Position Active: {current_dir} {bybit_pos['quantity']} {symbol} | Mark: ${bybit_pos['mark_price']:,.2f} | Unrel PnL: ${bybit_pos['unrealized_pnl']:,.2f}.")

        # Account history ingestion step
        try:
            state = get_ingestion_state(conn)
            last_exec = state.get("last_executions_time")
            last_pnl = state.get("last_closed_pnl_time")
            last_tx = state.get("last_tx_log_time")

            acc_execs = executor.get_account_executions(start_time=last_exec)
            acc_pnl = executor.get_account_closed_pnl(start_time=last_pnl)
            acc_tx = executor.get_transaction_log(start_time=last_tx)

            if acc_execs:
                ingest_account_executions(conn, acc_execs)
                exec_times = [int(item.get("execTime", 0)) for item in acc_execs if item.get("execTime")]
                if exec_times:
                    max_exec = max(exec_times)
                    if max_exec > (last_exec or 0):
                        update_ingestion_state(conn, last_executions_time=max_exec)
                else:
                    logger.warning(f"No 'execTime' field found in execution records; sample keys: {list(acc_execs[0].keys()) if acc_execs else 'N/A'}")

            if acc_pnl:
                ingest_account_closed_pnl(conn, acc_pnl)
                pnl_times = [int(item.get("updatedTime", 0)) for item in acc_pnl if item.get("updatedTime")]
                if pnl_times:
                    max_pnl = max(pnl_times)
                    if max_pnl > (last_pnl or 0):
                        update_ingestion_state(conn, last_closed_pnl_time=max_pnl)
                else:
                    logger.warning(f"No 'updatedTime' field found in closed PnL records; sample keys: {list(acc_pnl[0].keys()) if acc_pnl else 'N/A'}")

            if acc_tx:
                ingest_account_transaction_log(conn, acc_tx)
                tx_times = [int(item.get("transactionTime", 0)) for item in acc_tx if item.get("transactionTime")]
                if tx_times:
                    max_tx = max(tx_times)
                    if max_tx > (last_tx or 0):
                        update_ingestion_state(conn, last_tx_log_time=max_tx)
                else:
                    logger.warning(f"No 'transactionTime' field found in transaction log records; sample keys: {list(acc_tx[0].keys()) if acc_tx else 'N/A'}")

        except Exception as e:
            logger.warning(f"Failed to ingest account history: {e}")

        # Account stats cycle
        try:
            run_account_stats_cycle(conn)
        except Exception as e:
            logger.warning(f"Failed to run account stats cycle: {e}")

    except Exception as error:
        conn.rollback()
        logger.error(f"Error in execution engine cycle: {error}")
    finally:
        conn.close()