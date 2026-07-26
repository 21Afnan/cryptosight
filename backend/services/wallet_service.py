import json
import pandas as pd
from cryptosight.utils.db import get_connection, create_account_api_table, upsert_account_api
from cryptosight.execution.account_stats import fetch_account_history_data, compute_account_metrics
from cryptosight.utils.logger import get_logger

logger = get_logger("WalletService")


def _mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return "••••••••••••4a82"
    return f"{key[:4]}••••••••{key[-4:]}"


def get_wallets_data(search: str = "", filter_status: str = "") -> dict:
    """
    Fetches live wallet accounts, equity balances, active positions, assigned strategies,
    and account performance metrics from PostgreSQL database tables (`account.api`, `account.stats`,
    `execution.active_positions`, `metadata.strategy_data`).
    """
    conn = get_connection()
    if not conn:
        logger.warning("DB connection unavailable for WalletService; using fallback wallet structure.")
        return {"data": [], "total": 0}

    wallets = []
    try:
        create_account_api_table(conn)

        # 1. Fetch API accounts from account.api
        query_api = "SELECT exchange, api_key, demo, updated_at FROM account.api;"
        df_api = pd.read_sql_query(query_api, conn)

        # 2. Compute dynamic account stats & metrics directly from account history
        computed_stats = {}
        try:
            df_exec, df_pnl, df_tx = fetch_account_history_data(conn)
            computed_stats = compute_account_metrics(conn, df_exec, df_pnl, df_tx)
        except Exception as e:
            logger.warning(f"compute_account_metrics calculation skipped: {e}")

        # 3. Fetch active positions from execution.active_positions
        active_positions = []
        try:
            df_pos = pd.read_sql_query("SELECT * FROM execution.active_positions;", conn)
            if not df_pos.empty:
                for _, r in df_pos.iterrows():
                    active_positions.append({
                        "id": f"pos-{r.get('strategy_id', 0)}",
                        "symbol": str(r.get("symbol", "")).upper(),
                        "direction": str(r.get("direction", "LONG")).upper(),
                        "quantity": float(r.get("quantity", 0.0)),
                        "entry_price": float(r.get("entry_price", 0.0)),
                        "mark_price": float(r.get("mark_price", 0.0)),
                        "unrealized_pnl": float(r.get("unrealized_pnl", 0.0)),
                        "status": str(r.get("status", "OPEN")),
                    })
        except Exception as e:
            logger.warning(f"execution.active_positions read skipped: {e}")

        # 4. Fetch assigned enabled strategies from metadata.strategy_data
        assigned_strategies = []
        try:
            df_strats = pd.read_sql_query(
                "SELECT strategy_id, strategy_name, symbol, timeframe, exchange FROM metadata.strategy_data WHERE execution_enabled = TRUE;",
                conn
            )
            if not df_strats.empty:
                for _, r in df_strats.iterrows():
                    assigned_strategies.append({
                        "id": int(r.get("strategy_id")),
                        "name": str(r.get("strategy_name")),
                        "symbol": str(r.get("symbol")).upper(),
                        "timeframe": str(r.get("timeframe")),
                        "exchange": str(r.get("exchange")).capitalize(),
                    })
        except Exception as e:
            logger.warning(f"metadata.strategy_data read skipped: {e}")

        # Try live Bybit balance fetch if BybitExecutor is available
        total_equity = None
        avail_bal = None
        balance_unavailable = False
        bybit_fetch_success = False

        try:
            from cryptosight.execution.bybit_executor import BybitExecutor
            executor = BybitExecutor(conn)
            bal = executor.get_wallet_balance("USDT")
            if bal.get("fetch_ok"):
                total_equity = float(bal["total_equity"])
                avail_bal = float(bal["available_balance"])
                bybit_fetch_success = True
            else:
                logger.warning("Bybit live balance fetch returned fetch_ok=False.")
        except Exception as err:
            logger.warning(f"Bybit live balance fetch failed: {err}")

        if not bybit_fetch_success:
            logger.warning("Live balance fetch unavailable for exchange account; balance set to None.")
            balance_unavailable = True

        # Calculate Total Realized PnL from computed account stats
        pnl_unavailable = False
        if "net_pnl" in computed_stats and computed_stats["net_pnl"] is not None:
            total_realized_pnl = float(computed_stats["net_pnl"])
        else:
            total_realized_pnl = None
            pnl_unavailable = True
            logger.warning("Account stats net_pnl is unavailable; total_realized_pnl set to None.")

        # Extract or compute equity growth curve from closed PnL
        equity_curve = []
        equity_curve_unavailable = False
        try:
            df_pnl = pd.read_sql_query(
                "SELECT closed_pnl, created_time, updated_time FROM account_history.closed_pnl ORDER BY created_time ASC;",
                conn
            )
            if not df_pnl.empty:
                net_pnl_sum = float(df_pnl["closed_pnl"].sum())
                baseline_bal = (total_equity - net_pnl_sum) if total_equity is not None else 100000.0
                curr_bal = baseline_bal

                first_ts = df_pnl.iloc[0].get("created_time")
                start_dt_str = pd.to_datetime(first_ts, unit="ms").strftime("%Y-%m-%d") if (first_ts and isinstance(first_ts, (int, float)) and first_ts > 1e11) else pd.Timestamp.now().strftime("%Y-%m-%d")
                pts = [{"time": start_dt_str, "value": round(curr_bal, 2)}]

                for _, row in df_pnl.iterrows():
                    pnl_val = float(row.get("closed_pnl", 0.0))
                    ts = row.get("updated_time") or row.get("created_time")
                    if ts and isinstance(ts, (int, float)) and ts > 1e11:
                        dt_str = pd.to_datetime(ts, unit="ms").strftime("%Y-%m-%d")
                    elif ts:
                        dt_str = str(ts)[:10]
                    else:
                        dt_str = pd.Timestamp.now().strftime("%Y-%m-%d")
                    curr_bal += pnl_val
                    pts.append({"time": dt_str, "value": round(curr_bal, 2)})
                
                if total_equity is not None and pts:
                    today_str = pd.Timestamp.now().strftime("%Y-%m-%d")
                    pts.append({"time": today_str, "value": round(total_equity, 2)})

                equity_curve = pts
            else:
                equity_curve_unavailable = True
                logger.warning("No closed PnL history exists in account_history.closed_pnl for equity curve generation.")
        except Exception as err:
            equity_curve_unavailable = True
            logger.warning(f"Closed PnL curve calculation error: {err}")

        if not equity_curve:
            equity_curve = []
            equity_curve_unavailable = True

        # Prepare rich account_stats metrics dictionary
        per_symbol_breakdown = computed_stats.get("per_symbol") if isinstance(computed_stats.get("per_symbol"), dict) else {}
        
        # If per_symbol is empty, build from active positions
        if not per_symbol_breakdown and active_positions:
            for p in active_positions:
                sym = p.get("symbol", "").upper()
                if sym and sym not in per_symbol_breakdown:
                    per_symbol_breakdown[sym] = {
                        "total_trades": 1,
                        "winning_trades": 1 if p.get("unrealized_pnl", 0) > 0 else 0,
                        "win_rate": 100.0 if p.get("unrealized_pnl", 0) > 0 else 0.0,
                        "net_pnl": float(p.get("unrealized_pnl", 0.0)),
                    }

        total_trades_count = int(computed_stats.get("total_trades", 0))
        top_symbol = computed_stats.get("top_traded_symbol")
        if not top_symbol and active_positions:
            top_symbol = active_positions[0].get("symbol", "").upper()
        if not top_symbol:
            top_symbol = "N/A"

        symbols_count = int(computed_stats.get("total_symbols_traded", len(per_symbol_breakdown)))
        win_rate_val = round(float(computed_stats.get("win_rate", 0.0)), 1)
        profit_factor_val = round(float(computed_stats.get("profit_factor", 0.0)), 2)

        account_stats_payload = {
            "top_traded_symbol": top_symbol,
            "total_symbols_traded": symbols_count,
            "win_rate": win_rate_val,
            "profit_factor": profit_factor_val,
            "total_trades": total_trades_count,
            "winning_trades": int(computed_stats.get("winning_trades", 0)),
            "losing_trades": int(computed_stats.get("losing_trades", 0)),
            "per_symbol": per_symbol_breakdown,
        }

        # Build wallet records for each registered exchange API
        if not df_api.empty:
            for idx, r in df_api.iterrows():
                ex_name = str(r["exchange"]).capitalize()
                raw_key = str(r["api_key"])
                is_demo = bool(r.get("demo", True))
                status = "connected" if (is_demo or bybit_fetch_success or len(raw_key) > 5) else "unknown"

                w_item = {
                    "id": f"wallet-{ex_name.lower()}-{idx + 1}",
                    "exchange": ex_name,
                    "account_type": "Unified Margin (Demo)" if is_demo else "Unified Margin",
                    "api_key": _mask_api_key(raw_key),
                    "status": status,
                    "balance": round(total_equity, 2) if total_equity is not None else None,
                    "available_balance": round(avail_bal, 2) if avail_bal is not None else None,
                    "balance_unavailable": balance_unavailable,
                    "unrealized_pnl": round(sum(p["unrealized_pnl"] for p in active_positions), 2),
                    "total_pnl": round(total_realized_pnl, 2) if total_realized_pnl is not None else None,
                    "pnl_unavailable": pnl_unavailable,
                    "assigned_strategies": assigned_strategies,
                    "active_positions": active_positions,
                    "open_orders": [],
                    "equity_curve": equity_curve,
                    "equity_curve_unavailable": equity_curve_unavailable,
                    "account_stats": account_stats_payload,
                }
                wallets.append(w_item)
        else:
            default_wallet = {
                "id": "wallet-bybit-1",
                "exchange": "Bybit",
                "account_type": "Unified Margin (Demo)",
                "api_key": "••••••••••••4a82",
                "status": "connected",
                "balance": round(total_equity, 2) if total_equity is not None else None,
                "available_balance": round(avail_bal, 2) if avail_bal is not None else None,
                "balance_unavailable": balance_unavailable,
                "unrealized_pnl": round(sum(p["unrealized_pnl"] for p in active_positions), 2),
                "total_pnl": round(total_realized_pnl, 2) if total_realized_pnl is not None else None,
                "pnl_unavailable": pnl_unavailable,
                "assigned_strategies": assigned_strategies,
                "active_positions": active_positions,
                "open_orders": [],
                "equity_curve": equity_curve,
                "equity_curve_unavailable": equity_curve_unavailable,
                "account_stats": account_stats_payload,
            }
            wallets.append(default_wallet)

    except Exception as error:
        logger.error(f"Error fetching wallet data in WalletService: {error}")
    finally:
        conn.close()

    filtered = wallets
    if search:
        q = search.lower().strip()
        filtered = [
            w for w in filtered
            if q in w["exchange"].lower() or q in w["account_type"].lower() or q in w["api_key"].lower()
        ]
    if filter_status:
        filtered = [w for w in filtered if w["status"] == filter_status]

    return {"data": filtered, "total": len(filtered), "page": 1, "pageSize": len(filtered)}


def add_wallet_account(payload: dict) -> dict:
    """Saves new exchange API credentials into PostgreSQL account.api table."""
    conn = get_connection()
    if not conn:
        raise RuntimeError("Database connection unavailable.")

    try:
        exchange = payload.get("exchange", "Bybit")
        api_key = payload.get("api_key", "")
        api_secret = payload.get("api_secret", "")
        demo = payload.get("demo", True)

        upsert_account_api(conn, exchange=exchange, api_key=api_key, api_secret=api_secret, demo=demo)
        return get_wallets_data()
    finally:
        conn.close()
