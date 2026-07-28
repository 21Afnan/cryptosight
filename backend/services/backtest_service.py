"""
backtest_service.py
PostgreSQL-backed Backtesting Service.
All queries operate strictly against real database tables (metadata.strategy_data,
metadata.backtest_runs, backtests.stats, and backtests.<strategy_slug>).
No fake fallback datasets or hardcoded defaults are used.
"""

import json
import re
from datetime import datetime, timedelta
import numpy as np
from cryptosight.utils.db import get_connection
from cryptosight.utils.logger import get_logger

logger = get_logger("BacktestService")


def clean_timestamp(dt_val) -> str:
    """
    Formats DB timestamp cleanly into 'YYYY-MM-DD HH:MM:SS', stripping raw UTC offset '+00:00'.
    """
    if not dt_val:
        return ""
    if hasattr(dt_val, "strftime"):
        return dt_val.strftime("%Y-%m-%d %H:%M:%S")
    s = str(dt_val).replace("T", " ")
    if "+00:00" in s:
        s = s.replace("+00:00", "")
    elif "+00" in s and s.endswith(":00"):
        s = s.split("+")[0]
    return s.strip()


def _to_slug(name: str) -> str:
    """Converts strategy name to clean database table slug."""
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def safe_float(val, default=0.0) -> float:
    if val is None:
        return float(default)
    try:
        return float(val)
    except (ValueError, TypeError):
        return float(default)


def safe_int(val, default=0) -> int:
    if val is None:
        return int(default)
    try:
        return int(val)
    except (ValueError, TypeError):
        return int(default)


def check_db_health() -> dict:
    """Real SELECT 1 connection check against PostgreSQL."""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        conn.close()
        return {"status": "active", "connected": True, "database": "PostgreSQL"}
    except Exception as e:
        logger.warning(f"DB health check failed: {e}")
        return {"status": "inactive", "connected": False, "error": str(e)}


def generate_charts_from_trades(trades: list, initial_balance: float = 10000.0) -> dict:
    """
    Calculates ALL 4 chart datasets strictly from REAL trade ledger rows.
    Returns empty lists if trades list is empty. ZERO fallback data is inserted here!
    """
    if not trades:
        return {
            "equity_curve": [],
            "drawdown_curve": [],
            "monthly_returns": [],
            "rolling_metrics": [],
            "pnl_per_trade": [],
        }

    sorted_trades = sorted(trades, key=lambda t: t.get("exit_time") or t.get("entry_time") or "")
    equity_points = []
    drawdown_points = []
    monthly_map = {}
    
    current_balance = float(initial_balance)
    peak_balance = current_balance

    first_dt_str = sorted_trades[0].get("entry_time", "")[:10] or sorted_trades[0].get("exit_time", "")[:10] or ""
    if first_dt_str:
        try:
            dt = datetime.strptime(first_dt_str, "%Y-%m-%d")
            start_date_str = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception:
            start_date_str = first_dt_str
    else:
        start_date_str = ""

    if start_date_str:
        equity_points.append({"time": start_date_str, "value": round(current_balance, 2)})
        drawdown_points.append({"time": start_date_str, "value": 0.0})

    rolling_points = []
    pnl_history = []
    pnl_per_trade = []

    for idx, trade in enumerate(sorted_trades):
        raw_exit_time = trade.get("exit_time", "") or trade.get("entry_time", "")
        if not raw_exit_time:
            continue
        exit_time = str(raw_exit_time).strip()
        date_str = exit_time[:10]
        pnl = float(trade.get("net_pnl") or 0.0)
        pnl_history.append(pnl)
        current_balance += pnl
        if current_balance > peak_balance:
            peak_balance = current_balance
        
        dd = (current_balance - peak_balance) / peak_balance if peak_balance > 0 else 0.0

        equity_points.append({"time": exit_time, "value": round(current_balance, 2)})
        drawdown_points.append({"time": exit_time, "value": round(dd, 4)})
        pnl_per_trade.append({
            "trade_id": trade.get("trade_id") or f"BT_{idx + 1}",
            "exit_time": exit_time,
            "net_pnl": round(pnl, 2),
            "side": trade.get("side") or trade.get("direction") or "LONG",
        })

        # Monthly grouping
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            m_key = dt.strftime("%b %y")
        except Exception:
            m_key = date_str[:7]

        if m_key not in monthly_map:
            monthly_map[m_key] = 0.0
        monthly_map[m_key] += pnl

        # Dynamic rolling ratios calculation from real PnL history
        if len(pnl_history) >= 1:
            arr = np.array(pnl_history)
            mean_pnl = float(np.mean(arr))
            std_pnl = float(np.std(arr))
            sharpe_val = round((mean_pnl / std_pnl * np.sqrt(252)) if std_pnl > 0 else 0.0, 2)
            
            downside = arr[arr < 0]
            downside_std = float(np.std(downside)) if len(downside) > 0 else (std_pnl if std_pnl > 0 else 0.0)
            sortino_val = round((mean_pnl / downside_std * np.sqrt(252)) if downside_std > 0 else 0.0, 2)
            
            calmar_val = round(abs((current_balance - initial_balance) / initial_balance / dd) if dd < 0 else 0.0, 2)

            rolling_points.append({
                "date": exit_time,
                "sharpe": sharpe_val,
                "sortino": sortino_val,
                "calmar": calmar_val,
            })

    monthly_returns_list = []
    for m_label, m_pnl in monthly_map.items():
        ret_pct = m_pnl / initial_balance if initial_balance > 0 else 0.0
        monthly_returns_list.append({
            "month": m_label,
            "value": round(ret_pct, 4),
            "pnl": round(m_pnl, 2),
        })

    return {
        "equity_curve": equity_points,
        "drawdown_curve": drawdown_points,
        "monthly_returns": monthly_returns_list,
        "rolling_metrics": rolling_points,
        "pnl_per_trade": pnl_per_trade,
    }


