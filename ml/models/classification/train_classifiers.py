import sys
from pathlib import Path
import numpy as np
import pandas as pd
from cryptosight.utils.config import load_config, get_ml_artifacts_dir, save_config_artifact
import json
from cryptosight.utils.logger import get_logger
from cryptosight.ml.models.model_utills import train_model, save_model
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from cryptosight.ml.evaluation.evaluator import evaluate_classification, create_leaderboard_entry
import lightgbm as lgb
import xgboost as xgb

logger = get_logger("TrainClassifiers")



class ClassifierPipeline:
    """
    State-of-the-Art Traditional Machine Learning Classifier Training Pipeline.
    Manages loading configurations, training classification models, handling class imbalances,
    evaluating out-of-sample metrics, persisting models, and extracting execution signals.
    """

    def __init__(self, config: dict):
        self.config = config
        self.symbols = config.get("data").get("symbols")
        self.tf = str(config.get("data").get("target_timeframe")).strip()
        self.models_to_train = config.get("classification").get("models")
        self.fitted_models = {}

    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        Trains all configured classification models on training data,
        evaluates validation/testing sets, saves models, and returns predictions.
        """
        if not self.models_to_train:
            logger.warning("No classification models configured in ml_config.yaml!")
            return {}

        all_predictions = {}

        for symbol in self.symbols:
            clean_sym = str(symbol).upper().strip()

            # Extract features and target values
            feature_cols = [c for c in train_df.columns if c not in ["timestamp", "target"]]
            logger.info(f"Training traditional classification models for {symbol} on {len(feature_cols)} features...")

            X_train = train_df[feature_cols].values
            y_train = train_df["target"].values

            X_val = val_df[feature_cols].values
            y_val = val_df["target"].values

            X_test = test_df[feature_cols].values
            y_test = test_df["target"].values

            # Map target labels [-1, 0, 1] -> [0, 1, 2] for model objective safety
            y_train_mapped = (y_train + 1).astype(int)
            y_val_mapped = (y_val + 1).astype(int)
            y_test_mapped = (y_test + 1).astype(int)

            leaderboard = []

            # Loop and train each configured model
            for model_cfg in self.models_to_train:
                model_name = model_cfg.get("name")
                params = model_cfg.get("parameters", {})

                logger.info(f"Fitting [{model_name}] classifier (Train: {len(X_train)} samples)...")

                # Instantiate raw model
                if model_name == "logistic_regression":
                    raw_model = LogisticRegression(**params, random_state=42)
                elif model_name == "decision_tree":
                    raw_model = DecisionTreeClassifier(**params, random_state=42)
                elif model_name == "random_forest":
                    raw_model = RandomForestClassifier(**params, random_state=42)
                elif model_name == "lightgbm":
                    raw_model = lgb.LGBMClassifier(**params, random_state=42)
                elif model_name == "xgboost":
                    raw_model = xgb.XGBClassifier(**params, random_state=42)
                elif model_name == "svm":
                    raw_model = SVC(**params, random_state=42)
                else:
                    logger.warning(f"Unsupported classification model type: {model_name}. Skipping.")
                    continue

                # Train the model using the generic functional utility
                model = train_model(model_name, raw_model, X_train, y_train_mapped, task="classification")

                # Store the fitted wrapper object
                self.fitted_models[model_name] = model

                # Evaluate Model using the external evaluator
                metrics, preds = evaluate_classification(
                    model, X_train, y_train_mapped, X_val, y_val_mapped, X_test, y_test_mapped
                )

                logger.info(
                    f"[{model_name}] Loss (Train/Val/Test): {metrics['train_loss']:.4f} / {metrics['val_loss']:.4f} / {metrics['test_loss']:.4f}\n"
                    f"    - Train Acc: {metrics['train_acc'] * 100.0:.2f}% ({metrics['correct_train_count']}/{metrics['total_train']})\n"
                    f"    - Val   Acc: {metrics['val_acc'] * 100.0:.2f}% ({metrics['correct_val_count']}/{metrics['total_val']}) | Prec: {metrics['val_prec'] * 100.0:.2f}% | Rec: {metrics['val_rec'] * 100.0:.2f}%\n"
                    f"    - Test  Acc: {metrics['test_acc'] * 100.0:.2f}% ({metrics['correct_test_count']}/{metrics['total_test']})"
                )

                # Persist Model using standardized save method
                model_dir = get_ml_artifacts_dir("model")
                model_save_path = model_dir / f"{clean_sym}_{self.tf}_{model_name}.joblib"
                save_model(model, str(model_save_path))

                # Map predictions back to original trading targets [-1, 0, 1]
                val_predictions = preds['val_preds'] - 1
                test_predictions = preds.get('test_preds', preds['val_preds']) - 1

                # Save predictions to CSV file under ml/csv_files/classification/model_predicted/
                pred_csv_dir = Path(__file__).resolve().parent.parent.parent / "csv_files" / "classification" / "model_predicted"
                pred_csv_dir.mkdir(parents=True, exist_ok=True)
                pred_save_path = pred_csv_dir / f"{clean_sym}_{model_name}_predicted.csv"

                # Store validation predictions along with input features, actual, and predicted targets
                pred_df = val_df.copy()
                pred_df["actual"] = val_df["target"]
                pred_df["predicted"] = val_predictions
                pred_df.to_csv(pred_save_path, index=False, encoding="utf-8")

                # Store testing dataset predictions along with actual vs predicted (specifically requested)
                test_pred_df = test_df.copy()
                test_pred_df["actual"] = test_df["target"]
                test_pred_df["predicted"] = test_predictions
                test_pred_save_path = pred_csv_dir / f"{clean_sym}_{model_name}_test_predicted.csv"
                test_pred_df.to_csv(test_pred_save_path, index=False, encoding="utf-8")

                # Store in returned dictionary (validation DataFrame with predicted column for backtesting)
                all_predictions[model_name] = pred_df

                entry = create_leaderboard_entry(
                    task="classification",
                    model_name=model_name,
                    metrics=metrics,
                    model_save_path=model_save_path,
                    pred_save_path=pred_save_path,
                    hyperparameters=params
                )
                leaderboard.append(entry)

            # Save leaderboard YAML — main.py reads this to inject trading metrics,
            # then writes the single authoritative quant_pipeline.json.
            leaderboard = sorted(leaderboard, key=lambda x: float(x["val_accuracy"].replace("%", "")), reverse=True)
            run_meta = {
                "symbol": symbol,
                "timeframe": self.tf,
                "features_count": len(feature_cols),
                "train_rows": len(train_df),
                "val_rows": len(val_df),
                "test_rows": len(test_df),
                "leaderboard": leaderboard
            }
            save_config_artifact(run_meta, "classification_run.yaml", asset_type="config")

            # ── DEDICATED MODEL METADATA JSON (separate from quant_pipeline.json) ──
            # Contains ONLY model-level information: hyperparameters + all metrics.
            # Named uniquely so multiple symbols/timeframes never collide.
            model_metadata = {
                "symbol": clean_sym,
                "timeframe": self.tf,
                "model_type": "classification",
                "models": {}
            }
            for entry in leaderboard:
                m = entry.get("model")
                model_metadata["models"][m] = {
                    "hyperparameters": entry.get("hyperparameters", {}),
                    "accuracy": {
                        "train_accuracy": entry.get("train_accuracy"),
                        "train_correct": entry.get("train_correct"),
                        "train_total": entry.get("train_total"),
                        "train_loss": entry.get("train_loss"),
                        "val_accuracy": entry.get("val_accuracy"),
                        "val_precision": entry.get("val_precision"),
                        "val_recall": entry.get("val_recall"),
                        "val_correct": entry.get("val_correct"),
                        "val_total": entry.get("val_total"),
                        "val_loss": entry.get("val_loss"),
                        "test_accuracy": entry.get("test_accuracy"),
                        "test_correct": entry.get("test_correct"),
                        "test_total": entry.get("test_total"),
                        "test_loss": entry.get("test_loss"),
                    },
                    "trading_metrics": entry.get("trading_metrics", {}),
                    "model_file": entry.get("model_file"),
                    "prediction_file": entry.get("prediction_file"),
                }

            metadata_json_path = get_ml_artifacts_dir("config") / f"{clean_sym}_{self.tf}_classification_metadata.json"
            try:
                with open(metadata_json_path, "w", encoding="utf-8") as mf:
                    json.dump(model_metadata, mf, indent=4, default=str)
                logger.info(f"Model metadata JSON saved -> {metadata_json_path}")
            except Exception as e_meta:
                logger.error(f"Could not write model metadata JSON: {e_meta}")

            logger.info(f"Saved classification leaderboard YAML for {clean_sym} {self.tf}")

        return all_predictions


def get_signals(predictions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts and formats predictions into a clean DataFrame containing
    only ['signal'] with a DatetimeIndex for the backtesting module.
    """
    if "predicted" not in predictions_df.columns:
        raise ValueError("Input DataFrame does not contain a 'predicted' column.")

    signal_df = pd.DataFrame({
        "timestamp": predictions_df["timestamp"],
        "signal": predictions_df["predicted"].astype(int)
    })
    
    # Backtester uses .join() and requires timestamp as index
    signal_df["timestamp"] = pd.to_datetime(signal_df["timestamp"], utc=True)
    signal_df.set_index("timestamp", inplace=True)
    
    return signal_df

