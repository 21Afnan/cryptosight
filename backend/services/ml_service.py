"""
Machine Learning Service Layer for CryptoSight API.
Interacts with PostgreSQL `ml.stats`, `ml.configs`, and `ml_backtests.<model_id>` tables.
"""

from typing import Dict, Any, List, Optional
import json
from cryptosight.utils.db import get_connection
from cryptosight.utils.logger import get_logger

logger = get_logger("MLService")


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


def get_all_ml_models(
    task_type: Optional[str] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """
    1. Fetches all trained ML models from `ml.stats` joined with `ml.configs`.
    Returns executive KPIs and the catalog models array for `/ml` catalog page.
    """
    conn = get_connection()
    if not conn:
        logger.error("Failed to connect to PostgreSQL database.")
        return {"kpis": {}, "models": []}

    models: List[Dict[str, Any]] = []

    query = """
    SELECT 
        s.model_id,
        s.config_name,
        s.model_name,
        s.task_type,
        s.symbol,
        s.exchange,
        s.timeframe,
        s.status,
        s.primary_metric,
        s.score,
        s.win_rate,
        s.sharpe,
        s.max_drawdown,
        s.metrics,
        s.charts,
        s.updated_at,
        c.config_json
    FROM ml.stats s
    LEFT JOIN ml.configs c ON s.config_name = c.config_name
    WHERE 1=1
    """
    params = []
    if task_type and task_type.strip().lower() not in ("all", ""):
        query += " AND LOWER(s.task_type) = %s"
        params.append(task_type.strip().lower())
    if symbol and symbol.strip().lower() not in ("all", ""):
        query += " AND UPPER(s.symbol) = %s"
        params.append(symbol.strip().upper())

    query += " ORDER BY s.score DESC, s.updated_at DESC;"

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]

            for row in rows:
                record = dict(zip(col_names, row))
                
                metrics = record.get("metrics") or {}
                if isinstance(metrics, str):
                    try:
                        metrics = json.loads(metrics)
                    except Exception:
                        metrics = {}

                charts = record.get("charts") or {}
                if isinstance(charts, str):
                    try:
                        charts = json.loads(charts)
                    except Exception:
                        charts = {}

                config_json = record.get("config_json") or {}
                if isinstance(config_json, str):
                    try:
                        config_json = json.loads(config_json)
                    except Exception:
                        config_json = {}

                raw_sharpe = float(record["sharpe"]) if record["sharpe"] is not None else 0.0
                if abs(raw_sharpe) > 20.0:
                    raw_sharpe = -5.0 if raw_sharpe < 0 else 5.0

                is_reg = record["task_type"] == "regression"
                p_metric = "R2 Score" if is_reg else record["primary_metric"]
                
                val_r2 = metrics.get("ml_accuracy", {}).get("val_r2")
                if is_reg and val_r2 is not None:
                    score_val = float(val_r2)
                else:
                    score_val = float(record["score"]) if record["score"] is not None else 0.0

                models.append({
                    "model_id": record["model_id"],
                    "config_name": record["config_name"],
                    "name": record["model_name"],
                    "type": record["task_type"],
                    "symbol": record["symbol"],
                    "exchange": record["exchange"],
                    "timeframe": record["timeframe"],
                    "status": record["status"] or "trained",
                    "primary_metric": p_metric,
                    "score": score_val,
                    "win_rate": float(record["win_rate"]) if record["win_rate"] is not None else 0.0,
                    "sharpe": raw_sharpe,
                    "max_drawdown": float(record["max_drawdown"]) if record["max_drawdown"] is not None else 0.0,
                    "updated_at": record["updated_at"].isoformat() if record.get("updated_at") else None,
                    "dataset_info": config_json.get("1_dataset_info", {}),
                    "training_info": config_json.get("2_preprocessing_info", {}),
                    "metrics": metrics,
                    "charts": charts,
                })

    except Exception as err:
        logger.error(f"Error querying ml.stats models: {err}")
    finally:
        conn.close()

    total_models = len(models)
    classification_count = sum(1 for m in models if m["type"].lower() == "classification")
    regression_count = sum(1 for m in models if m["type"].lower() == "regression")
    top_performer = models[0]["name"] if models else "N/A"

    kpis = {
        "total_models": total_models,
        "classification_models": classification_count,
        "regression_models": regression_count,
        "top_performer": top_performer,
    }

    return {
        "kpis": kpis,
        "models": models,
    }


