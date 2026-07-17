import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.metrics import precision_score, recall_score, mean_squared_error, mean_absolute_error, r2_score
import json
import copy

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
    Reads everything from one single master ml_config.yaml.
    - data.symbols, data.exchange, data.timeframe, data.target_timeframe → inherited
    - features, target, splitting                                         → inherited
    - inference.model_type, inference.models, inference.start/end_date   → inference-specific
    No duplication. No separate config file. One source of truth.
    """

    def __init__(self, config_path: str | Path = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent / "ml_config.yaml"
        self.config = load_config(config_path)

        # --- Inherit from top-level data config ---
        data_cfg = self.config.get("data", {})
        self.symbols    = [str(s).upper().strip() for s in data_cfg.get("symbols")]
        self.exchange   = str(data_cfg.get("exchange")).lower()
        self.timeframe  = str(data_cfg.get("timeframe")).strip()       # base: "1m"
        self.tf         = str(data_cfg.get("target_timeframe")).strip() # target: "15m"

        # --- Read inference-specific block ---
        inf_cfg = self.config.get("inference", {})
        if not inf_cfg:
            raise ValueError("Missing 'inference:' block in ml_config.yaml")

        self.task_type   = str(inf_cfg.get("model_type", "classification")).lower()
        self.models      = [str(m).lower() for m in inf_cfg.get("models")]
        self.start_date  = inf_cfg.get("start_date")
        self.end_date    = inf_cfg.get("end_date")

        if not self.models:
            raise ValueError("No models listed under 'inference.models' in ml_config.yaml")

        logger.info(f"[Inference] Task: {self.task_type.upper()} | Models: {self.models}")
        logger.info(f"[Inference] Symbols: {self.symbols} | {self.timeframe}→{self.tf} | {self.start_date} to {self.end_date}")

    def predict(self) -> dict[str, pd.DataFrame]:
        """
        Loops over all symbols, fetches 1m → resamples → engineers features →
        loads each model → predicts signals → evaluates Actual vs Predicted.
        Saves ONE unified inference_report.yaml to artifacts per symbol.
        Returns dict keyed as '{SYMBOL}_{model_name}' → signal DataFrame.
        """
        all_results = {}

        for symbol in self.symbols:
            csv_dir = Path(__file__).resolve().parent.parent / "csv_files" / "inference"
            csv_dir.mkdir(parents=True, exist_ok=True)

            # ── STEP 1: Fetch & Resample ──────────────────────────────────────────
            logger.info(f"[{symbol}] Fetching {self.timeframe} data ({self.start_date} → {self.end_date})...")
            dl = Downloader(exchange=self.exchange, symbol=symbol, timeframe=self.timeframe)

            # 10-day warmup so early indicators don't output NaN
            try:
                warmup_start = (
                    datetime.strptime(self.start_date, "%Y-%m-%d %H:%M:%S") - timedelta(days=10)
                ).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                warmup_start = self.start_date

            _, resampled_df = dl.resample(
                target_timeframe=self.tf,
                start_time=warmup_start,
                end_time=self.end_date,
                max_retries=3,
                retry_delay=5
            )

            if resampled_df is None or resampled_df.empty:
                logger.error(f"[{symbol}] Failed to fetch/resample data. Skipping.")
                continue

            # ── STEP 2: Engineer Features (no target — we are predicting it!) ─────
            logger.info(f"[{symbol}] Engineering technical features on {len(resampled_df)} candles...")
            # Override training dates with inference dates so MLFeatureBuilder logs correctly
            inf_scoped_config = copy.deepcopy(self.config)
            inf_scoped_config["data"]["start_date"] = self.start_date
            inf_scoped_config["data"]["end_date"] = self.end_date

            builder = MLFeatureBuilder(config=inf_scoped_config)
            features_df = builder.add_technical_features(resampled_df)

            # Ensure timestamp is a column, not an index
            if "timestamp" not in features_df.columns:
                features_df = features_df.reset_index()

            # ── STEP 3: Compute Actual Targets (for evaluation only) ──────────────
            features_with_target = builder.add_target(features_df.copy())

            # Ensure timestamp is a column here too
            if "timestamp" not in features_with_target.columns:
                features_with_target = features_with_target.reset_index()

            features_with_target = features_with_target[
                features_with_target["timestamp"].astype(str) >= self.start_date
            ].copy()

            # Clip to requested inference window
            features_df = features_df[features_df["timestamp"].astype(str) >= self.start_date].copy()
            if features_df.empty:
                logger.error(f"[{symbol}] No rows after filtering to inference window. Skipping.")
                continue

            # ── STEP 4: Load Preprocessor (shared across all models for this symbol)
            preproc_dir = get_ml_artifacts_dir("preprocessor")
            preproc_path = preproc_dir / f"{self.exchange}_{symbol}_{self.tf}_preprocessor.joblib"   # exact filename saved by QuantPreprocessor.save()
            if not preproc_path.exists():
                logger.error(f"[{symbol}] Preprocessor not found at {preproc_path}. Skipping.")
                continue

            preprocessor = load_model(str(preproc_path))  # joblib.load under the hood
            X_live = preprocessor.transform(features_df)
            X_model = X_live[preprocessor.feature_cols]

            # ── STEP 5: Loop Models, Predict, Collect Metrics ─────────────────────
            # One report dict for ALL models on this symbol
            inference_report = {
                "symbol":     symbol,
                "timeframe":  self.tf,
                "task_type":  self.task_type,
                "period": {
                    "start": self.start_date,
                    "end":   self.end_date
                },
                "models": {}
            }
            
            # Initialize a unified DataFrame for the final CSV export
            combined_csv_df = features_df[["timestamp"]].copy().reset_index(drop=True)
            combined_csv_df["timestamp"] = pd.to_datetime(combined_csv_df["timestamp"], utc=True)
            if "target" in features_with_target.columns:
                target_df = features_with_target[["timestamp", "target"]].copy()
                target_df["timestamp"] = pd.to_datetime(target_df["timestamp"], utc=True)
                combined_csv_df = combined_csv_df.merge(target_df, on="timestamp", how="left")
                combined_csv_df.rename(columns={"target": "actual_signal"}, inplace=True)

            model_dir = get_ml_artifacts_dir("model")
            for model_name in self.models:

                # --- Resolve model path: .pt for lstm_regressor, .joblib for everything else ---
                if model_name == "lstm_regressor":
                    model_path = model_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}_{model_name}.pt"
                else:
                    model_path = model_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}_{model_name}.joblib"

                if not model_path.exists():
                    logger.warning(f"[{symbol}] Model '{model_name}' not found at {model_path}. Skipping.")
                    continue

                # --- Load model and run predictions ---
                if model_name == "lstm_regressor":
                    import torch
                    from cryptosight.ml.models.regression.pytorch_lstm import LSTMNet
                    X_arr = X_model.values if isinstance(X_model, pd.DataFrame) else X_model
                    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    checkpoint = torch.load(str(model_path), map_location=device)
                    lstm_model = LSTMNet(
                        input_size=X_arr.shape[1],
                        hidden_size=checkpoint.get("params", {}).get("hidden_size", 128) if isinstance(checkpoint, dict) else 128,
                        num_layers=checkpoint.get("params", {}).get("num_layers", 2) if isinstance(checkpoint, dict) else 2
                    ).to(device)
                    state_dict = checkpoint["state_dict"] if isinstance(checkpoint, dict) else checkpoint
                    lstm_model.load_state_dict(state_dict)
                    lstm_model.eval()
                    with torch.no_grad():
                        raw_preds = lstm_model(
                            torch.tensor(X_arr, dtype=torch.float32).to(device)
                        ).cpu().numpy()
                else:
                    model = load_model(str(model_path))
                    raw_preds = model.predict(
                        X_model.values if isinstance(X_model, pd.DataFrame) else X_model
                    )

                # Classification: remap [0,1,2] → [-1,0,1] | Regression: use continuous returns as-is
                signals = raw_preds - 1 if self.task_type == "classification" else raw_preds

                results_df = pd.DataFrame({
                    "timestamp": features_df["timestamp"].reset_index(drop=True),
                    "signal": signals
                })

                # ── Compute Metrics (dynamic per task_type) ───────────────────────
                if "target" in features_with_target.columns:
                    results_df["timestamp"] = pd.to_datetime(results_df["timestamp"], utc=True)
                    features_with_target["timestamp"] = pd.to_datetime(features_with_target["timestamp"], utc=True)

                    merged = results_df.merge(
                        features_with_target[["timestamp", "target"]],
                        on="timestamp", how="inner"
                    )
                    actual    = merged["target"].values
                    predicted = merged["signal"].values
                    total     = len(actual)

                    if self.task_type == "classification":
                        correct  = int(np.sum(actual == predicted))
                        accuracy = correct / total * 100.0 if total > 0 else 0.0
                        prec = precision_score(actual, predicted, average="macro", zero_division=0) * 100.0
                        rec  = recall_score(actual, predicted, average="macro", zero_division=0) * 100.0

                        preds_series  = pd.Series(predicted)
                        actual_series = pd.Series(actual)

                        print("\n" + "=" * 65)
                        print(f"  INFERENCE  |  {symbol}  |  {model_name.upper()}  |  {self.tf}")
                        print("=" * 65)
                        print(f"  Period    : {self.start_date}  →  {self.end_date}")
                        print(f"  Total Rows: {total}")
                        print(f"  Correct   : {correct}/{total} ({accuracy:.2f}%)")
                        print(f"  Precision : {prec:.2f}%    Recall: {rec:.2f}%")
                        print("-" * 65)
                        print(f"  {'Signal':<12} {'Actual':>10} {'Predicted':>12}")
                        print(f"  {'Buy  (+1)':<12} {int((actual_series==1).sum()):>10} {int((preds_series==1).sum()):>12}")
                        print(f"  {'Hold (0)':<12} {int((actual_series==0).sum()):>10} {int((preds_series==0).sum()):>12}")
                        print(f"  {'Sell (-1)':<12} {int((actual_series==-1).sum()):>10} {int((preds_series==-1).sum()):>12}")
                        print("-" * 65)
                        print(f"  {'Timestamp':<26} {'Actual':>8} {'Predicted':>12}")
                        print("-" * 65)
                        for _, row in merged.head(20).iterrows():
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
                                "buy  (+1)": {"actual": int((pd.Series(actual)==1).sum()),  "predicted": int((preds_series==1).sum())},
                                "hold (0)":  {"actual": int((pd.Series(actual)==0).sum()),  "predicted": int((preds_series==0).sum())},
                                "sell (-1)": {"actual": int((pd.Series(actual)==-1).sum()), "predicted": int((preds_series==-1).sum())},
                            }
                        }

                    else:  # regression
                        rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
                        mae  = float(mean_absolute_error(actual, predicted))
                        r2   = float(r2_score(actual, predicted))

                        print("\n" + "=" * 65)
                        print(f"  REGRESSION INFERENCE  |  {symbol}  |  {model_name.upper()}  |  {self.tf}")
                        print("=" * 65)
                        print(f"  Period    : {self.start_date}  →  {self.end_date}")
                        print(f"  Total Rows: {total}")
                        print(f"  RMSE      : {rmse:.6f}")
                        print(f"  MAE       : {mae:.6f}")
                        print(f"  R2 Score  : {r2:.4f}")
                        print("-" * 65)
                        print(f"  {'Timestamp':<26} {'Actual':>14} {'Predicted':>14}")
                        print("-" * 65)
                        for _, row in merged.head(20).iterrows():
                            print(f"  {str(row['timestamp']):<26} {float(row['target']):>14.6f} {float(row['signal']):>14.6f}")
                        print("=" * 65)

                        inference_report["models"][model_name] = {
                            "total_rows": total,
                            "rmse":       round(rmse, 6),
                            "mae":        round(mae, 6),
                            "r2":         round(r2, 4),
                        }

                # Save individual model inference CSV
                csv_dir.mkdir(parents=True, exist_ok=True)
                model_csv_path = csv_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}_{model_name}_inference.csv"
                results_df.to_csv(model_csv_path, index=False, encoding="utf-8")

                # Add to combined CSV
                results_df["timestamp"] = pd.to_datetime(results_df["timestamp"], utc=True)
                combined_csv_df = combined_csv_df.merge(results_df, on="timestamp", how="left")
                combined_csv_df.rename(columns={"signal": f"{model_name}_predicted_signal"}, inplace=True)

                all_results[f"{symbol}_{model_name}"] = results_df

            # ── STEP 6: Update the unified pipeline JSON in artifacts/configs/ ────────────
            config_dir = get_ml_artifacts_dir("config")
            unified_json_path = config_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}.json"
            
            existing_pipeline_data = {}
            if unified_json_path.exists():
                try:
                    with open(unified_json_path, "r", encoding="utf-8") as f:
                        existing_pipeline_data = json.load(f) or {}
                except Exception as e_read:
                    logger.warning(f"Could not read existing unified JSON {unified_json_path}: {e_read}")
            
            existing_pipeline_data["inference_report"] = inference_report
            try:
                with open(unified_json_path, "w", encoding="utf-8") as f:
                    json.dump(existing_pipeline_data, f, indent=4, default=str)
                logger.info(f"[{symbol}] Updated unified pipeline JSON with inference report -> {unified_json_path}")
            except Exception as e_write:
                logger.error(f"[{symbol}] Failed to update unified pipeline JSON: {e_write}")
            
            # ── STEP 7: Save ONE unified easy-to-read CSV inside ml/csv_files/inference/ ────────────
            csv_dir.mkdir(parents=True, exist_ok=True)
            csv_path = csv_dir / f"{self.exchange}_{symbol}_{self.tf}_{self.task_type}_combined_inference.csv"
            combined_csv_df.to_csv(csv_path, index=False)
            logger.info(f"[{symbol}] Saved combined CSV to {csv_path}")

        return all_results


if __name__ == "__main__":
    engine = InferencePipeline()
    all_signals = engine.predict()