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


def calculate_position_quantity(conn, strategy: dict, current_price: float, wallet_balance: float) -> tuple:
    """
    Calculates trade position quantity, Take Profit price, and Stop Loss price.
    STEP 9 FIX: Explicitly validates TP/SL configuration presence to prevent float(None) crashes.
    """
    exec_cfg = fetch_execution_config(conn)
    initial_bal = float(exec_cfg["reference_balance"])
    pos_type = str(exec_cfg["position_size_type"]).lower()
    pos_val = float(exec_cfg["position_size_value"])

    capital = float(wallet_balance)
    if capital <= 0:
        logger.warning(f"Wallet balance is {capital} (<= 0), cannot size position. Returning 0 quantity.")
        quantity = 0.0
    else:
        allocated_usd = capital * (pos_val / 100.0) if pos_type in ("percent", "percentage") else pos_val
        quantity = round(allocated_usd / current_price, 4) if current_price > 0 else 0.0

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
        "SELECT order_id, direction, entry_price, entry_time "
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
            "entry_time": row["entry_time"],
        }
    except Exception as err:
        logger.warning(f"Could not fetch stored active position for strategy #{strategy_id}: {err}")
        return None


def record_closed_trade(conn, strategy: dict, entry_order_id: str, exit_order_id: str, direction: str, entry_price: float, exit_price: float, quantity: float, pnl: float, commission: float, exit_reason: str, entry_time=None, exit_time=None):
    """
    Helper to log closed trade into execution_ledgers and directly update execution.stats.
    STEP 5 FIX: Receives entry_order_id and exit_order_id explicitly, deduping against exit_order_id.
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
    )

    # 2. Delete position from active positions table
    delete_execution_active_position(conn, strategy_id)

    # 3. Read execution ledger and directly calculate & update execution.stats
    query_sql = f"SELECT * FROM {schema_name}.{table_name};"

    try:
        df_ledger = pd.read_sql_query(query_sql, conn)
        exec_cfg = fetch_execution_config(conn)
        initial_balance = float(exec_cfg["reference_balance"])

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
        # Initialize required tables before the selector runs
        create_strategy_data(conn)
        create_execution_active_positions_table(conn)
        create_execution_stats_table(conn)
        create_simulation_stats_table(conn)

        strategies = get_top_strategies(conn, limit=3)
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
                    # STEP 1 FIX: Query get_closed_pnl using startTime filter
                    closed_pnl_records = executor.get_closed_pnl(symbol, start_time=stored_position["entry_time"])
                    matched_record = None

                    if closed_pnl_records:
                        start_ms = int(pd.Timestamp(stored_position["entry_time"]).timestamp() * 1000)
                        for item in closed_pnl_records:
                            entry_diff = abs(item["entry_price"] - stored_position["entry_price"])
                            item_time = item["updated_time"] or item["created_time"]
                            # Match: entry_price within 0.1% tolerance AND time >= entry_time
                            if (entry_diff <= (0.001 * stored_position["entry_price"])) and (item_time >= start_ms - 1000):
                                matched_record = item
                                break

                    if matched_record:
                        exit_reason = matched_record.get("exit_reason") or "TP_SL_RECONCILED"
                        logger.info(f"Reconciling closed trade on Bybit: PnL=${matched_record['closed_pnl']:,.2f}, Reason={exit_reason}.")
                        # STEP 5 FIX: Pass entry_order_id and exit_order_id
                        record_closed_trade(
                            conn=conn,
                            strategy=strategy,
                            entry_order_id=stored_position["order_id"],
                            exit_order_id=matched_record["order_id"],
                            direction=stored_position["direction"],
                            entry_price=stored_position["entry_price"],
                            exit_price=matched_record["exit_price"],
                            quantity=matched_record["quantity"],
                            pnl=matched_record["closed_pnl"],
                            commission=matched_record["commission"],
                            exit_reason=exit_reason,
                            entry_time=stored_position["entry_time"],
                            exit_time=matched_record.get("updated_time") or matched_record.get("created_time"),
                        )
                    else:
                        logger.warning(
                            f"No matching closed PnL record found for strategy #{strategy_id} "
                            f"(entry_price={stored_position['entry_price']}, entry_time={stored_position['entry_time']})."
                        )
                else:
                    logger.debug(f"No stored active position in DB for strategy #{strategy_id}.")

            # 2. Get latest candle signal and price
            signal, current_price = get_latest_signal_and_price(strategy)

            # 3. New Entry Logic (No Position Open)
            if not bybit_pos:
                if signal != 0:
                    direction = "LONG" if signal == 1 else "SHORT"
                    # STEP 9: Validates TP/SL internally
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
                            entry_price=current_price,
                            quantity=quantity,
                            mark_price=current_price,
                            liq_price=None,
                            take_profit=tp_price,
                            stop_loss=sl_price,
                            unrealized_pnl=0.0,
                            status="OPEN"
                        )
                        logger.info(f"Opened New Position: {direction} {quantity} {symbol} at ${current_price:,.2f}.")

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
                        
                        closed_pnl_data = None
                        if closed_pnl_records and stored_pos and stored_pos.get("entry_time"):
                            start_ms = int(pd.Timestamp(stored_pos["entry_time"]).timestamp() * 1000)
                            for item in closed_pnl_records:
                                entry_diff = abs(item["entry_price"] - bybit_pos["entry_price"])
                                item_time = item["updated_time"] or item["created_time"]
                                if (entry_diff <= (0.001 * bybit_pos["entry_price"])) and (item_time >= start_ms - 1000):
                                    closed_pnl_data = item
                                    break

                        pnl = closed_pnl_data["closed_pnl"] if closed_pnl_data else bybit_pos["unrealized_pnl"]
                        exit_price = closed_pnl_data["exit_price"] if closed_pnl_data else current_price

                        # STEP 4 FIX: Unique fallback for exit_order_id
                        unique_fallback = f"REVERSAL_{strategy_id}_{int(pd.Timestamp.now().timestamp() * 1000)}"
                        exit_order_id = closed_pnl_data["order_id"] if closed_pnl_data else unique_fallback

                        # STEP 7 FIX: Real commission
                        commission = (
                            closed_pnl_data["commission"] if closed_pnl_data else executor.get_position_real_commission(symbol, start_time=stored_pos.get("entry_time") if stored_pos else None)
                        )

                        # STEP 5 FIX: Pass entry_order_id and exit_order_id
                        record_closed_trade(
                            conn=conn,
                            strategy=strategy,
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
                                entry_price=current_price,
                                quantity=quantity,
                                mark_price=current_price,
                                liq_price=None,
                                take_profit=tp_price,
                                stop_loss=sl_price,
                                unrealized_pnl=0.0,
                                status="OPEN"
                            )
                            logger.info(f"Position Flipped: New {new_dir} {quantity} {symbol} at ${current_price:,.2f}.")

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
                max_exec = max([int(item.get("execTime", 0)) for item in acc_execs if item.get("execTime")])
                if max_exec > (last_exec or 0):
                    update_ingestion_state(conn, last_executions_time=max_exec)

            if acc_pnl:
                ingest_account_closed_pnl(conn, acc_pnl)
                max_pnl = max([int(item.get("updatedTime", 0)) for item in acc_pnl if item.get("updatedTime")])
                if max_pnl > (last_pnl or 0):
                    update_ingestion_state(conn, last_closed_pnl_time=max_pnl)

            if acc_tx:
                ingest_account_transaction_log(conn, acc_tx)
                max_tx = max([int(item.get("transactionTime", 0)) for item in acc_tx if item.get("transactionTime")])
                if max_tx > (last_tx or 0):
                    update_ingestion_state(conn, last_tx_log_time=max_tx)
                    
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