def get_ml_model_by_id(model_id: str) -> Optional[Dict[str, Any]]:
    """
    2. Fetches complete deep details for a single model by its `model_id`.
    Reads `ml.stats`, `ml.configs`, and recent trades from `ml_backtests.<model_id>`.
    """
    conn = get_connection()
    if not conn:
        logger.error("Failed to connect to PostgreSQL database.")
        return None

    clean_model_id = str(model_id).lower().strip()

    query = """
    SELECT 
        s.model_id,
        s.config_name,
        s.model_name,
        s.task_type,
        s.symbol,
        s.exchange,
        s.timeframe,
        s.status,
        s.primary_metric,
        s.score,
        s.win_rate,
        s.sharpe,
        s.max_drawdown,
        s.metrics,
        s.charts,
        s.updated_at,
        c.config_json
    FROM ml.stats s
    LEFT JOIN ml.configs c ON s.config_name = c.config_name
    WHERE LOWER(s.model_id) = %s;
    """

    model_detail = None

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (clean_model_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"No ML model found with model_id '{clean_model_id}'.")
                return None

            col_names = [desc[0] for desc in cursor.description]
            record = dict(zip(col_names, row))

            metrics = record.get("metrics") or {}
            if isinstance(metrics, str):
                try:
                    metrics = json.loads(metrics)
                except Exception:
                    metrics = {}

            charts = record.get("charts") or {}
            if isinstance(charts, str):
                try:
                    charts = json.loads(charts)
                except Exception:
                    charts = {}

            config_json = record.get("config_json") or {}
            if isinstance(config_json, str):
                try:
                    config_json = json.loads(config_json)
                except Exception:
                    config_json = {}

            # Fetch recent trade ledger rows from dedicated table `ml_backtests.<model_id>`
            ledger_table = f"ml_backtests.{clean_model_id.replace('-', '_')}"
            recent_trades: List[Dict[str, Any]] = []

            try:
                ledger_query = f"""
                SELECT entry_time, direction, signal, entry_price, quantity, exit_price, exit_time, exit_reason, status, net_pnl, perc_pnl
                FROM {ledger_table}
                ORDER BY entry_time DESC
                LIMIT 50;
                """
                cursor.execute(ledger_query)
                trade_rows = cursor.fetchall()
                t_cols = [d[0] for d in cursor.description]
                for tr in trade_rows:
                    t_rec = dict(zip(t_cols, tr))
                    if t_rec.get("entry_time"):
                        t_rec["entry_time"] = clean_timestamp(t_rec["entry_time"])
                    if t_rec.get("exit_time"):
                        t_rec["exit_time"] = clean_timestamp(t_rec["exit_time"])
                    recent_trades.append(t_rec)
            except Exception as leg_err:
                logger.info(f"Note: Could not query backtest ledger table '{ledger_table}': {leg_err}")

            # Extract directly from ml.configs.config_json without hardcoded fallbacks
            ds_info = config_json.get("1_dataset_info", {})
            prep_info = config_json.get("2_preprocessing_info", {})
            splits = prep_info.get("splitting_ratios", {})
            c_splits = prep_info.get("chronological_splits", {})

            start_date = ds_info.get("start_date", "")
            end_date = ds_info.get("end_date", "")
            exch = (ds_info.get("exchange") or record.get("exchange") or "").upper()
            sym = (ds_info.get("symbol") or record.get("symbol") or "").upper()
            tf = ds_info.get("target_timeframe") or record.get("timeframe") or ""

            dataset_info = {
                "dataset": f"{exch} {sym} {tf} {start_date} to {end_date}".strip(),
                "date_range": f"{start_date} → {end_date}".strip(" →"),
                "total_samples": ds_info.get("total_dataset_rows"),
                "features": ds_info.get("features_generated_count"),
                "target": "Direction (Long/Short/Hold)" if record["task_type"] == "classification" else "Target Return",
                "train_split": splits.get("train"),
                "val_split": splits.get("val"),
                "test_split": splits.get("test"),
                "train_samples": c_splits.get("train", {}).get("rows"),
                "val_samples": c_splits.get("validation", {}).get("rows"),
                "test_samples": c_splits.get("test", {}).get("rows"),
            }

            training_info = {
                "algorithm": record["model_name"],
            }

            quant_stats = metrics.get("quant_stats", {})
            evaluation_metrics = metrics.get("ml_accuracy", {})

            model_detail = {
                "id": record["model_id"],
                "model_id": record["model_id"],
                "name": record["model_name"],
                "type": record["task_type"],
                "symbol": record["symbol"],
                "exchange": record["exchange"],
                "timeframe": record["timeframe"],
                "status": record["status"] or "trained",
                "primary_metric": record["primary_metric"],
                "score": float(record["score"]) if record["score"] is not None else 0.0,
                "dataset_info": dataset_info,
                "training_info": training_info,
                "hyperparameters": evaluation_metrics.get("hyperparameters", {}),
                "evaluation_metrics": evaluation_metrics,
                "backtest_metrics": quant_stats,
                "backtest_ledger": recent_trades,
                "feature_importance": charts.get("feature_importance", []),
                "confusion_matrix": charts.get("confusion_matrix", []),
                "quant_charts": charts.get("quant_charts", {}),
            }

    except Exception as err:
        logger.error(f"Error fetching model details for '{clean_model_id}': {err}")
    finally:
        conn.close()

    return model_detail


