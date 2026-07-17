from pathlib import Path
import numpy as np
import pandas as pd
from cryptosight.utils.config import get_ml_artifacts_dir
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
        self.exchange = str(config.get("data").get("exchange")).lower().strip()
        self.models_to_train = config.get("classification").get("models")
        self.fitted_models = {}

    def save_predictions(self, df: pd.DataFrame, predictions: np.ndarray, save_path: Path) -> pd.DataFrame:
        """Helper to copy dataframe, set actual and predicted target columns, and save to CSV."""
        pred_df = df
        pred_df["actual"] = df["target"]
        pred_df["predicted"] = predictions
        save_path.parent.mkdir(parents=True, exist_ok=True)
        pred_df.to_csv(save_path, index=False, encoding="utf-8")
        return pred_df

    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict[str, dict]]:
        """
        Trains all configured classification models on training data,
        evaluates validation/testing sets, saves models, and returns predictions along with unified run metadata (dict keyed by symbol).
        """
        if not self.models_to_train:
            logger.warning("No classification models configured in ml_config.yaml!")
            return {}, {}

        all_predictions = {}
        run_meta = {}

        for symbol in self.symbols:
            clean_sym = str(symbol).upper().strip()
            all_predictions[clean_sym] = {}

            # Extract features and target values
            feature_cols = [c for c in train_df.columns if c not in ["timestamp", "target"]]
            logger.info(f"Training traditional classification models for {symbol} on {len(feature_cols)} features...")

            X_train = train_df[feature_cols]
            y_train = train_df["target"].values

            X_val = val_df[feature_cols]
            y_val = val_df["target"].values

            X_test = test_df[feature_cols]
            y_test = test_df["target"].values

            # Map target labels [-1, 0, 1] -> [0, 1, 2] for model objective safety
            y_train_mapped = (y_train + 1).astype(int)
            y_val_mapped = (y_val + 1).astype(int)
            y_test_mapped = (y_test + 1).astype(int)

            leaderboard = []

            # Create prediction CSV directory once per symbol
            pred_csv_dir = Path(__file__).resolve().parent.parent.parent / "csv_files" / "classification" / "model_predicted"
            pred_csv_dir.mkdir(parents=True, exist_ok=True)

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
                model_save_path = model_dir / f"{self.exchange}_{clean_sym}_{self.tf}_classification_{model_name}.joblib"
                save_model(model, str(model_save_path))

                # Map predictions back to original trading targets [-1, 0, 1]
                val_predictions = preds['val_preds'] - 1
                test_predictions = preds.get('test_preds', preds['val_preds']) - 1

                # Save validation and test predictions using our helper
                pred_save_path = pred_csv_dir / f"{self.exchange}_{clean_sym}_{self.tf}_classification_{model_name}_predicted.csv"
                pred_df = self.save_predictions(val_df, val_predictions, pred_save_path)

                test_pred_save_path = pred_csv_dir / f"{self.exchange}_{clean_sym}_{self.tf}_classification_{model_name}_test_predicted.csv"
                test_pred_df = self.save_predictions(test_df, test_predictions, test_pred_save_path)

                # Store in returned dictionary both val and test DataFrames
                all_predictions[clean_sym][model_name] = {
                    "val": pred_df,
                    "test": test_pred_df
                }

                # Extract hyperparameters directly from the model object, keeping only configured keys
                raw_params = model.get_params() if hasattr(model, "get_params") else {}
                trained_params = {k: v for k, v in raw_params.items() if k in params}

                entry = create_leaderboard_entry(
                    task="classification",
                    model_name=model_name,
                    metrics=metrics,
                    model_save_path=model_save_path,
                    pred_save_path=pred_save_path,
                    hyperparameters=trained_params,
                    trading_metrics={}
                )
                entry.pop("prediction_file", None)
                leaderboard.append(entry)

            # Build unified metadata dictionary in memory without creating extra files
            leaderboard = sorted(leaderboard, key=lambda x: float(str(x.get("val_accuracy", "0%")).replace("%", "")), reverse=True)
            
            models_dict = {}
            for entry in leaderboard:
                m = entry.get("model")
                models_dict[m] = {
                    "hyperparameters": entry.get("hyperparameters", {}),
                    "accuracy_metrics": {
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
                    "artifacts": {
                        "model_file": entry.get("model_file")
                    }
                }

            run_meta[clean_sym] = {
                "leaderboard": leaderboard,
                "models": models_dict
            }
            logger.info(f"Classification training finished for {clean_sym} {self.tf}")

        return all_predictions, run_meta


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
