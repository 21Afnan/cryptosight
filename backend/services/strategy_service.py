"""
strategy_service.py
Service layer for Strategies page.
Queries strategy definitions from metadata.strategy_data joined with simulations.stats,
and trade ledgers from simulation_ledgers schema.
"""
import json
import pandas as pd
from cryptosight.utils.db import get_connection

def get_all_strategies():
    """
    Fetches all strategies registered in PostgreSQL metadata.strategy_data.
    Joins simulations.stats for simulation performance metrics (net_pnl, win_rate, total_trades, sharpe).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch global initial_balance from metadata.simulator_config
            cursor.execute("SELECT initial_balance FROM metadata.simulator_config LIMIT 1;")
            cfg_row = cursor.fetchone()
            global_init_bal = float(cfg_row[0]) if cfg_row and cfg_row[0] is not None else 0.0

            query = """
                SELECT 
                    s.strategy_id,
                    s.strategy_name,
                    s.exchange,
                    s.symbol,
                    s.target_timeframe,
                    COALESCE(sim.total_trades, 0) AS total_trades,
                    COALESCE(sim.win_rate, 0.0) AS win_rate,
                    COALESCE(sim.net_pnl, 0.0) AS net_pnl,
                    sim.final_balance AS final_balance,
                    sim.sharpe AS sharpe,
                    sim.charts AS charts
                FROM metadata.strategy_data s
                LEFT JOIN simulations.stats sim ON s.strategy_id = sim.strategy_id
                ORDER BY s.strategy_id ASC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            strategies = []
            for r in rows:
                net_pnl = float(r[7] or 0.0)
                final_bal = float(r[8]) if r[8] is not None else None
                init_bal = (final_bal - net_pnl) if (final_bal is not None) else global_init_bal
                calc_return = (net_pnl / init_bal) if init_bal else 0.0

                win_rate = float(r[6] or 0.0)
                if win_rate > 1.0:
                    win_rate = win_rate / 100.0

                raw_sharpe = r[9]
                sharpe_val = round(float(raw_sharpe), 2) if raw_sharpe is not None else None

                raw_charts = r[10]
                charts_val = None
                if raw_charts is not None:
                    if isinstance(raw_charts, (dict, list)):
                        charts_val = raw_charts
                    elif isinstance(raw_charts, str):
                        try:
                            charts_val = json.loads(raw_charts)
                        except Exception:
                            charts_val = None

                strategies.append({
                    "id": r[0],
                    "strategy_id": r[0],
                    "name": r[1],
                    "strategy_name": r[1],
                    "exchange": (r[2] or "").lower(),
                    "symbol": (r[3] or "").upper(),
                    "timeframe": r[4] or "",
                    "target_timeframe": r[4] or "",
                    "status": "active",
                    "total_trades": r[5],
                    "win_rate": win_rate,
                    "net_pnl": net_pnl,
                    "latest_return": round(calc_return, 4),
                    "sharpe": sharpe_val,
                    "charts": charts_val,
                })
            return strategies
    finally:
        conn.close()


