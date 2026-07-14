
import numpy as np
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from cryptosight.utils.logger import get_logger
try:
    from cryptosight.preprocessing.preprocessor import DataPreprocessor
except ImportError:
    from preprocessor import DataPreprocessor

logger = get_logger("MLModels")


class CryptoMLClassifier:
    """
    Step 1: Modular Machine Learning Evaluation Engine (`Regression` & `Classification`).
    Evaluates how each quantitative preprocessing technique impacts model accuracy, loss, and trading signals.
    Supports XGBoost, LightGBM, LinearRegression, Ridge, and RandomForest across regression/classification tasks.
    """

    def __init__(self, config: dict):
        self.config = config or {}
        # Load selected models dynamically from pp.config.yaml (`models:` list)
        raw_models = [str(m).lower().strip() for m in self.config.get("models", ["lightgbm", "xgboost"])]
        # Map canonical names so duplicates like 'xgboost' and 'xgbregressor' only evaluate once
        canonical_map = {"xgbregressor": "xgboost", "xgbclassifier": "xgboost", "lgbmregressor": "lightgbm", "lgbmclassifier": "lightgbm", "ols": "linear_regression"}
        self.models_list = list(dict.fromkeys([canonical_map.get(m, m) for m in raw_models]))
        self.model_task = str(self.config.get("model_task", "regression")).lower()
        self.regression_signal_threshold = float(self.config.get("regression_signal_threshold", 0.002))
        self.random_state = 42
        self.model = None

        logger.info(f"Initialized CryptoMLClassifier | Task: [{self.model_task.upper()}] | Models to Evaluate: {self.models_list}")

    def build_model_object(self, model_name: str):
        """
        Function 1: Returns scikit-learn compatible regressor or classifier object based on `model_name` and `model_task`.
        Locks `random_state` for 100% reproducibility across all preprocessing comparison tests.
        """
        model_name_clean = str(model_name).lower().strip()

        if self.model_task == "regression":
            if model_name_clean in ["xgboost", "xgbregressor"]:
                return XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.05,
                    random_state=self.random_state,
                )
            elif model_name_clean in ["lightgbm", "lgbmregressor"]:
                return LGBMRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.05,
                    random_state=self.random_state,
                    verbose=-1,
                )
            elif model_name_clean in ["linear_regression", "linearregression", "ols"]:
                return LinearRegression()
            elif model_name_clean in ["ridge"]:
                return Ridge(random_state=self.random_state)
            elif model_name_clean in ["random_forest", "randomforestregressor"]:
                return RandomForestRegressor(n_estimators=100, max_depth=5, random_state=self.random_state)
            else:
                if "xgb" in model_name_clean:
                    return XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=self.random_state)
                elif "lgbm" in model_name_clean or "lightgbm" in model_name_clean:
                    return LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=self.random_state, verbose=-1)
                logger.error(f"Unsupported regression model requested: {model_name}")
                return None
        else:
            # Classification
            if model_name_clean in ["xgboost", "xgbclassifier"]:
                return XGBClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.05,
                    random_state=self.random_state,
                    eval_metric="mlogloss",
                )
            elif model_name_clean in ["lightgbm", "lgbmclassifier"]:
                return LGBMClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.05,
                    random_state=self.random_state,
                    verbose=-1,
                )
            elif model_name_clean in ["logistic_regression", "logisticregression"]:
                return LogisticRegression(max_iter=1000, random_state=self.random_state)
            elif model_name_clean in ["random_forest", "randomforestclassifier"]:
                return RandomForestClassifier(n_estimators=100, max_depth=5, random_state=self.random_state)
            else:
                if "xgb" in model_name_clean:
                    return XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=self.random_state, eval_metric="mlogloss")
                elif "lgbm" in model_name_clean or "lightgbm" in model_name_clean:
                    return LGBMClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=self.random_state, verbose=-1)
                logger.error(f"Unsupported classification model requested: {model_name}")
                return None

    def fit_and_evaluate(
        self,
        model,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        method_name: str,
        scaled_test: pd.DataFrame = None,
    ) -> tuple[dict, pd.DataFrame]:
        """
        Function 2: Fits the regressor or classifier, computes evaluation metrics, and generates side-by-side
        trading signals (`+1 Buy, -1 Sell, 0 Hold`) and actual vs predicted evaluation DataFrame.
        """
        model_display_name = type(model).__name__.upper()

        if self.model_task == "regression":
            # 1. Fit regressor strictly on Training Data (`No Look-Ahead bias`)
            model.fit(X_train, y_train)

            # 2. Predict continuous return on unseen Test Data
            y_pred_cont = model.predict(X_test)

            # Convert continuous predictions to discrete +1/0/-1 signals using threshold
            y_pred_signal = np.where(y_pred_cont > self.regression_signal_threshold, 1,
                            np.where(y_pred_cont < -self.regression_signal_threshold, -1, 0))

            # Also convert y_test into actual signals if y_test is continuous return
            y_test_signal = np.where(y_test > self.regression_signal_threshold, 1,
                            np.where(y_test < -self.regression_signal_threshold, -1, 0))

            # Calculate Regression Metrics
            mae = mean_absolute_error(y_test, y_pred_cont)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_cont))
            try:
                r2 = r2_score(y_test, y_pred_cont)
            except Exception:
                r2 = 0.0

            # Directional / Signal accuracy & F1 score on generated signals
            acc = accuracy_score(y_test_signal, y_pred_signal) * 100.0
            prec = precision_score(y_test_signal, y_pred_signal, average="weighted", zero_division=0) * 100.0
            f1 = f1_score(y_test_signal, y_pred_signal, average="weighted", zero_division=0) * 100.0

            correct_count = int(np.sum(y_test_signal == y_pred_signal))
            total_count = int(len(y_test_signal))
            wrong_count = total_count - correct_count

            metrics = {
                "method": method_name.upper(),
                "model": model_display_name,
                "task": "REGRESSION",
                "accuracy_pct": round(acc, 2),
                "precision_pct": round(prec, 2),
                "f1_score_pct": round(f1, 2),
                "mae": round(float(mae), 6),
                "rmse": round(float(rmse), 6),
                "r2_score": round(float(r2), 4),
                "correct_predictions": f"{correct_count} / {total_count}",
                "wrong_predictions": wrong_count,
                "log_loss": "N/A",
            }
            logger.info(
                f"Evaluated [{method_name.upper()}] ({model_display_name}) | Dir.Acc: {metrics['accuracy_pct']}% | MAE: {metrics['mae']} | RMSE: {metrics['rmse']}"
            )

            prediction_df = scaled_test.copy() if scaled_test is not None else X_test.copy()
            if "timestamp" not in prediction_df.columns:
                if prediction_df.index.name == "timestamp" or isinstance(prediction_df.index, pd.DatetimeIndex):
                    prediction_df = prediction_df.reset_index()
                    if "index" in prediction_df.columns and "timestamp" not in prediction_df.columns:
                        prediction_df = prediction_df.rename(columns={"index": "timestamp"})

            prediction_df["actual_target"] = y_test
            prediction_df["predicted_target"] = np.round(y_pred_cont, 6)
            prediction_df["predicted_prob"] = 1.0
            prediction_df["is_correct"] = (y_test_signal == y_pred_signal)
            prediction_df["signal"] = y_pred_signal

            front_cols = [c for c in ["timestamp", "actual_target", "predicted_target", "is_correct", "predicted_prob", "signal", "open", "high", "low", "close", "volume"] if c in prediction_df.columns]
            other_cols = [c for c in prediction_df.columns if c not in front_cols and c != "target"]
            prediction_df = prediction_df[front_cols + other_cols]

            return metrics, prediction_df

        else:
            # 0. Map [-1, 0, 1] -> [0, 1, 2] for strict XGBoost / LightGBM compatibility
            unique_classes = np.unique(y_train)
            is_ternary = (-1 in unique_classes and 1 in unique_classes and 0 in unique_classes) or len(unique_classes) == 3

            if is_ternary:
                y_train_fit = np.where(y_train == -1, 0, np.where(y_train == 0, 1, np.where(y_train == 1, 2, y_train)))
                y_test_fit = np.where(y_test == -1, 0, np.where(y_test == 0, 1, np.where(y_test == 1, 2, y_test)))
            else:
                y_train_fit = np.where(y_train == -1, 0, y_train)
                y_test_fit = np.where(y_test == -1, 0, y_test)

            # 1. Fit model strictly on Training Data (`No Look-Ahead bias`)
            model.fit(X_train, y_train_fit)

            # 2. Predict classes and probabilities on unseen Test Data
            y_pred_fit = model.predict(X_test)
            if hasattr(model, "predict_proba"):
                y_prob_matrix = model.predict_proba(X_test)
                y_prob_max = np.max(y_prob_matrix, axis=1)
                try:
                    loss = log_loss(y_test_fit, y_prob_matrix)
                except Exception:
                    loss = 0.0
            else:
                y_prob_max = np.ones(len(X_test))
                loss = 0.0

            # Map predictions back to original domain (`actual_target vs predicted_target`)
            if is_ternary:
                y_pred = np.where(y_pred_fit == 0, -1, np.where(y_pred_fit == 1, 0, np.where(y_pred_fit == 2, 1, y_pred_fit)))
            else:
                y_pred = np.where(y_pred_fit == 0, -1, y_pred_fit)

            acc = accuracy_score(y_test_fit, y_pred_fit) * 100.0
            prec = precision_score(y_test_fit, y_pred_fit, average="weighted", zero_division=0) * 100.0
            f1 = f1_score(y_test_fit, y_pred_fit, average="weighted", zero_division=0) * 100.0

            correct_count = int(np.sum(y_test_fit == y_pred_fit))
            total_count = int(len(y_test_fit))
            wrong_count = total_count - correct_count

            metrics = {
                "method": method_name.upper(),
                "model": model_display_name,
                "task": "CLASSIFICATION",
                "accuracy_pct": round(acc, 2),
                "precision_pct": round(prec, 2),
                "f1_score_pct": round(f1, 2),
                "mae": "N/A",
                "rmse": "N/A",
                "r2_score": "N/A",
                "correct_predictions": f"{correct_count} / {total_count}",
                "wrong_predictions": wrong_count,
                "log_loss": round(loss, 4) if isinstance(loss, (int, float)) else "N/A",
            }
            logger.info(
                f"Evaluated [{method_name.upper()}] ({model_display_name}) | Acc: {metrics['accuracy_pct']}% ({correct_count}/{total_count}) | F1: {metrics['f1_score_pct']}% | Loss: {metrics['log_loss']}"
            )

            prediction_df = scaled_test.copy() if scaled_test is not None else X_test.copy()
            if "timestamp" not in prediction_df.columns:
                if prediction_df.index.name == "timestamp" or isinstance(prediction_df.index, pd.DatetimeIndex):
                    prediction_df = prediction_df.reset_index()
                    if "index" in prediction_df.columns and "timestamp" not in prediction_df.columns:
                        prediction_df = prediction_df.rename(columns={"index": "timestamp"})

            prediction_df["actual_target"] = y_test
            prediction_df["predicted_target"] = y_pred
            prediction_df["predicted_prob"] = np.round(y_prob_max, 4)
            prediction_df["is_correct"] = (prediction_df["actual_target"] == prediction_df["predicted_target"])
            prediction_df["signal"] = np.where(y_pred == 1, 1, np.where(y_pred == -1, -1, 0))

            front_cols = [c for c in ["timestamp", "actual_target", "predicted_target", "is_correct", "predicted_prob", "signal", "open", "high", "low", "close", "volume"] if c in prediction_df.columns]
            other_cols = [c for c in prediction_df.columns if c not in front_cols and c != "target"]
            prediction_df = prediction_df[front_cols + other_cols]

            return metrics, prediction_df

    def run_preprocessing_comparison(self, df: pd.DataFrame, symbol: str = "BTC") -> tuple[pd.DataFrame, dict, dict]:
        """
        Function 3: Splits data chronologically (80/20), loops across all preprocessing techniques,
        saves each preprocessed DataFrame to root `csv_files/` folder (excluding timestamp/target from transformation),
        and evaluates selected models to return a benchmark DataFrame table, full preprocessed splits, and model prediction evaluation splits.
        """
        methods_list = self.config.get("methods_to_test")
        if not methods_list:
            logger.error("No `methods_to_test` configured!")
            return pd.DataFrame(), {}, {}

        # 1. Institutional Time-Series Split (`80% Train / 20% Test`, No Shuffling!)
        split_idx = int(len(df) * 0.80)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        # Extract Targets
        y_train = train_df["target"].values
        y_test = test_df["target"].values

        # Pre-calculate scaled splits & store full preprocessed datasets for main.py to save
        preprocessed_splits = {}
        full_dfs = {}
        for method in methods_list:
            pp_config = {
                "method": method,
                "parameters": self.config.get("parameters", {}),
                "exclude_columns": self.config.get("exclude_columns", ["timestamp", "target"]),
            }
            preprocessor = DataPreprocessor(pp_config)
            scaled_train = preprocessor.fit_transform(train_df.copy())
            scaled_test = preprocessor.transform(test_df.copy())
            preprocessed_splits[method] = (scaled_train, scaled_test)

            # Reconstruct full dataset chronologically (`timestamp and target intact, features scaled/transformed`)
            full_preprocessed_df = pd.concat([scaled_train, scaled_test], axis=0)
            if "timestamp" not in full_preprocessed_df.columns:
                if full_preprocessed_df.index.name == "timestamp" or isinstance(full_preprocessed_df.index, pd.DatetimeIndex):
                    full_preprocessed_df = full_preprocessed_df.reset_index()
                    if "index" in full_preprocessed_df.columns and "timestamp" not in full_preprocessed_df.columns:
                        full_preprocessed_df = full_preprocessed_df.rename(columns={"index": "timestamp"})

            # Guarantee timestamp and target are clearly ordered right at the front
            front_cols = [c for c in ["timestamp", "target"] if c in full_preprocessed_df.columns]
            other_cols = [c for c in full_preprocessed_df.columns if c not in front_cols]
            full_preprocessed_df = full_preprocessed_df[front_cols + other_cols]
            full_dfs[method] = full_preprocessed_df

        results = []
        predictions_dfs = {}

        # 2. Loop across Models loaded dynamically from config (`self.models_list`)
        for model_name in self.models_list:
            logger.info(f"=== Starting Evaluation Loop for Model: [{model_name.upper()}] ===")

            # 3. Loop across Preprocessing Methods using pre-calculated zero-leakage splits
            for method in methods_list:
                scaled_train, scaled_test = preprocessed_splits[method]

                # Drop non-feature columns (`target` and `timestamp`)
                X_train = scaled_train.drop(columns=["timestamp", "target"], errors="ignore")
                X_test = scaled_test.drop(columns=["timestamp", "target"], errors="ignore")

                # Build Model & Evaluate
                model_obj = self.build_model_object(model_name)
                if model_obj is not None:
                    metrics, prediction_df = self.fit_and_evaluate(
                        model_obj, X_train, y_train, X_test, y_test, method, scaled_test=scaled_test
                    )
                    metrics["model"] = type(model_obj).__name__.upper()
                    results.append(metrics)
                    # Store rich predictions DataFrame (key by method name e.g. 'robust')
                    predictions_dfs[method] = prediction_df

        # 4. Return Final Benchmark Table sorted by Accuracy along with full preprocessed datasets & evaluation splits
        benchmark_df = pd.DataFrame(results)
        if not benchmark_df.empty:
            sort_col = "accuracy_pct" if "accuracy_pct" in benchmark_df.columns else benchmark_df.columns[0]
            benchmark_df = benchmark_df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
        return benchmark_df, full_dfs, predictions_dfs




