import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from cryptosight.utils.config import load_config, get_ml_artifacts_dir, save_config_artifact
from cryptosight.utils.logger import get_logger

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, log_loss
from sklearn.utils.class_weight import compute_sample_weight
import lightgbm as lgb
import xgboost as xgb

logger = get_logger("TrainClassifiers")


class ClassifierModel:
    """
    Flat wrapper that exposes the standard train(), predict(), 
    predict_proba(), save(), and load() interface for all models.
    Satisfies PDF requirement 6 without abstract classes or private functions.
    """
    def __init__(self, model_name: str, model_object):
        self.model_name = model_name
        self.model = model_object

    def train(self, X_train, y_train, **kwargs):
        # Automatically handles sample weights for XGBoost
        if self.model_name == "xgboost":
            sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)
            self.model.fit(X_train, y_train, sample_weight=sample_weights, **kwargs)
        else:
            self.model.fit(X_train, y_train, **kwargs)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)


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

                # Wrap raw model to satisfy Stage 6 required interface (train, predict, save, load)
                model = ClassifierModel(model_name, raw_model)
                model.train(X_train, y_train_mapped)

                # Store the fitted wrapper object
                self.fitted_models[model_name] = model

                # Predict and evaluate on Training Set
                train_preds = model.predict(X_train)
                train_acc = float(accuracy_score(y_train_mapped, train_preds))
                correct_train_count = int(np.sum(train_preds == y_train_mapped))
                total_train = len(y_train_mapped)

                # Predict and evaluate on Validation Set
                val_preds = model.predict(X_val)
                val_acc = float(accuracy_score(y_val_mapped, val_preds))
                val_prec = float(precision_score(y_val_mapped, val_preds, average="weighted", zero_division=0))
                val_rec = float(recall_score(y_val_mapped, val_preds, average="weighted", zero_division=0))
                correct_val_count = int(np.sum(val_preds == y_val_mapped))
                total_val = len(y_val_mapped)

                # Predict and evaluate on Test Set (Out-of-sample)
                test_preds = model.predict(X_test)
                test_acc = float(accuracy_score(y_test_mapped, test_preds))
                correct_test_count = int(np.sum(test_preds == y_test_mapped))
                total_test = len(y_test_mapped)

                # Calculate Loss (Log Loss / Cross-Entropy)
                try:
                    train_proba = model.predict_proba(X_train)
                    val_proba = model.predict_proba(X_val)
                    test_proba = model.predict_proba(X_test)

                    train_loss = float(log_loss(y_train_mapped, train_proba))
                    val_loss = float(log_loss(y_val_mapped, val_proba))
                    test_loss = float(log_loss(y_test_mapped, test_proba))
                except Exception:
                    # Fallback if probability prediction is not supported
                    train_loss, val_loss, test_loss = 0.0, 0.0, 0.0

                logger.info(
                    f"[{model_name}] Loss (Train/Val/Test): {train_loss:.4f} / {val_loss:.4f} / {test_loss:.4f}\n"
                    f"    - Train Acc: {train_acc * 100.0:.2f}% ({correct_train_count}/{total_train})\n"
                    f"    - Val   Acc: {val_acc * 100.0:.2f}% ({correct_val_count}/{total_val}) | Prec: {val_prec * 100.0:.2f}% | Rec: {val_rec * 100.0:.2f}%\n"
                    f"    - Test  Acc: {test_acc * 100.0:.2f}% ({correct_test_count}/{total_test})"
                )

                # Persist Model wrapper using standardized save method
                model_dir = get_ml_artifacts_dir("model")
                model_save_path = model_dir / f"{clean_sym}_{self.tf}_{model_name}.joblib"
                model.save(str(model_save_path))

                # Map predictions back to original trading targets [-1, 0, 1]
                val_predictions = val_preds - 1

                # Save predictions to CSV file under ml/csv_files for the signals module to use
                pred_csv_dir = Path(__file__).resolve().parent.parent.parent / "csv_files" / "classification" / "model_predicted"
                pred_csv_dir.mkdir(parents=True, exist_ok=True)
                pred_save_path = pred_csv_dir / f"{clean_sym}_{model_name}_predicted.csv"

                # Store predictions along with all input features and actual target
                pred_df = val_df.copy()
                pred_df["predicted"] = val_predictions
                pred_df.to_csv(pred_save_path, index=False, encoding="utf-8")

                # Store in returned dictionary
                all_predictions[model_name] = pred_df

                leaderboard.append({
                    "model": model_name,
                    "train_accuracy": f"{train_acc * 100.0:.2f}%",
                    "train_correct": correct_train_count,
                    "train_total": total_train,
                    "train_loss": round(train_loss, 4),
                    "val_accuracy": f"{val_acc * 100.0:.2f}%",
                    "val_precision": f"{val_prec * 100.0:.2f}%",
                    "val_recall": f"{val_rec * 100.0:.2f}%",
                    "val_correct": correct_val_count,
                    "val_total": total_val,
                    "val_loss": round(val_loss, 4),
                    "test_accuracy": f"{test_acc * 100.0:.2f}%",
                    "test_correct": correct_test_count,
                    "test_total": total_test,
                    "test_loss": round(test_loss, 4),
                    "model_file": str(model_save_path),
                    "prediction_file": str(pred_save_path)
                })

            # Save comparative leaderboard artifact
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
            logger.info("Saved classification run leaderboard to artifacts/configs/classification_run.yaml")

        return all_predictions


def get_signals(predictions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts and formats predictions into a clean DataFrame containing
    only ['timestamp', 'signal'] for backtesting and signal generation modules.
    """
    if "predicted" not in predictions_df.columns:
        raise ValueError("Input DataFrame does not contain a 'predicted' column.")

    signal_df = pd.DataFrame({
        "timestamp": predictions_df["timestamp"],
        "signal": predictions_df["predicted"].astype(int)
    })
    return signal_df