def get_strategy_by_id(identifier):
    """
    Fetches detailed performance summary, configuration, and risk management parameters
    for a single strategy directly from PostgreSQL metadata.strategy_data, simulations.stats, and metadata.simulator_config.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch strategy metadata
            is_numeric = str(identifier).isdigit()
            if is_numeric:
                cursor.execute("""
                    SELECT strategy_id, strategy_name, exchange, symbol, target_timeframe, timeframe,
                           indicators_config, strategy_config, total_rows, long_signals, short_signals, last_signal_time
                    FROM metadata.strategy_data WHERE strategy_id = %s;
                """, (int(identifier),))
            else:
                cursor.execute("""
                    SELECT strategy_id, strategy_name, exchange, symbol, target_timeframe, timeframe,
                           indicators_config, strategy_config, total_rows, long_signals, short_signals, last_signal_time
                    FROM metadata.strategy_data WHERE LOWER(strategy_name) = LOWER(%s);
                """, (str(identifier),))

            s_row = cursor.fetchone()
            if not s_row:
                return None

            strat_id, strat_name, exch, sym, tgt_tf, base_tf, ind_cfg, strat_cfg, total_rows, long_sigs, short_sigs, last_sig = s_row

            # Parse strategy_config JSONB if present
            cfg_json = {}
            if strat_cfg:
                if isinstance(strat_cfg, dict):
                    cfg_json = strat_cfg
                elif isinstance(strat_cfg, str):
                    try:
                        cfg_json = json.loads(strat_cfg)
                    except Exception:
                        pass

            # 2. Fetch simulation performance stats dynamically as a dictionary
            cursor.execute("SELECT * FROM simulations.stats WHERE strategy_id = %s;", (strat_id,))
            sim_row = cursor.fetchone()
            sim_dict = {}
            if sim_row:
                colnames = [desc[0] for desc in cursor.description]
                sim_dict = dict(zip(colnames, sim_row))

            net_pnl = float(sim_dict.get("net_pnl") or 0.0)
            final_bal = float(sim_dict.get("final_balance")) if sim_dict.get("final_balance") is not None else None
            win_rate = float(sim_dict.get("win_rate") or 0.0)
            if win_rate > 1.0:
                win_rate = win_rate / 100.0

            total_trades = int(sim_dict.get("total_trades") or 0)
            sharpe = float(sim_dict.get("sharpe")) if sim_dict.get("sharpe") is not None else None
            sortino = float(sim_dict.get("sortino")) if sim_dict.get("sortino") is not None else None
            calmar = float(sim_dict.get("calmar")) if sim_dict.get("calmar") is not None else None
            max_dd = float(sim_dict.get("max_drawdown")) if sim_dict.get("max_drawdown") is not None else None
            cagr = float(sim_dict.get("cagr")) if sim_dict.get("cagr") is not None else None

            # 3. Fetch global risk management settings from metadata.simulator_config
            cursor.execute("""
                SELECT initial_balance, position_size_type, position_size_value, commission, slippage
                FROM metadata.simulator_config LIMIT 1;
            """)
            sim_cfg = cursor.fetchone()
            init_bal = float(sim_cfg[0]) if sim_cfg and sim_cfg[0] is not None else ((final_bal - net_pnl) if final_bal is not None else 0.0)
            pos_size = f"{sim_cfg[2]}%" if sim_cfg and sim_cfg[2] is not None else "—"
            comm = f"{sim_cfg[3]}" if sim_cfg and sim_cfg[3] is not None else "—"
            slip = f"{sim_cfg[4]}" if sim_cfg and sim_cfg[4] is not None else "—"

            tp = cfg_json.get("take_profit", "—")
            sl = cfg_json.get("stop_loss", "—")

            # 4. Fetch trade history to build equity curve and drawdown curve dynamically from initial_balance
            clean_name = strat_name.lower().replace(" ", "_").replace("-", "_")
            table_name = f"simulation_ledgers.{clean_name}"
            
            equity_curve = []
            drawdown_curve = []
            monthly_returns = []
            trade_distribution = []
            
            try:
                cursor.execute(f"""
                    SELECT exit_time, COALESCE(net_pnl, gross_pnl, 0) FROM {table_name} ORDER BY trade_id ASC;
                """)
                t_rows = cursor.fetchall()
                balance = init_bal
                peak = init_bal
                
                m_returns = {}
                pnl_counts = {"loss_large": 0, "loss_small": 0, "win_small": 0, "win_large": 0}
                
                for tr in t_rows:
                    pnl = float(tr[1] or 0)
                    balance += pnl
                    if balance > peak:
                        peak = balance
                    dd = (balance - peak) / peak if peak else 0.0
                    time_str = str(tr[0])[:10] if tr[0] else ""
                    
                    if tr[0]:
                        try:
                            m_key = pd.to_datetime(tr[0]).strftime("%b %y")
                            m_returns[m_key] = m_returns.get(m_key, 0.0) + pnl
                        except Exception:
                            pass
                    
                    if pnl < -50:
                        pnl_counts["loss_large"] += 1
                    elif pnl < 0:
                        pnl_counts["loss_small"] += 1
                    elif pnl < 50:
                        pnl_counts["win_small"] += 1
                    else:
                        pnl_counts["win_large"] += 1
                        
                    equity_curve.append({"time": time_str, "value": round(balance, 2)})
                    drawdown_curve.append({"time": time_str, "value": round(dd, 4)})

                for m, val in m_returns.items():
                    monthly_returns.append({"month": m, "value": round(val / init_bal, 4) if init_bal else 0.0})
                    
                trade_distribution = [
                    {"range": "< -$50", "count": pnl_counts["loss_large"], "positive": False},
                    {"range": "-$50 to $0", "count": pnl_counts["loss_small"], "positive": False},
                    {"range": "$0 to $50", "count": pnl_counts["win_small"], "positive": True},
                    {"range": "> $50", "count": pnl_counts["win_large"], "positive": True},
                ]
            except Exception:
                pass

            raw_charts = sim_dict.get("charts")
            charts_val = None
            if raw_charts is not None:
                if isinstance(raw_charts, (dict, list)):
                    charts_val = raw_charts
                elif isinstance(raw_charts, str):
                    try:
                        charts_val = json.loads(raw_charts)
                    except Exception:
                        charts_val = None

            return {
                "strategy_id": strat_id,
                "strategy_name": strat_name,
                "exchange": exch,
                "symbol": sym,
                "target_timeframe": tgt_tf,
                "status": "active",

                "performance": {
                    "net_pnl": net_pnl,
                    "win_rate": win_rate,
                    "sharpe": sharpe,
                    "sortino": sortino,
                    "calmar": calmar,
                    "max_drawdown": max_dd,
                    "cagr": cagr,
                    "total_trades": total_trades,
                },

                "configuration": {
                    "exchange": exch,
                    "symbol": sym,
                    "target_timeframe": tgt_tf,
                    "base_timeframe": base_tf or "—",
                    "long_signals": long_sigs or 0,
                    "short_signals": short_sigs or 0,
                    "total_rows": total_rows or 0,
                    "last_signal": str(last_sig) if last_sig else "—",
                },

                "risk_management": {
                    "take_profit": str(tp),
                    "stop_loss": str(sl),
                    "position_size": str(pos_size),
                    "commission": str(comm),
                    "slippage": str(slip),
                },

                "equity_curve": equity_curve,
                "drawdown_curve": drawdown_curve,
                "monthly_returns": monthly_returns,
                "trade_distribution": trade_distribution,
                "charts": charts_val,
            }
    finally:
        conn.close()


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


def get_strategy_ledgers(strategy_name: str):
    """
    Fetches trade ledgers for a given strategy from simulation_ledgers.<clean_strategy_name>.
    Supports both numeric strategy_id and strategy_name strings.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Resolve numeric strategy_id to real strategy_name if needed
            if str(strategy_name).isdigit():
                cursor.execute("SELECT strategy_name FROM metadata.strategy_data WHERE strategy_id = %s;", (int(strategy_name),))
                s_row = cursor.fetchone()
                if s_row and s_row[0]:
                    strategy_name = s_row[0]

            clean_name = str(strategy_name).lower().replace(" ", "_").replace("-", "_")
            table_name = f"simulation_ledgers.{clean_name}"

            # 2. Check if simulation_ledgers table exists for this strategy
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_tables 
                    WHERE schemaname = 'simulation_ledgers' AND tablename = %s
                );
            """, (clean_name,))
            exists = cursor.fetchone()[0]

            if not exists:
                return []

            cursor.execute(f"""
                SELECT trade_id, direction, entry_time, exit_time, 
                       entry_price, exit_price, quantity, gross_pnl, COALESCE(net_pnl, gross_pnl, 0) AS net_pnl
                FROM {table_name}
                ORDER BY trade_id ASC LIMIT 100;
            """)
            rows = cursor.fetchall()
            trades = []
            for r in rows:
                t_id = str(r[0])
                direction = (r[1] or "LONG").upper()
                entry_time = clean_timestamp(r[2])
                exit_time = clean_timestamp(r[3])
                entry_p = float(r[4] or 0)
                exit_p = float(r[5] or 0)
                qty = float(r[6] or 0)
                gross_pnl = float(r[7] or 0)
                net_pnl = float(r[8] or gross_pnl)

                ret_pct = ((exit_p - entry_p) / entry_p) if entry_p and direction == "LONG" else (-(exit_p - entry_p) / entry_p if entry_p else 0.0)

                trades.append({
                    "trade_id": t_id,
                    "order_id": t_id,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "direction": direction,
                    "side": direction,
                    "entry_price": entry_p,
                    "exit_price": exit_p,
                    "quantity": qty,
                    "gross_pnl": gross_pnl,
                    "net_pnl": net_pnl,
                    "return_pct": ret_pct,
                })
            return trades
    finally:
        conn.close()
