from pathlib import Path
import inspect
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb
import xgboost as xgb

from cryptosight.utils.config import get_ml_artifacts_dir, load_config
from cryptosight.utils.logger import get_logger
from cryptosight.ml.models.model_utills import train_model, save_model
from cryptosight.ml.evaluation.evaluator import evaluate_regression, create_leaderboard_entry

logger = get_logger("TrainRegressors")


class RegressorPipeline:
    """
    Standardized Regression Pipeline.
    """

    def __init__(self, config: dict):
        self.config = config
        self.exchange = str(config.get("data", {}).get("exchange")).lower().strip()
        self.tf = str(config.get("data", {}).get("target_timeframe")).lower().strip()
        self.symbols = [str(s).upper().strip() for s in self.config.get("data").get("symbols")]
        self.models_to_train = self.config.get("regression").get("models")
        self.fitted_models = {}

    def filter_params(self, model_class, params: dict) -> dict:
        """Filters `params` to only include keys accepted by `model_class.__init__`."""
        try:
            valid_keys = set(inspect.signature(model_class.__init__).parameters.keys()) - {"self"}
            filtered = {k: v for k, v in params.items() if k in valid_keys}
            skipped = set(params.keys()) - valid_keys
            if skipped:
                logger.warning(f"[{model_class.__name__}] Skipping unknown params: {skipped}")
            return filtered
        except Exception:
            return params

    def save_predictions(self, df: pd.DataFrame, predictions: np.ndarray, save_path: Path) -> pd.DataFrame:
        """Saves predictions alongside timestamps and actual targets to a CSV file."""
        pred_df = pd.DataFrame()
        if "timestamp" in df.columns:
            pred_df["timestamp"] = df["timestamp"].values
        elif isinstance(df.index, pd.DatetimeIndex) or df.index.name == "timestamp":
            pred_df["timestamp"] = df.index

        pred_df["target"] = df["target"].values if "target" in df.columns else np.nan
        pred_df["predicted_target"] = predictions

        save_path.parent.mkdir(parents=True, exist_ok=True)
        pred_df.to_csv(save_path, index=False, encoding="utf-8")
        return pred_df

    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[dict, dict]:
        """Trains regression models, evaluates them, and generates leaderboard."""
        if not self.models_to_train:
            logger.warning("No regression models configured in ml_config.yaml!")
            return {}, {}

        all_predictions = {}
        run_meta = {}

        for symbol in self.symbols:
            clean_sym = str(symbol).upper().strip()
            leaderboard = []

            feature_cols = [c for c in train_df.columns if c not in ["timestamp", "target"]]
            logger.info(f"Training regression models for {clean_sym} on {len(feature_cols)} features...")

            X_train, y_train = train_df[feature_cols].values, train_df["target"].values
            X_val, y_val     = val_df[feature_cols].values,   val_df["target"].values
            X_test, y_test   = test_df[feature_cols].values,  test_df["target"].values

            pred_csv_dir = Path(__file__).resolve().parent.parent.parent / "csv_files" / "regression" / "model_predicted"
            pred_csv_dir.mkdir(parents=True, exist_ok=True)

            model_dir = get_ml_artifacts_dir("model")

            for model_cfg in self.models_to_train:
                model_name = model_cfg.get("name")
                params     = model_cfg.get("parameters", {})

                logger.info(f"Fitting [{model_name}] (Train: {len(X_train)} samples)...")

                if model_name == "lstm_regressor":
                    from cryptosight.ml.models.regression.pytorch_lstm import train_pytorch_lstm_regressor
                    model_save_path = model_dir / f"{self.exchange}_{clean_sym}_{self.tf}_regression_{model_name}.pt"
                    metrics, preds, trained_params, model = train_pytorch_lstm_regressor(
                        X_train, y_train, X_val, y_val, X_test, y_test, params, model_save_path
                    )
                    self.fitted_models[model_name] = model

                else:
                    if model_name == "linear_regression":
                        raw_model = LinearRegression(**self.filter_params(LinearRegression, params))
                    elif model_name == "random_forest_regressor":
                        raw_model = RandomForestRegressor(**self.filter_params(RandomForestRegressor, params), random_state=42)
                    elif model_name == "xgboost_regressor":
                        raw_model = xgb.XGBRegressor(**self.filter_params(xgb.XGBRegressor, params), random_state=42)
                    elif model_name == "lightgbm_regressor":
                        raw_model = lgb.LGBMRegressor(**self.filter_params(lgb.LGBMRegressor, params), random_state=42)
                    else:
                        logger.warning(f"Unsupported regression model type: {model_name}. Skipping.")
                        continue

                    model = train_model(model_name, raw_model, X_train, y_train, task="regression")
                    self.fitted_models[model_name] = model

                    metrics, preds = evaluate_regression(model, X_train, y_train, X_val, y_val, X_test, y_test)
                    
                    model_save_path = model_dir / f"{self.exchange}_{clean_sym}_{self.tf}_regression_{model_name}.joblib"
                    save_model(model, str(model_save_path))

                    # Extract hyperparameters
                    trained_params = {}
                    try:
                        raw_params = model.get_params() if hasattr(model, "get_params") else {}
                        for k, v in raw_params.items():
                            if v is None or v is False or str(v) in ("None", "nan"):
                                continue
                            if isinstance(v, float) and (np.isnan(v) or v == 0.0):
                                continue
                            if isinstance(v, int) and v == 0:
                                continue
                            if isinstance(v, (str, int, float, bool)):
                                trained_params[str(k)] = round(v, 6) if isinstance(v, float) else v
                    except Exception:
                        pass

                logger.info(
                    f"[{model_name}] RMSE: {metrics['train_rmse']:.6f} / {metrics['val_rmse']:.6f} / {metrics['test_rmse']:.6f} | "
                    f"R2: {metrics['test_r2']:.4f}"
                )

                val_predictions  = preds["val_preds"]
                test_predictions = preds.get("test_preds", preds["val_preds"])

                pred_save_path = pred_csv_dir / f"{self.exchange}_{clean_sym}_{self.tf}_regression_{model_name}_predicted.csv"
                pred_df = self.save_predictions(val_df, val_predictions, pred_save_path)

                test_pred_save_path = pred_csv_dir / f"{self.exchange}_{clean_sym}_{self.tf}_regression_{model_name}_test_predicted.csv"
                test_pred_df = self.save_predictions(test_df, test_predictions, test_pred_save_path)

                all_predictions[model_name] = {
                    "val": pred_df,
                    "test": test_pred_df
                }

                entry = create_leaderboard_entry(
                    task="regression",
                    model_name=model_name,
                    metrics=metrics,
                    model_save_path=model_save_path,
                    pred_save_path=pred_save_path,
                    hyperparameters=trained_params
                )
                entry.pop("prediction_file", None)
                leaderboard.append(entry)

            leaderboard = sorted(leaderboard, key=lambda x: float(x.get("test_r2") or 0.0), reverse=True)

            models_dict = {}
            for entry in leaderboard:
                m = entry.get("model")
                models_dict[m] = {
                    "hyperparameters": entry.get("hyperparameters", {}),
                    "accuracy_metrics": {
                        "train_rmse":  entry.get("train_rmse"),
                        "train_mae":   entry.get("train_mae"),
                        "train_r2":    entry.get("train_r2"),
                        "train_total": entry.get("train_total"),
                        "val_rmse":    entry.get("val_rmse"),
                        "val_mae":     entry.get("val_mae"),
                        "val_r2":      entry.get("val_r2"),
                        "val_total":   entry.get("val_total"),
                        "test_rmse":   entry.get("test_rmse"),
                        "test_mae":    entry.get("test_mae"),
                        "test_r2":     entry.get("test_r2"),
                        "test_total":  entry.get("test_total"),
                    },
                    "artifacts": {
                        "model_file": entry.get("model_file")
                    }
                }

            run_meta[clean_sym] = {
                "leaderboard": leaderboard,
                "models": models_dict
            }
            logger.info(f"Regression training finished for {clean_sym} {self.tf}")

        return all_predictions, run_meta
