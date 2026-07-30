"""
main.py — Master Execution Runner for Machine Learning Module.

1. Executes the ML training pipeline using settings from `ml_config.yaml`.
2. Reads backtest ledgers and passes timestamped return series to `cryptosight.stats`
   (`compute_all_metrics` & `generate_all_plots`) to calculate QuantStats trading metrics & interactive charts.
3. Ingests all ML configurations and model performance metrics into PostgreSQL:
   - `ml.configs`: ML Dataset & System Configurations
   - `ml.stats`: Per-Model Evaluation Metrics, QuantStats Trading Metrics & Plotly Charts
   - `ml_backtests.<model_id>`: Dedicated Schema for Trade-by-Trade ML Backtest Ledgers
"""
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import math

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import get_connection, insert_ml_backtest_ledger
from cryptosight.utils.metadata import create_ml_schema_and_tables
from cryptosight.ml.pipeline import QuantMLPipeline
from cryptosight.stats.metrices import compute_all_metrics
from cryptosight.stats.plots import generate_all_plots

logger = get_logger("MLMain")


def _sanitize_for_json(obj):
    """
    Recursively convert NumPy/pandas scalars, tuples, and Plotly Figures to standard JSON-serializable types.
    Handles tuples, sets, and Plotly Figure objects seamlessly.
    """
    if hasattr(obj, "to_plotly_json"):
        try:
            obj = obj.to_plotly_json()
        except Exception:
            pass
    elif hasattr(obj, "to_dict"):
        try:
            obj = obj.to_dict()
        except Exception:
            pass

    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(x) for x in obj]
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return _sanitize_for_json(obj.tolist())
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (str, bool)):
        return obj
    else:
        # Fallback to string representation if object is not recognized
        try:
            return str(obj)
        except Exception:
            return None


def get_ml_dataset(config_path: str | Path = None) -> dict:
    """
    Helper function to load the ML configuration, build the dataset features and target,
    and return a dictionary of raw/engineered datasets for the benchmark.
    """
    from cryptosight.utils.config import load_config
    from cryptosight.ml.preprocessing.features import MLFeatureBuilder
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "ml_config.yaml"
    config = load_config(config_path)
    builder = MLFeatureBuilder(config=config)
    return builder.build_dataset()