def get_ml_model_ledger(
    model_id: str,
    limit: int = 1000,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    3. Server-side paginated trade ledger endpoint for `ml_backtests.<model_id>`.
    """
    conn = get_connection()
    if not conn:
        logger.error("Failed to connect to PostgreSQL database.")
        return {"total_trades": 0, "trades": []}

    clean_table_name = str(model_id).lower().strip().replace("-", "_").replace(" ", "_")
    ledger_table = f"ml_backtests.{clean_table_name}"

    trades: List[Dict[str, Any]] = []
    total_trades = 0

    try:
        with conn.cursor() as cursor:
            # Count total trades
            count_query = f"SELECT COUNT(*) FROM {ledger_table};"
            cursor.execute(count_query)
            total_trades = cursor.fetchone()[0]

            # Fetch paginated trades
            fetch_query = f"""
            SELECT entry_time, direction, signal, entry_price, quantity, take_profit, stop_loss, exit_price, exit_time, exit_reason, status, net_pnl, perc_pnl, cumulative_pnl, balance
            FROM {ledger_table}
            ORDER BY entry_time DESC
            LIMIT %s OFFSET %s;
            """
            cursor.execute(fetch_query, (limit, offset))
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]

            for r in rows:
                t = dict(zip(col_names, r))
                if t.get("entry_time"):
                    t["entry_time"] = clean_timestamp(t["entry_time"])
                if t.get("exit_time"):
                    t["exit_time"] = clean_timestamp(t["exit_time"])
                trades.append(t)

    except Exception as err:
        logger.warning(f"Error querying ledger table '{ledger_table}': {err}")
    finally:
        conn.close()

    return {
        "total_trades": total_trades,
        "trades": trades,
        "limit": limit,
        "offset": offset,
    }