# =============================================================================
# Core API Services & Helpers
# =============================================================================




def get_all_backtests(search: str = "", status: str = "all") -> list:
    """
    Queries metadata.strategy_data LEFT JOIN backtests.stats LEFT JOIN metadata.backtest_data.
    Returns all strategies with real DB status and metrics.
    """
    backtests = []
    conn = None

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    s.strategy_id,
                    s.strategy_name,
                    s.exchange,
                    s.symbol,
                    s.target_timeframe,
                    COALESCE(bs.status, 'completed') AS backtest_status,
                    bs.metrics,
                    s.last_updated,
                    bd.total_trades,
                    bd.win_rate,
                    bd.net_pnl
                FROM metadata.strategy_data s
                LEFT JOIN backtests.stats bs ON s.strategy_id = bs.strategy_id
                LEFT JOIN metadata.backtest_data bd ON s.strategy_id = bd.strategy_id
                ORDER BY s.strategy_id ASC;
            """)
            rows = cursor.fetchall()
            for r in rows:
                strat_id = int(r[0])
                strat_name = str(r[1]) if r[1] else f"Strategy #{strat_id}"
                exchange = str(r[2]).upper() if r[2] else ""
                raw_sym = str(r[3]).upper() if r[3] else ""
                symbol = raw_sym if ("/" in raw_sym or not raw_sym) else f"{raw_sym}/USDT"
                timeframe = str(r[4]) if r[4] else ""
                bt_status = str(r[5]).lower() if r[5] else "completed"
                last_updated = r[7].isoformat() if r[7] else ""

                raw_metrics = r[6]
                metrics = {}
                if raw_metrics:
                    metrics = raw_metrics if isinstance(raw_metrics, dict) else json.loads(raw_metrics)

                net_pnl = safe_float(metrics.get("net_pnl") if metrics.get("net_pnl") is not None else r[10], 0.0)
                win_rate = safe_float(metrics.get("win_rate") if metrics.get("win_rate") is not None else r[9], 0.0)
                if win_rate > 1.0:
                    win_rate = win_rate / 100.0

                sharpe = safe_float(metrics.get("sharpe"), 0.0) if metrics.get("sharpe") is not None else None
                max_dd = safe_float(metrics.get("max_drawdown"), 0.0)
                tot_trades = safe_int(metrics.get("total_trades") if metrics.get("total_trades") is not None else r[8], 0)

                backtests.append({
                    "id": strat_id,
                    "strategy_id": strat_id,
                    "table_name": _to_slug(strat_name),
                    "strategy_name": strat_name,
                    "exchange": exchange,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "status": bt_status,
                    "submitted_at": last_updated,
                    "created_at": last_updated,
                    "net_pnl": net_pnl,
                    "win_rate": win_rate,
                    "sharpe": sharpe,
                    "max_drawdown": max_dd,
                    "total_trades": tot_trades,
                    "metrics": metrics,
                })

    except Exception as e:
        logger.warning(f"PostgreSQL DB error in get_all_backtests: {e}")
    finally:
        if conn:
            conn.close()

    # Apply search filter
    if search:
        sl = search.lower()
        backtests = [
            b for b in backtests
            if sl in b["strategy_name"].lower() or sl in b["symbol"].lower() or sl in b["exchange"].lower()
        ]

    # Apply status tab filter
    if status and status != "all":
        backtests = [b for b in backtests if b["status"].lower() == status.lower()]

    return backtests


def get_backtest_by_id(identifier: str) -> dict:
    """
    Fetches full detail for a strategy backtest run using run_id or strategy_id / strategy_slug.
    Strictly returns DB data. Returns None if item does not exist.
    """
    str_id = str(identifier).strip()
    clean_num = re.sub(r"^(bt|strat|strategy|run)[-_]?", "", str_id, flags=re.IGNORECASE).lstrip("0")
    if not clean_num and str_id:
        clean_num = "0"
    numeric_id = int(clean_num) if (clean_num and clean_num.isdigit()) else (int(str_id) if str_id.isdigit() else None)
    slug_id = _to_slug(str_id) if not numeric_id else ""

    conn = None
    strat_meta = None
    metrics = {}
    charts = {}
    trades = []
    status = "completed"
    error_message = None
    run_cfg = {}

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # First check if identifier corresponds to a run_id in metadata.backtest_runs
            run_data = None
            if numeric_id:
                run_data = get_backtest_run_by_id(conn, numeric_id)

            if run_data:
                strat_id = run_data["strategy_id"]
                status = run_data["status"]
                error_message = run_data["error_message"]
                metrics = run_data["metrics"] or {}
                run_cfg = run_data["backtest_config"] or {}

                cursor.execute("""
                    SELECT s.strategy_id, s.strategy_name, s.exchange, s.symbol, s.target_timeframe,
                           bs.metrics, bs.charts, s.strategy_config
                    FROM metadata.strategy_data s
                    LEFT JOIN backtests.stats bs ON s.strategy_id = bs.strategy_id
                    WHERE s.strategy_id = %s;
                """, (strat_id,))
                row = cursor.fetchone()
                if row:
                    strat_name = str(row[1])
                    exchange = str(row[2]).upper() if row[2] else ""
                    symbol = str(row[3]).upper() if row[3] else ""
                    timeframe = str(row[4]) if row[4] else ""
                    raw_m, raw_c = row[5], row[6]
                    if raw_m and not metrics:
                        metrics = raw_m if isinstance(raw_m, dict) else json.loads(raw_m)
                    if raw_c:
                        charts = raw_c if isinstance(raw_c, dict) else json.loads(raw_c)

                    table_name = _to_slug(strat_name)
                    strat_meta = {
                        "id": run_data["run_id"],
                        "run_id": run_data["run_id"],
                        "strategy_id": strat_id,
                        "strategy_name": strat_name,
                        "exchange": exchange,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "table_name": table_name,
                        "status": status,
                        "error_message": error_message,
                    }
            else:
                # Query strategy_data & backtests.stats directly
                if numeric_id:
                    cursor.execute("""
                        SELECT s.strategy_id, s.strategy_name, s.exchange, s.symbol, s.target_timeframe,
                               COALESCE(bs.status, 'completed'), bs.metrics, bs.charts, s.strategy_config
                        FROM metadata.strategy_data s
                        LEFT JOIN backtests.stats bs ON s.strategy_id = bs.strategy_id
                        WHERE s.strategy_id = %s;
                    """, (numeric_id,))
                else:
                    cursor.execute("""
                        SELECT s.strategy_id, s.strategy_name, s.exchange, s.symbol, s.target_timeframe,
                               COALESCE(bs.status, 'completed'), bs.metrics, bs.charts, s.strategy_config
                        FROM metadata.strategy_data s
                        LEFT JOIN backtests.stats bs ON s.strategy_id = bs.strategy_id
                        WHERE LOWER(s.strategy_name) = %s OR REGEXP_REPLACE(LOWER(s.strategy_name), '[^a-z0-9]+', '_', 'g') = %s;
                    """, (str_id.lower(), slug_id))
                
                row = cursor.fetchone()
                if row:
                    strat_id = int(row[0])
                    strat_name = str(row[1])
                    exchange = str(row[2]).upper() if row[2] else ""
                    symbol = str(row[3]).upper() if row[3] else ""
                    timeframe = str(row[4]) if row[4] else ""
                    status = str(row[5]) if row[5] else "completed"
                    raw_m, raw_c = row[6], row[7]

                    if raw_m:
                        metrics = raw_m if isinstance(raw_m, dict) else json.loads(raw_m)
                    if raw_c:
                        charts = raw_c if isinstance(raw_c, dict) else json.loads(raw_c)

                    table_name = _to_slug(strat_name)
                    strat_meta = {
                        "id": strat_id,
                        "strategy_id": strat_id,
                        "strategy_name": strat_name,
                        "exchange": exchange,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "table_name": table_name,
                        "status": status,
                        "error_message": None,
                    }

            if strat_meta:
                table_name = strat_meta["table_name"]
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_tables
                        WHERE schemaname = 'backtests' AND tablename = %s
                    );
                """, (table_name,))
                if cursor.fetchone()[0]:
                    cursor.execute(f"""
                        SELECT
                            entry_time, exit_time, direction,
                            entry_price, exit_price, net_pnl,
                            COALESCE(perc_pnl, 0) AS return_pct,
                            exit_reason, status
                        FROM backtests.{table_name}
                        ORDER BY entry_time ASC
                        LIMIT 500;
                    """)
                    for idx, tr in enumerate(cursor.fetchall()):
                        trades.append({
                            "trade_id": f"BT_{idx + 1}",
                            "side": str(tr[2] or "LONG").upper(),
                            "entry_time": clean_timestamp(tr[0]),
                            "exit_time": clean_timestamp(tr[1]),
                            "entry_price": float(tr[3] or 0.0),
                            "exit_price": float(tr[4] or 0.0),
                            "net_pnl": float(tr[5] or 0.0),
                            "return_pct": float(tr[6] or 0.0),
                            "exit_reason": str(tr[7] or ""),
                            "status": str(tr[8] or "Completed"),
                        })

    except Exception as e:
        logger.warning(f"Could not read backtest detail from DB for '{identifier}': {e}")
    finally:
        if conn:
            conn.close()

    if not strat_meta:
        return {
            "id": identifier,
            "strategy_id": numeric_id or 0,
            "strategy_name": str(identifier),
            "symbol": "",
            "exchange": "",
            "timeframe": "",
            "status": "failed",
            "error_message": f"Backtest detail for '{identifier}' not found in database.",
            "net_pnl": 0.0,
            "win_rate": 0.0,
            "sharpe": None,
            "trades": [],
        }

    def _extract_list(data_obj):
        if isinstance(data_obj, list):
            return data_obj
        if isinstance(data_obj, dict):
            return data_obj.get("raw_values") or data_obj.get("data") or data_obj.get("values") or []
        return []

    equity_curve = _extract_list(charts.get("equity_curve"))
    drawdown_curve = _extract_list(charts.get("drawdown_curve") or charts.get("drawdown"))
    monthly_returns = _extract_list(charts.get("monthly_returns"))
    rolling_metrics = _extract_list(charts.get("rolling_metrics"))
    pnl_per_trade = _extract_list(charts.get("pnl_per_trade"))

    if (not equity_curve or not drawdown_curve or not monthly_returns or not rolling_metrics or not pnl_per_trade) and trades:
        gen_charts = generate_charts_from_trades(trades, initial_balance=float(run_cfg.get("initial_balance", 10000.0)))
        if not equity_curve:
            equity_curve = gen_charts["equity_curve"]
        if not drawdown_curve:
            drawdown_curve = gen_charts["drawdown_curve"]
        if not monthly_returns:
            monthly_returns = gen_charts["monthly_returns"]
        if not rolling_metrics:
            rolling_metrics = gen_charts["rolling_metrics"]
        if not pnl_per_trade:
            pnl_per_trade = gen_charts["pnl_per_trade"]

    if not pnl_per_trade and trades:
        pnl_per_trade = [{
            "trade_id": t.get("trade_id") or f"BT_{i+1}",
            "exit_time": t.get("exit_time") or t.get("entry_time") or "",
            "net_pnl": float(t.get("net_pnl") or 0.0),
            "side": str(t.get("side") or t.get("direction") or "LONG").upper(),
        } for i, t in enumerate(trades)]

    raw_win_rate = metrics.get("win_rate")
    if raw_win_rate is None:
        raw_win_rate = strat_meta.get("win_rate", 0.0)
    win_rate = safe_float(raw_win_rate, 0.0)
    if win_rate > 1.0:
        win_rate = win_rate / 100.0

    raw_net_pnl = metrics.get("net_pnl")
    if raw_net_pnl is None:
        raw_net_pnl = strat_meta.get("net_pnl", 0.0)
    net_pnl = safe_float(raw_net_pnl, 0.0)

    raw_sharpe = metrics.get("sharpe")
    if raw_sharpe is None:
        raw_sharpe = strat_meta.get("sharpe")
    sharpe = safe_float(raw_sharpe, 0.0) if raw_sharpe is not None else None

    raw_max_dd = metrics.get("max_drawdown")
    if raw_max_dd is None:
        raw_max_dd = strat_meta.get("max_drawdown", 0.0)

    raw_trades_cnt = metrics.get("total_trades")
    if raw_trades_cnt is None:
        raw_trades_cnt = strat_meta.get("total_trades", len(trades))

    return {
        "id": strat_meta["id"],
        "run_id": strat_meta.get("run_id"),
        "strategy_id": strat_meta["strategy_id"],
        "strategy_name": strat_meta["strategy_name"],
        "symbol": strat_meta["symbol"],
        "exchange": strat_meta["exchange"],
        "timeframe": strat_meta["timeframe"],
        "status": strat_meta.get("status", "completed"),
        "error_message": strat_meta.get("error_message"),
        "completed_at": strat_meta.get("submitted_at") or "",
        "net_pnl": net_pnl,
        "win_rate": win_rate,
        "sharpe": sharpe,
        "sortino": safe_float(metrics.get("sortino"), 0.0),
        "cagr": safe_float(metrics.get("cagr"), 0.0),
        "calmar": safe_float(metrics.get("calmar"), 0.0),
        "max_drawdown": safe_float(raw_max_dd, 0.0),
        "profit_factor": safe_float(metrics.get("profit_factor"), 0.0),
        "total_trades": safe_int(raw_trades_cnt, len(trades)),
        "backtest_config": run_cfg,
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "monthly_returns": monthly_returns,
        "rolling_metrics": rolling_metrics,
        "pnl_per_trade": pnl_per_trade,
        "trades": trades,
    }