def ingest_ml_artifacts_to_db(conn, config_path: Path):
    """
    Ingests generated JSON artifact into PostgreSQL:
    `ml.configs`, `ml.stats`, and dedicated `ml_backtests.<model_id>` tables.
    """
    if not config_path.exists():
        logger.warning(f"Config artifact '{config_path}' does not exist; skipping DB ingestion.")
        return

    create_ml_schema_and_tables(conn)

    with open(config_path, "r", encoding="utf-8") as f:
        art = json.load(f)

    ds = art["1_dataset_info"]
    symbol = str(ds["symbol"]).upper()
    exchange = str(ds["exchange"]).lower()
    timeframe = str(ds["target_timeframe"])
    config_name = config_path.stem

    # Determine task_type dynamically from artifact
    if "3_classification_models" in art:
        task_type = "classification"
        models_block = art["3_classification_models"]
    else:
        task_type = "regression"
        models_block = art["3_regression_models"]

    # 1. Upsert into ml.configs
    upsert_cfg_sql = """
    INSERT INTO ml.configs (config_name, task_type, symbol, exchange, timeframe, config_json, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (config_name) DO UPDATE SET
        task_type   = EXCLUDED.task_type,
        symbol      = EXCLUDED.symbol,
        exchange    = EXCLUDED.exchange,
        timeframe   = EXCLUDED.timeframe,
        config_json = EXCLUDED.config_json,
        updated_at  = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_cfg_sql, (config_name, task_type, symbol, exchange, timeframe, json.dumps(art)))
            conn.commit()
            logger.info(f"Ingested ML config artifact '{config_name}' into 'ml.configs'.")
    except Exception as err:
        conn.rollback()
        logger.error(f"Failed to ingest config artifact into ml.configs: {err}")

    # 2. Upsert models into ml.stats
    leaderboard = models_block.get("leaderboard", [])
    backtest_csv_dir = Path(__file__).resolve().parent / "csv_files" / "backtesting"

    upsert_stats_sql = """
    INSERT INTO ml.stats (
        model_id, config_name, model_name, task_type, symbol, exchange, timeframe, status,
        primary_metric, score, win_rate, sharpe, max_drawdown, metrics, charts, updated_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (model_id) DO UPDATE SET
        config_name    = EXCLUDED.config_name,
        model_name     = EXCLUDED.model_name,
        task_type      = EXCLUDED.task_type,
        symbol         = EXCLUDED.symbol,
        exchange       = EXCLUDED.exchange,
        timeframe      = EXCLUDED.timeframe,
        status         = EXCLUDED.status,
        primary_metric = EXCLUDED.primary_metric,
        score          = EXCLUDED.score,
        win_rate       = EXCLUDED.win_rate,
        sharpe         = EXCLUDED.sharpe,
        max_drawdown   = EXCLUDED.max_drawdown,
        metrics        = EXCLUDED.metrics,
        charts         = EXCLUDED.charts,
        updated_at     = CURRENT_TIMESTAMP;
    """

    for idx, item in enumerate(leaderboard):
        raw_m_name = item["model"]
        model_type_name = str(raw_m_name).replace("_", " ").title()
        model_id = f"{symbol.lower()}_{timeframe}_{task_type}_{raw_m_name}".lower()
        model_name = f"{symbol}_{model_type_name}_{task_type.capitalize()}"

        # ----------------------------------------------------------------------
        # A. Extract ML Accuracy Metrics & Primary Score from Artifact
        # ----------------------------------------------------------------------
        if task_type == "classification":
            prec = float(str(item.get("val_precision", "0")).replace("%", "").strip()) / 100.0
            rec = float(str(item.get("val_recall", "0")).replace("%", "").strip()) / 100.0
            f1_val = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            primary_metric = "F1 Score"
            score = round(f1_val, 6)
        else:
            primary_metric = "RMSE"
            raw_score = item.get("val_rmse") or item.get("test_rmse") or item.get("val_loss") or item.get("score")
            score = float(raw_score) if raw_score is not None else 0.0

        ml_accuracy_metrics = {
            "train_accuracy": item.get("train_accuracy"),
            "val_accuracy": item.get("val_accuracy"),
            "val_precision": item.get("val_precision"),
            "val_recall": item.get("val_recall"),
            "val_f1_score": f"{round(score * 100.0, 2)}%" if task_type == "classification" else None,
            "val_loss": item.get("val_loss") or item.get("val_rmse"),
            "val_rmse": item.get("val_rmse"),
            "val_mae": item.get("val_mae"),
            "val_r2": item.get("val_r2"),
            "test_accuracy": item.get("test_accuracy"),
            "test_loss": item.get("test_loss") or item.get("test_rmse"),
            "test_rmse": item.get("test_rmse"),
            "test_mae": item.get("test_mae"),
            "test_r2": item.get("test_r2"),
            "train_metrics": {k: float(v) for k, v in item.items() if k.startswith("train_") and isinstance(v, (int, float))},
            "val_metrics": {k: float(v) for k, v in item.items() if k.startswith("val_") and isinstance(v, (int, float))},
            "test_metrics": {k: float(v) for k, v in item.items() if k.startswith("test_") and isinstance(v, (int, float))},
            "hyperparameters": item.get("hyperparameters", {}),
        }

        # ----------------------------------------------------------------------
        # B. Call `cryptosight.stats` Engine for Quant Trading Metrics & Charts
        # ----------------------------------------------------------------------
        qs_metrics = {}
        qs_charts = {}
        win_rate = 0.0
        sharpe = 0.0
        max_dd = 0.0
        ledger_df = pd.DataFrame()

        # Look for backtest ledger CSV
        ledger_filename = f"{exchange}_{symbol}_{timeframe}_{raw_m_name}_ledger.csv"
        ledger_path = backtest_csv_dir / ledger_filename

        if ledger_path.exists():
            try:
                ledger_df = pd.read_csv(ledger_path)
                if not ledger_df.empty and "perc_pnl" in ledger_df.columns:
                    if "exit_time" in ledger_df.columns:
                        clean_ledger = ledger_df.sort_values(by="exit_time")
                        clean_ledger["exit_time"] = pd.to_datetime(clean_ledger["exit_time"])
                        returns_series = clean_ledger.set_index("exit_time")["perc_pnl"]
                    else:
                        returns_series = ledger_df["perc_pnl"]

                    logger.info(f"Passing {len(returns_series)} trade returns of '{raw_m_name}' to cryptosight.stats module...")
                    qs_metrics = compute_all_metrics(returns_series, is_percentage=True)
                    
                    # Unpack generate_all_plots which returns (plots, master_json_data)
                    plots_tuple = generate_all_plots(returns_series, is_percentage=True)
                    if isinstance(plots_tuple, tuple) and len(plots_tuple) > 1:
                        qs_charts = plots_tuple[1]  # Use master_json_data (clean dicts)
                    else:
                        qs_charts = plots_tuple

                    # Explicitly enrich quant_stats with complete trade performance metrics
                    net_pnl = float(ledger_df["net_pnl"].sum()) if "net_pnl" in ledger_df.columns else 0.0
                    pos_pnl = float(ledger_df[ledger_df["net_pnl"] > 0]["net_pnl"].sum()) if "net_pnl" in ledger_df.columns else 0.0
                    neg_pnl = abs(float(ledger_df[ledger_df["net_pnl"] < 0]["net_pnl"].sum())) if "net_pnl" in ledger_df.columns else 0.0
                    profit_factor = (pos_pnl / neg_pnl) if neg_pnl > 0 else (pos_pnl if pos_pnl > 0 else 1.0)

                    qs_metrics.update({
                        "total_trades": len(ledger_df),
                        "acted_signals": len(ledger_df),
                        "net_pnl": net_pnl,
                        "profit_factor": profit_factor,
                    })

                    win_rate = float(qs_metrics.get("win_rate", 0.0) or 0.0) * 100.0
                    sharpe = float(qs_metrics.get("sharpe", 0.0) or 0.0)
                    if abs(sharpe) > 20.0 or math.isnan(sharpe) or math.isinf(sharpe):
                        sharpe = -5.0 if sharpe < 0 else 5.0
                    max_dd = float(qs_metrics.get("max_drawdown", 0.0) or 0.0)
            except Exception as err:
                logger.warning(f"QuantStats calculation skipped for '{raw_m_name}': {err}")

        # Fallback to artifact trading metrics if returns_series had 0 trades
        if not qs_metrics:
            tm = item.get("trading_metrics", {})
            win_rate = float(tm.get("win_rate", 0.0) or 0.0)
            if win_rate <= 1.0 and win_rate > 0:
                win_rate = win_rate * 100.0
            sharpe = float(tm.get("sharpe", 0.0) or 0.0)
            max_dd = float(tm.get("max_drawdown", 0.0) or 0.0)
            qs_metrics = tm

        # ----------------------------------------------------------------------
        # C. Assemble Consolidated `metrics` & `charts` JSON payloads
        # ----------------------------------------------------------------------
        metrics_payload = _sanitize_for_json({
            "ml_accuracy": ml_accuracy_metrics,
            "quant_stats": qs_metrics,
        })

        charts_payload = _sanitize_for_json({
            "feature_importance": ds.get("features_summary", {}).get("features_list", []),
            "confusion_matrix": item.get("confusion_matrix", []),
            "quant_charts": qs_charts,
        })

        metrics_json = json.dumps(metrics_payload)
        charts_json = json.dumps(charts_payload)

        try:
            with conn.cursor() as cursor:
                cursor.execute(upsert_stats_sql, (
                    model_id, config_name, model_name, task_type, symbol, exchange, timeframe, "trained",
                    primary_metric, score, win_rate, sharpe, max_dd, metrics_json, charts_json
                ))
                conn.commit()
                logger.info(f"Saved ML model stats for '{model_name}' (ID: {model_id}) into 'ml.stats'.")
        except Exception as err:
            conn.rollback()
            logger.error(f"Failed to save ML model stats for '{model_id}': {err}")

        # ----------------------------------------------------------------------
        # D. Ingest ML Trade Ledger into Dedicated Schema `ml_backtests.{model_id}`
        # ----------------------------------------------------------------------
        if not ledger_df.empty:
            try:
                insert_ml_backtest_ledger(conn, model_id, ledger_df)
            except Exception as err:
                logger.error(f"Failed to ingest backtest ledger into ml_backtests for '{model_id}': {err}")


def orchestrate_ml_pipeline(config_path: str | Path = None):
    """
    Main entry point for ML execution pipeline and DB ingestion using `ml_config.yaml`.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "ml_config.yaml"
    else:
        config_path = Path(config_path)

    logger.info(f"Initializing Cryptosight Machine Learning Module using '{config_path.name}'...")

    # 1. Run ML Pipeline
    pipeline = QuantMLPipeline(config_path=config_path)
    pipeline.run_pipeline()

    # 2. Ingest generated JSON artifacts into PostgreSQL metadata tables
    conn = get_connection()
    if conn:
        try:
            config_artifact_dir = Path(__file__).resolve().parent / "artifacts" / "configs"
            if config_artifact_dir.exists():
                for json_file in config_artifact_dir.glob("*.json"):
                    ingest_ml_artifacts_to_db(conn, json_file)
        finally:
            conn.close()

    logger.info("Machine Learning Pipeline & Ingestion Complete!")


if __name__ == "__main__":
    orchestrate_ml_pipeline()
