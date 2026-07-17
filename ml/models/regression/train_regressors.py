from pathlib import Path
import inspect
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb
import xgboost as xgb

from cryptosight.utils.config import get_ml_artifacts_dir
from cryptosight.utils.logger import get_logger
from cryptosight.ml.models.model_utills import train_model, save_model
from cryptosight.ml.evaluation.evaluator import evaluate_regression, create_leaderboard_entry

logger = get_logger("TrainRegressors")

# Supported model name → class mapping
SKLEARN_REGRESSORS = {
    "linear_regression":        LinearRegression,
    "random_forest_regressor":  RandomForestRegressor,
    "xgboost_regressor":        xgb.XGBRegressor,
    "lightgbm_regressor":       lgb.LGBMRegressor,
}


class RegressorPipeline:
    """Trains, evaluates, and persists regression models from ml_config.yaml."""

    def __init__(self, config: dict):
        data_cfg             = config.get("data", {})
        self.config          = config
        self.exchange        = str(data_cfg.get("exchange")).lower().strip()
        self.tf              = str(data_cfg.get("target_timeframe")).lower().strip()
        self.symbols         = [str(s).upper().strip() for s in data_cfg.get("symbols", [])]
        self.models_to_train = config.get("regression", {}).get("models", [])
        self.fitted_models   = {}

    def filter_params(self, model_class, params: dict) -> dict:
        """Returns only the params accepted by model_class.__init__."""
        try:
            valid = set(inspect.signature(model_class.__init__).parameters) - {"self"}
            skipped = set(params) - valid
            if skipped:
                logger.warning(f"[{model_class.__name__}] Skipping unknown params: {skipped}")
            return {k: v for k, v in params.items() if k in valid}
        except Exception:
            return params



    def save_predictions(self, df: pd.DataFrame, predictions: np.ndarray, save_path: Path) -> pd.DataFrame:
        """Saves timestamp + target + predicted_target to CSV. Returns the DataFrame."""
        pred_df = pd.DataFrame()
        if "timestamp" in df.columns:
            pred_df["timestamp"] = df["timestamp"].values
        elif isinstance(df.index, pd.DatetimeIndex) or df.index.name == "timestamp":
            pred_df["timestamp"] = df.index

        pred_df["target"] = df["target"].values if "target" in df.columns else np.nan

        # Pad with NaN if predictions are shorter (e.g. LSTM sliding window)
        diff = len(df) - len(predictions)
        pred_df["predicted_target"] = (
            np.pad(predictions, (diff, 0), constant_values=np.nan) if diff > 0 else predictions
        )
        pred_df = pred_df.dropna(subset=["predicted_target"])
        save_path.parent.mkdir(parents=True, exist_ok=True)
        pred_df.to_csv(save_path, index=False, encoding="utf-8")
        return pred_df

    def build_model(self, model_name: str, params: dict):
        """Instantiates the correct model class from SKLEARN_REGRESSORS."""
        if model_name not in SKLEARN_REGRESSORS:
            raise ValueError(f"Unsupported model: {model_name}")
        cls = SKLEARN_REGRESSORS[model_name]
        # Tree-based models need random_state; LinearRegression does not
        kw = self.filter_params(cls, params)
        if "random_state" in inspect.signature(cls.__init__).parameters:
            kw.setdefault("random_state", 42)
        return cls(**kw)

    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame,
              test_df: pd.DataFrame) -> tuple[dict, dict]:
        """
        Trains all configured regression models, evaluates them, and returns:
          all_predictions : {sym: {model_name: {"val": df, "test": df}}}
          run_meta        : {sym: {"leaderboard": [...], "models": {...}}}
        """
        if not self.models_to_train:
            logger.warning("No regression models configured in ml_config.yaml!")
            return {}, {}

        feature_cols = [c for c in train_df.columns if c not in ["timestamp", "target"]]
        X_train, y_train = train_df[feature_cols], train_df["target"].values
        X_val,   y_val   = val_df[feature_cols],   val_df["target"].values
        X_test,  y_test  = test_df[feature_cols],  test_df["target"].values

        model_dir    = get_ml_artifacts_dir("model")
        all_predictions = {}
        run_meta        = {}

        for clean_sym in self.symbols:
            all_predictions[clean_sym] = {}
            leaderboard = []
            pred_dir = (Path(__file__).resolve().parent.parent.parent
                        / "csv_files" / "regression" / "model_predicted")
            pred_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Training regression models for {clean_sym} on {len(feature_cols)} features...")

            for model_cfg in self.models_to_train:
                model_name = model_cfg.get("name")
                params     = model_cfg.get("parameters", {})
                logger.info(f"Fitting [{model_name}] (Train: {len(X_train)} samples)...")

                try:
                    # ── LSTM (PyTorch) ────────────────────────────────────────
                    if model_name == "lstm_regressor":
                        from cryptosight.ml.models.regression.pytorch_lstm import train_pytorch_lstm_regressor
                        save_path = model_dir / f"{self.exchange}_{clean_sym}_{self.tf}_regression_{model_name}.pt"
                        metrics, preds, trained_params, model = train_pytorch_lstm_regressor(
                            X_train, y_train, X_val, y_val, X_test, y_test, params, save_path
                        )
                        self.fitted_models[model_name] = model

                    # ── Scikit-learn / LightGBM / XGBoost ───────────────────
                    else:
                        raw_model = self.build_model(model_name, params)
                        model     = train_model(model_name, raw_model, X_train, y_train, task="regression")
                        self.fitted_models[model_name] = model

                        metrics, preds  = evaluate_regression(model, X_train, y_train, X_val, y_val, X_test, y_test)
                        # Extract hyperparameters directly from the model object, keeping only configured keys
                        raw_params = model.get_params() if hasattr(model, "get_params") else {}
                        trained_params = {k: v for k, v in raw_params.items() if k in params}

                        save_path = model_dir / f"{self.exchange}_{clean_sym}_{self.tf}_regression_{model_name}.joblib"
                        save_model(model, str(save_path))

                except Exception as e:
                    logger.error(f"[{model_name}] Training failed: {e}")
                    continue

                logger.info(
                    f"[{model_name}] RMSE: {metrics['train_rmse']:.6f} / "
                    f"{metrics['val_rmse']:.6f} / {metrics['test_rmse']:.6f} | "
                    f"R2: {metrics['test_r2']:.4f}"
                )

                # Save prediction CSVs
                prefix     = f"{self.exchange}_{clean_sym}_{self.tf}_regression_{model_name}"
                val_pred   = self.save_predictions(val_df,  preds["val_preds"],  pred_dir / f"{prefix}_predicted.csv")
                test_pred  = self.save_predictions(test_df, preds.get("test_preds", preds["val_preds"]),
                                                    pred_dir / f"{prefix}_test_predicted.csv")

                all_predictions[clean_sym][model_name] = {"val": val_pred, "test": test_pred}

                # Leaderboard entry
                entry = create_leaderboard_entry(
                    task="regression", model_name=model_name, metrics=metrics,
                    model_save_path=save_path, pred_save_path=pred_dir / f"{prefix}_predicted.csv",
                    hyperparameters=trained_params
                )
                entry.pop("prediction_file", None)
                leaderboard.append(entry)

            # Sort leaderboard by test R2 (higher = better)
            leaderboard.sort(key=lambda x: float(x.get("test_r2") or 0.0), reverse=True)

            run_meta[clean_sym] = {
                "leaderboard": leaderboard,
                "models": {
                    e["model"]: {
                        "hyperparameters":  e.get("hyperparameters", {}),
                        "accuracy_metrics": {
                            k: e.get(k) for k in [
                                "train_rmse", "train_mae", "train_r2", "train_total",
                                "val_rmse",   "val_mae",   "val_r2",   "val_total",
                                "test_rmse",  "test_mae",  "test_r2",  "test_total",
                            ]
                        },
                        "artifacts": {"model_file": e.get("model_file")},
                    }
                    for e in leaderboard
                },
            }
            logger.info(f"Regression training finished for {clean_sym} {self.tf}")

        return all_predictions, run_meta
