
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, f1_score, log_loss
from cryptosight.utils.logger import get_logger
try:
    from cryptosight.preprocessing.preprocessor import DataPreprocessor
except ImportError:
    from preprocessor import DataPreprocessor

logger = get_logger("MLModels")


class CryptoMLClassifier:
    """
    Step 1: Modular Classification Engine (`XGBoost` & `LightGBM`).
    Evaluates how each quantitative preprocessing technique impacts model accuracy.
    """

    def __init__(self, config: dict):
        self.config = config
        # Load selected models dynamically from pp.config.yaml (`models:` list)
        self.models_list = [str(m).lower() for m in self.config.get("models")]
        self.random_state = 42
        self.model = None

        logger.info(f"Initialized CryptoMLClassifier | Models to Evaluate: {self.models_list}")

    def build_model_object(self, model_name: str):
        """
        Function 1: Returns scikit-learn compatible classifier object based on `model_name`.
        Locks `random_state` for 100% reproducibility across all preprocessing comparison tests.
        """
        model_name = str(model_name).lower()
        if model_name == "xgboost":
            return XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05,
                random_state=self.random_state,
                eval_metric="mlogloss",
            )
        elif model_name == "lightgbm":
            return LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05,
                random_state=self.random_state,
                verbose=-1,
            )
        else:
            logger.error(f"Unsupported model requested: {model_name}")
            return None

    def fit_and_evaluate(
        self,
        model,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        method_name: str,
    ) -> dict:
        """
        Function 2: Fits the classifier and computes classification metrics (Accuracy, F1, Log-Loss).
        """
        # 0. Map [-1, 0, 1] -> [0, 1, 2] for strict XGBoost / LightGBM compatibility
        y_train_fit = np.where(y_train == -1, 0, np.where(y_train == 0, 1, np.where(y_train == 1, 2, y_train)))
        y_test_fit = np.where(y_test == -1, 0, np.where(y_test == 0, 1, np.where(y_test == 1, 2, y_test)))

        # 1. Fit model strictly on Training Data (`No Look-Ahead bias`)
        model.fit(X_train, y_train_fit)

        # 2. Predict classes and probabilities on unseen Test Data
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)

        # 3. Calculate Institutional Metrics (`PDF Step 5/6`)
        acc = accuracy_score(y_test_fit, y_pred) * 100.0
        f1 = f1_score(y_test_fit, y_pred, average="weighted") * 100.0
        loss = log_loss(y_test_fit, y_prob)

        correct_count = int(np.sum(y_test_fit == y_pred))
        total_count = int(len(y_test_fit))
        wrong_count = total_count - correct_count

        metrics = {
            "method": method_name.upper(),
            "accuracy_pct": round(acc, 2),
            "correct_predictions": f"{correct_count} / {total_count}",
            "wrong_predictions": wrong_count,
            "f1_score_pct": round(f1, 2),
            "log_loss": round(loss, 4),
        }
        logger.info(
            f"Evaluated [{method_name.upper()}] | Acc: {metrics['accuracy_pct']}% ({correct_count}/{total_count}) | F1: {metrics['f1_score_pct']}% | Loss: {metrics['log_loss']}"
        )
        return metrics

    def run_preprocessing_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Function 3: Splits data chronologically (80/20), loops across selected models and all 
        preprocessing techniques dynamically from `config`, and returns a benchmark DataFrame table.
        """
        methods_list = self.config.get("methods_to_test")

        # 1. Institutional Time-Series Split (`80% Train / 20% Test`, No Shuffling!)
        split_idx = int(len(df) * 0.80)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        # Extract Targets
        y_train = train_df["target"].values
        y_test = test_df["target"].values

        results = []

        # 2. Loop across Models loaded dynamically from config (`self.models_list`)
        for model_name in self.models_list:
            logger.info(f"=== Starting Evaluation Loop for Model: [{model_name.upper()}] ===")

            # 3. Loop across Preprocessing Methods loaded from config
            for method in methods_list:
                pp_config = {
                    "method": method,
                    "parameters": self.config.get("parameters"),
                    "exclude_columns": self.config.get("exclude_columns"),
                }
                preprocessor = DataPreprocessor(pp_config)

                # Fit-transform strictly on Train data, and transform on Test data (`0% Leakage`)
                scaled_train = preprocessor.fit_transform(train_df.copy())
                scaled_test = preprocessor.transform(test_df.copy())

                # Drop non-feature columns (`target` and `timestamp`)
                X_train = scaled_train.drop(columns=["timestamp", "target"], errors="ignore")
                X_test = scaled_test.drop(columns=["timestamp", "target"], errors="ignore")

                # Build Model & Evaluate
                model_obj = self.build_model_object(model_name)
                if model_obj is not None:
                    metrics = self.fit_and_evaluate(model_obj, X_train, y_train, X_test, y_test, method)
                    metrics["model"] = model_name.upper()
                    results.append(metrics)

        # 4. Return Final Benchmark Table sorted by Accuracy
        benchmark_df = pd.DataFrame(results)
        if not benchmark_df.empty:
            benchmark_df = benchmark_df.sort_values(by="accuracy_pct", ascending=False).reset_index(drop=True)
        return benchmark_df



