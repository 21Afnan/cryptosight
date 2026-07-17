import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.metrics import precision_score, recall_score, mean_squared_error, mean_absolute_error, r2_score
import json
import copy
import yaml

from cryptosight.utils.config import load_config, get_ml_artifacts_dir
from cryptosight.ml.preprocessing.preproc import QuantPreprocessor
from cryptosight.ml.models.model_utills import load_model
from cryptosight.utils.logger import get_logger
from cryptosight.data.downloader import Downloader
from cryptosight.ml.preprocessing.features import MLFeatureBuilder

logger = get_logger("Inference")


class InferencePipeline:
    """
    Senior Quant-grade Inference Engine.
    Orchestrates live/backtest inference using trained ML models.
    """

    def __init__(self, config_path: str | Path = None):
        # Resolve ml_config.yaml path
        self.config_path = Path(config_path or Path(__file__).resolve().parent.parent / "ml_config.yaml")
        self.config      = load_config(self.config_path)

        # Inherit base data config
        data_cfg       = self.config.get("data", {})
        self.symbols   = [str(s).upper().strip() for s in data_cfg.get("symbols", [])]
        self.exchange  = str(data_cfg.get("exchange")).lower().strip()
        self.timeframe = str(data_cfg.get("timeframe")).strip()        # base: e.g. "1m"
        self.tf        = str(data_cfg.get("target_timeframe")).strip()  # target: e.g. "15m"

        # Read inference configurations
        inf_cfg = self.config.get("inference", {})
        if not inf_cfg:
            raise ValueError("Missing 'inference:' configuration block in ml_config.yaml")

        self.task_type  = str(inf_cfg.get("model_type", "classification")).lower().strip()
        self.models     = [str(m).lower().strip() for m in inf_cfg.get("models", [])]
        self.start_date = str(inf_cfg.get("start_date")).strip()
        self.end_date   = str(inf_cfg.get("end_date")).strip()

        # Paths
        self.csv_dir = Path(__file__).resolve().parent.parent / "csv_files" / "inference"
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.preproc_dir = get_ml_artifacts_dir("preprocessor")
        self.model_dir   = get_ml_artifacts_dir("model")
        self.config_dir  = get_ml_artifacts_dir("config")

        if not self.models:
            raise ValueError("No models listed under 'inference.models' in ml_config.yaml")

        logger.info(f"InferencePipeline initialized | task={self.task_type} | models={self.models}")

    def fetch_data(self, symbol: str) -> pd.DataFrame:
        """Downloads base timeframe data (with 10-day warmup) and resamples to target timeframe."""
        logger.info(f"[{symbol}] Fetching base data ({self.start_date} to {self.end_date})...")
        dl = Downloader(exchange=self.exchange, symbol=symbol, timeframe=self.timeframe)

        # 10-day warmup prevents indicator boundary issues (NaNs)
        try:
            warmup_start = (
                datetime.strptime(self.start_date, "%Y-%m-%d %H:%M:%S") - timedelta(days=10)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Fall back if start_date is date-only string
            warmup_start = (
                datetime.strptime(self.start_date, "%Y-%m-%d") - timedelta(days=10)
            ).strftime("%Y-%m-%d")
        except Exception:
            warmup_start = self.start_date

        _, resampled_df = dl.resample(
            target_timeframe=self.tf,
            start_time=warmup_start,
            end_time=self.end_date,
            max_retries=3,
            retry_delay=5
        )
        return resampled_df

    def engineer_features(self, resampled_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Engineers technical features and computes target returns.
        Keeps full warmup history (unclipped) so sequence models (LSTMs) can predict correctly.
        Returns: (features_df, features_with_target)
        """
        logger.info(f"Engineering technical indicators & features...")
        inf_cfg = copy.deepcopy(self.config)
        inf_cfg["data"]["start_date"] = self.start_date
        inf_cfg["data"]["end_date"]   = self.end_date

        builder = MLFeatureBuilder(config=inf_cfg)
        features_df = builder.add_technical_features(resampled_df)
        if "timestamp" not in features_df.columns:
            features_df = features_df.reset_index()

        features_with_target = builder.add_target(features_df.copy())
        if "timestamp" not in features_with_target.columns:
            features_with_target = features_with_target.reset_index()

        return features_df, features_with_target

    def load_preprocessor(self, symbol: str) -> QuantPreprocessor:
        """Loads the fitted scaler/preprocessor for the given symbol."""
        preproc_path = self.preproc_dir / f"{self.exchange}_{symbol}_{self.tf}_preprocessor.joblib"
        if not preproc_path.exists():
            raise FileNotFoundError(f"Fitted preprocessor not found at {preproc_path}")
        return load_model(str(preproc_path))

    def build_inference_sequences(self, X: np.ndarray, lookback: int) -> np.ndarray:
        """
        Converts unclipped 2D tabular features of shape (N, features) into
        sliding 3D sequences of shape (N, lookback, features) expected by the LSTM.
        For indexes < lookback, pads using the first available row features.
        """
        X_seqs = []
        for i in range(len(X)):
            if i < lookback:
                # Pad early rows with copies of the first row to keep array shapes aligned
                pad_len = lookback - i
                seq = np.vstack([np.tile(X[0], (pad_len, 1)), X[0 : i]])
            else:
                seq = X[i - lookback : i]
            X_seqs.append(seq)
        return np.array(X_seqs, dtype=np.float32)

    def predict_model(self, symbol: str, model_name: str, X_model: pd.DataFrame,
                      features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Loads the trained model checkpoint and generates prediction signals.
        Supports both scikit-learn models (.joblib) and PyTorch LSTMs (.pt).
        Clips predictions to the requested inference window (>= start_date) before returning.
        Returns a signal DataFrame with columns ['timestamp', 'signal'].
        """
        import torch

        is_lstm = (model_name == "lstm_regressor")
        ext = "pt" if is_lstm else "joblib"
        model_path = self.model_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}_{model_name}.{ext}"

        if not model_path.exists():
            logger.warning(f"[{symbol}] Model checkpoint not found: {model_path}")
            return None

        # Predict
        if is_lstm:
            from cryptosight.ml.models.regression.pytorch_lstm import LSTMNet
            X_arr = X_model.values if isinstance(X_model, pd.DataFrame) else X_model

            # Retrieve parameters from config
            lstm_cfg = next((m for m in self.config.get("regression", {}).get("models", [])
                             if m.get("name") == "lstm_regressor"), {})
            lstm_params = lstm_cfg.get("parameters", {})
            hidden_size = int(lstm_params.get("hidden_size", 64))
            num_layers  = int(lstm_params.get("num_layers", 1))
            lookback    = int(lstm_params.get("lookback_window", 15))

            # Build sliding sequences using warmup history
            X_seq = self.build_inference_sequences(X_arr, lookback)

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            checkpoint = torch.load(str(model_path), map_location=device)

            model = LSTMNet(input_size=X_arr.shape[1], hidden_size=hidden_size, num_layers=num_layers).to(device)
            state_dict = checkpoint["state_dict"] if (isinstance(checkpoint, dict) and "state_dict" in checkpoint) else checkpoint
            model.load_state_dict(state_dict)
            model.eval()

            with torch.no_grad():
                raw_preds = model(torch.tensor(X_seq, dtype=torch.float32).to(device)).cpu().numpy()
        else:
            model = load_model(str(model_path))
            raw_preds = model.predict(X_model)

        # Classification targets [0, 1, 2] map back to [-1, 0, 1] for signal trading
        signals = raw_preds - 1 if self.task_type == "classification" else raw_preds

        results_df = pd.DataFrame({
            "timestamp": features_df["timestamp"].reset_index(drop=True),
            "signal":    signals
        })

        # Clip predictions to the active inference window (>= start_date)
        results_df = results_df[results_df["timestamp"].astype(str) >= self.start_date].reset_index(drop=True)
        return results_df

    def evaluate_predictions(self, symbol: str, model_name: str, results_df: pd.DataFrame,
                             features_with_target: pd.DataFrame, inference_report: dict) -> None:
        """
        Computes accuracy, precision, recall for classification, or RMSE, MAE, R2 for regression.
        Prints performance report tables and updates the in-memory report dict.
        """
        if "target" not in features_with_target.columns:
            logger.info(f"[{symbol}] 'target' column not in data — skipping metric evaluation.")
            return

        results_df["timestamp"]           = pd.to_datetime(results_df["timestamp"], utc=True)
        features_with_target["timestamp"] = pd.to_datetime(features_with_target["timestamp"], utc=True)

        merged = results_df.merge(features_with_target[["timestamp", "target"]], on="timestamp", how="inner")
        actual    = merged["target"].values
        predicted = merged["signal"].values
        total     = len(actual)

        print("\n" + "=" * 65)
        print(f"  INFERENCE REPORT | {symbol} | {model_name.upper()} | {self.tf}")
        print("=" * 65)
        print(f"  Period    : {self.start_date} → {self.end_date}")
        print(f"  Total Rows: {total}")

        if self.task_type == "classification":
            correct  = int(np.sum(actual == predicted))
            accuracy = correct / total * 100.0 if total > 0 else 0.0
            prec = precision_score(actual, predicted, average="macro", zero_division=0) * 100.0
            rec  = recall_score(actual, predicted, average="macro", zero_division=0) * 100.0

            actual_s = pd.Series(actual)
            preds_s  = pd.Series(predicted)

            print(f"  Correct   : {correct}/{total} ({accuracy:.2f}%)")
            print(f"  Precision : {prec:.2f}% | Recall: {rec:.2f}%")
            print("-" * 65)
            print(f"  {'Signal':<12} {'Actual':>10} {'Predicted':>12}")
            print(f"  {'Buy  (+1)':<12} {int((actual_s==1).sum()):>10} {int((preds_s==1).sum()):>12}")
            print(f"  {'Hold (0)':<12} {int((actual_s==0).sum()):>10} {int((preds_s==0).sum()):>12}")
            print(f"  {'Sell (-1)':<12} {int((actual_s==-1).sum()):>10} {int((preds_s==-1).sum()):>12}")
            print("-" * 65)
            print(f"  {'Timestamp':<26} {'Actual':>8} {'Predicted':>12}")
            print("-" * 65)
            for _, row in merged.head(10).iterrows():
                mark = "✓" if row["target"] == row["signal"] else "✗"
                print(f"  {str(row['timestamp']):<26} {int(row['target']):>8} {int(row['signal']):>12}  {mark}")
            print("=" * 65)

            inference_report["models"][model_name] = {
                "total_rows": total,
                "correct":    correct,
                "accuracy":   f"{accuracy:.2f}%",
                "precision":  f"{prec:.2f}%",
                "recall":     f"{rec:.2f}%",
                "signal_distribution": {
                    "buy  (+1)": {"actual": int((actual_s==1).sum()),  "predicted": int((preds_s==1).sum())},
                    "hold (0)":  {"actual": int((actual_s==0).sum()),  "predicted": int((preds_s==0).sum())},
                    "sell (-1)": {"actual": int((actual_s==-1).sum()), "predicted": int((preds_s==-1).sum())},
                }
            }

        else:  # regression
            rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
            mae  = float(mean_absolute_error(actual, predicted))
            r2   = float(r2_score(actual, predicted))

            print(f"  RMSE      : {rmse:.6f}")
            print(f"  MAE       : {mae:.6f}")
            print(f"  R2 Score  : {r2:.4f}")
            print("-" * 65)
            print(f"  {'Timestamp':<26} {'Actual':>14} {'Predicted':>14}")
            print("-" * 65)
            for _, row in merged.head(10).iterrows():
                print(f"  {str(row['timestamp']):<26} {float(row['target']):>14.6f} {float(row['signal']):>14.6f}")
            print("=" * 65)

            inference_report["models"][model_name] = {
                "total_rows": total,
                "rmse":       round(rmse, 6),
                "mae":        round(mae, 6),
                "r2":         round(r2, 4)
            }

    def save_outputs(self, symbol: str, combined_csv_df: pd.DataFrame, inference_report: dict) -> None:
        """Saves combined inference results CSV and writes/updates the Master pipeline JSON."""
        # Save unified CSV
        csv_path = self.csv_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}_combined_inference.csv"
        combined_csv_df.to_csv(csv_path, index=False)
        logger.info(f"[{symbol}] Combined predictions saved → {csv_path}")

        # Update Master pipeline JSON report
        master_json_path = self.config_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}.json"
        pipeline_data = {}
        if master_json_path.exists():
            try:
                pipeline_data = json.loads(master_json_path.read_text(encoding="utf-8")) or {}
            except Exception as e:
                logger.warning(f"Could not read existing Master JSON: {e}")

        pipeline_data["inference_report"] = inference_report
        try:
            master_json_path.write_text(json.dumps(pipeline_data, indent=4, default=str), encoding="utf-8")
            logger.info(f"[{symbol}] Master JSON updated with inference_report → {master_json_path}")
        except Exception as e:
            logger.error(f"[{symbol}] Failed to save Master JSON: {e}")

    def predict(self) -> dict[str, pd.DataFrame]:
        """Orchestrates predictions end-to-end for all symbols."""
        all_results = {}

        for symbol in self.symbols:
            # ── STEP 1: Fetch base market data & resample ───────────────────
            resampled_df = self.fetch_data(symbol)
            if resampled_df is None or resampled_df.empty:
                logger.error(f"[{symbol}] No data loaded. Skipping.")
                continue

            # ── STEP 2: Engineer technical indicators & targets ──────────────
            # Kept unclipped with full warmup history
            features_df, features_with_target = self.engineer_features(resampled_df)
            if features_df.empty:
                logger.error(f"[{symbol}] No candles in inference range. Skipping.")
                continue

            # ── STEP 3: Load Preprocessor Scaler & transform live data ────────
            try:
                preprocessor = self.load_preprocessor(symbol)
            except Exception as e:
                logger.error(f"[{symbol}] Preprocessor load failed: {e}. Skipping.")
                continue

            X_live = preprocessor.transform(features_df)
            X_model = X_live[preprocessor.feature_cols]

            # ── STEP 4: Setup Combined CSV & Report tracking (Clipped to active window) 
            features_df_clipped = features_df[features_df["timestamp"].astype(str) >= self.start_date].copy()
            features_with_target_clipped = features_with_target[
                features_with_target["timestamp"].astype(str) >= self.start_date
            ].copy()

            combined_csv_df = features_df_clipped[["timestamp"]].copy().reset_index(drop=True)
            combined_csv_df["timestamp"] = pd.to_datetime(combined_csv_df["timestamp"], utc=True)
            if "target" in features_with_target_clipped.columns:
                target_df = features_with_target_clipped[["timestamp", "target"]].copy()
                target_df["timestamp"] = pd.to_datetime(target_df["timestamp"], utc=True)
                combined_csv_df = combined_csv_df.merge(target_df, on="timestamp", how="left")
                combined_csv_df.rename(columns={"target": "actual_signal"}, inplace=True)

            inference_report = {
                "symbol":    symbol,
                "timeframe": self.tf,
                "task_type": self.task_type,
                "period":    {"start": self.start_date, "end": self.end_date},
                "models":    {}
            }

            # ── STEP 5: Run predictions, evaluate metrics, and save ledger CSVs
            for model_name in self.models:
                results_df = self.predict_model(symbol, model_name, X_model, features_df)
                if results_df is None:
                    continue

                self.evaluate_predictions(symbol, model_name, results_df, features_with_target_clipped, inference_report)

                # Save individual model inference CSV
                model_csv_path = self.csv_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}_{model_name}_inference.csv"
                results_df.to_csv(model_csv_path, index=False, encoding="utf-8")

                # Merge model prediction signals to combined output DF
                results_df["timestamp"] = pd.to_datetime(results_df["timestamp"], utc=True)
                combined_csv_df = combined_csv_df.merge(results_df, on="timestamp", how="left")
                combined_csv_df.rename(columns={"signal": f"{model_name}_predicted_signal"}, inplace=True)

                all_results[f"{symbol}_{model_name}"] = results_df

            # ── STEP 6: Save combined CSV and update master config JSON ─────────
            self.save_outputs(symbol, combined_csv_df, inference_report)

        return all_results


# ── Standalone execution entry point ──────────────────────────────────────────
def run_inference_pipeline(config_path: str | Path = None) -> dict[str, pd.DataFrame]:
    return InferencePipeline(config_path).predict()


if __name__ == "__main__":
    run_inference_pipeline()