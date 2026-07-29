import warnings
import json
import pandas as pd
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

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
                        "exchange": str(r.get("exchange", "")).lower(),
                        "direction": str(r.get("direction", "LONG")).upper(),
                        "quantity": float(r.get("quantity", 0.0)),
                        "entry_price": float(r.get("entry_price", 0.0)),
                        "mark_price": float(r.get("mark_price", 0.0)),
                        "liq_price": float(r.get("liq_price", 0.0)) if pd.notna(r.get("liq_price")) else None,
                        "unrealized_pnl": float(r.get("unrealized_pnl", 0.0)),
                        "status": str(r.get("status", "OPEN")),
                        "strategy_name": str(r.get("strategy_name")) if pd.notna(r.get("strategy_name")) else f"Strategy {r.get('strategy_id')}",
                    })
        except Exception as e:
            logger.warning(f"execution.active_positions read skipped: {e}")

        # 4. Fetch all assigned strategies from metadata.strategy_data (active & disabled)
        assigned_strategies = []
        try:
            df_strats = pd.read_sql_query(
                "SELECT strategy_id, strategy_name, symbol, timeframe, exchange, execution_enabled FROM metadata.strategy_data;",
                conn
            )
            if not df_strats.empty:
                for _, r in df_strats.iterrows():
                    assigned_strategies.append({
                        "id": int(r.get("strategy_id")),
                        "strategy_id": int(r.get("strategy_id")),
                        "name": str(r.get("strategy_name")),
                        "symbol": str(r.get("symbol")).upper(),
                        "timeframe": str(r.get("timeframe")),
                        "exchange": str(r.get("exchange")).capitalize(),
                        "execution_enabled": bool(r.get("execution_enabled") if r.get("execution_enabled") is not None else True),
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
                df_pnl["closed_pnl"] = pd.to_numeric(df_pnl["closed_pnl"], errors="coerce").fillna(0.0)
                net_pnl_sum = float(df_pnl["closed_pnl"].sum())
                baseline_bal = (total_equity - net_pnl_sum) if total_equity is not None else 100000.0
                curr_bal = baseline_bal

                def _to_unix_sec(raw_ts) -> int:
                    if not raw_ts:
                        return int(pd.Timestamp.now().timestamp())
                    try:
                        num = float(raw_ts)
                        if num > 1e11:  # Epoch ms
                            return int(num / 1000)
                        elif num > 1e8: # Epoch s
                            return int(num)
                    except Exception:
                        pass
                    try:
                        dt = pd.to_datetime(str(raw_ts).replace("T", " ").split("+")[0])
                        return int(dt.timestamp())
                    except Exception:
                        return int(pd.Timestamp.now().timestamp())

                first_raw_ts = df_pnl.iloc[0].get("created_time")
                start_ts_sec = _to_unix_sec(first_raw_ts) - 60  # Start 1 minute before first trade
                pts = [{"time": start_ts_sec, "value": round(curr_bal, 2)}]

                for _, row in df_pnl.iterrows():
                    pnl_val = float(row.get("closed_pnl", 0.0))
                    raw_ts = row.get("updated_time") or row.get("created_time")
                    ts_sec = _to_unix_sec(raw_ts)

                    curr_bal += pnl_val
                    pts.append({"time": ts_sec, "value": round(curr_bal, 2)})

                if total_equity is not None and pts:
                    now_sec = int(pd.Timestamp.now().timestamp())
                    last_sec = pts[-1]["time"]
                    final_sec = max(now_sec, last_sec + 60)
                    pts.append({"time": final_sec, "value": round(total_equity, 2)})

                # Ensure strict ascending timestamps for lightweight-charts
                pts.sort(key=lambda p: p["time"])
                # Deduplicate exact duplicate timestamps by incrementing 1 second
                for i in range(1, len(pts)):
                    if pts[i]["time"] <= pts[i-1]["time"]:
                        pts[i]["time"] = pts[i-1]["time"] + 1

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
        exchange = payload.get("exchange")
        api_key = payload.get("api_key")
        api_secret = payload.get("api_secret")
        demo = payload.get("demo")

        upsert_account_api(conn, exchange=exchange, api_key=api_key, api_secret=api_secret, demo=demo)
        return get_wallets_data()
    finally:
        conn.close()
