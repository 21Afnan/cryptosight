import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_score
import lightgbm as lgb
import xgboost as xgb
from cryptosight.utils.logger import get_logger

logger = get_logger("PPModels")


class ModelEvaluator:
    """
    Quantitative Model Training & Evaluation Suite.
    Trains identical models (`LinearRegression`, `LightGBM`, `XGBoost`) across all
    preprocessed feature sets under identical train/test conditions.
    Converts predictions directly into integer trading signals (`+1, 0, -1`).
    """

    def __init__(self, task: str = "regression", threshold: float = 0.002):
        self.task = str(task).lower()
        self.threshold = float(threshold)
        logger.info(f"Initialized ModelEvaluator | Task: [{self.task.upper()}] | Signal Threshold: {self.threshold}")

    def get_model(self, model_name: str):
        """
        Instantiates the required ML model based on `model_name` and `task`.
        """
        clean_name = str(model_name).lower().strip()

        if self.task == "regression":
            if clean_name in ["linear", "linear_regression"]:
                return LinearRegression()
            elif clean_name == "lightgbm":
                return lgb.LGBMRegressor(random_state=42, n_estimators=100, verbosity=-1)
            elif clean_name == "xgboost":
                return xgb.XGBRegressor(random_state=42, n_estimators=100, verbosity=0)
            else:
                logger.warning(f"Unknown regression model '{model_name}'. Defaulting to LinearRegression.")
                return LinearRegression()

        elif self.task == "classification":
            if clean_name == "lightgbm":
                return lgb.LGBMClassifier(random_state=42, n_estimators=100, verbosity=-1)
            elif clean_name == "xgboost":
                # XGBoost classifier requires classes to be 0, 1, 2 instead of -1, 0, 1
                return xgb.XGBClassifier(random_state=42, n_estimators=100, verbosity=0, eval_metric="mlogloss")
            elif clean_name in ["logistic", "logistic_regression"]:
                return LogisticRegression(max_iter=1000, random_state=42)
            else:
                logger.warning(f"Unknown classification model '{model_name}'. Defaulting to LightGBM.")
                return lgb.LGBMClassifier(random_state=42, n_estimators=100, verbosity=-1)

        raise ValueError(f"Unsupported task: '{self.task}'. Use 'regression' or 'classification'.")

    def train_and_predict(self, df: pd.DataFrame, model_name: str, test_size: float = 0.20) -> dict:
        """
        Trains model on the first (1 - test_size) rows and evaluates on the last `test_size` rows.
        Returns a dictionary containing evaluation metrics (`MAE/RMSE` or `Accuracy/Precision`)
        and a clean out-of-sample prediction DataFrame (`timestamp, target, predicted, signal`).
        """
        if df.empty or "target" not in df.columns:
            raise ValueError("Input DataFrame is empty or missing required 'target' column.")

        feature_cols = [
            col for col in df.columns
            if col not in ["timestamp", "target"] and pd.api.types.is_numeric_dtype(df[col])
        ]

        if not feature_cols:
            raise ValueError("No numeric feature columns found for model training.")

        # Temporal split (No data leakage)
        split_idx = int(len(df) * (1.0 - test_size))
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        # Sanitize any residual NaNs in X
        X_train = train_df[feature_cols].ffill().bfill().fillna(0.0).to_numpy(dtype=float)
        y_train = train_df["target"].to_numpy(dtype=float)

        X_test = test_df[feature_cols].ffill().bfill().fillna(0.0).to_numpy(dtype=float)
        y_test = test_df["target"].to_numpy(dtype=float)

        model = self.get_model(model_name)

        if self.task == "classification":
            # Map labels [-1, 0, 1] -> [0, 1, 2] for model fitting if required by XGBoost/LGBM
            y_train_mapped = (y_train + 1).astype(int)
            y_test_mapped = (y_test + 1).astype(int)

            model.fit(X_train, y_train_mapped)
            y_pred_mapped = model.predict(X_test)
            y_pred = y_pred_mapped - 1  # Map back to original [-1, 0, 1]

            metrics = {
                "accuracy": round(float(accuracy_score(y_test_mapped, y_pred_mapped)), 4),
                "precision": round(float(precision_score(y_test_mapped, y_pred_mapped, average="weighted", zero_division=0)), 4),
            }
            signals = y_pred.astype(int)

        else:
            # Regression training (predict continuous log return)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            metrics = {
                "mae": round(float(mean_absolute_error(y_test, y_pred)), 6),
                "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 6),
                "r2": round(float(r2_score(y_test, y_pred)), 4),
            }

            # Convert continuous return prediction into +1, 0, -1 trading signals using return threshold
            signals = np.where(y_pred > self.threshold, 1, np.where(y_pred < -self.threshold, -1, 0))

        # Create clean predictions DataFrame indexed by timestamp
        predictions_df = pd.DataFrame({
            "timestamp": test_df["timestamp"].values if "timestamp" in test_df.columns else test_df.index.values,
            "actual_target": y_test,
            "predicted": y_pred,
            "signal": signals.astype(int),
        })

        logger.info(f"Model [{model_name.upper()}] evaluated on {len(X_test)} out-of-sample bars | Metrics: {metrics}")

        return {
            "model_name": model_name,
            "task": self.task,
            "metrics": metrics,
            "predictions_df": predictions_df,
        }

    def benchmark_models(self, preprocessed_datasets: dict[str, pd.DataFrame], models_list: list[str]) -> pd.DataFrame:
        """
        Loops over a dictionary of preprocessed datasets (`{"robust": df_robust, ...}`)
        and trains every model in `models_list` (`["linear", "lightgbm", ...]\`) on each dataset.
        Returns a Master Comparative Leaderboard summary table.
        """
        leaderboard_rows = []

        for method_name, df in preprocessed_datasets.items():
            for model_name in models_list:
                try:
                    res = self.train_and_predict(df=df, model_name=model_name)
                    metrics = res["metrics"]
                    row = {
                        "preprocessing_method": method_name,
                        "model": model_name,
                    }
                    row.update(metrics)
                    leaderboard_rows.append(row)
                except Exception as e:
                    logger.error(f"Error evaluating model [{model_name}] on method [{method_name}]: {e}")

        summary_table = pd.DataFrame(leaderboard_rows)
        return summary_table
