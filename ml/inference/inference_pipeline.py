import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.metrics import precision_score, recall_score

from cryptosight.utils.config import load_config, get_ml_artifacts_dir, save_config_artifact
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
            import copy
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
            preproc_path = preproc_dir / "preprocessor.joblib"   # exact filename saved by QuantPreprocessor.save()
            if not preproc_path.exists():
                logger.error(f"[{symbol}] Preprocessor not found at {preproc_path}. Skipping.")
                continue

            preprocessor = load_model(str(preproc_path))  # joblib.load under the hood
            timestamps = features_df["timestamp"].values
            X_live = preprocessor.transform(features_df)

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

            for model_name in self.models:
                model_dir = get_ml_artifacts_dir("model")
                model_path = model_dir / f"{symbol}_{self.tf}_{model_name}.joblib"

                if not model_path.exists():
                    logger.warning(f"[{symbol}] Model '{model_name}' not found. Skipping.")
                    continue

                model    = load_model(str(model_path))
                
                # Pass ONLY the feature columns to the model (drops timestamp)
                X_model = X_live[preprocessor.feature_cols]
                
                raw_preds = model.predict(
                    X_model.values if isinstance(X_model, pd.DataFrame) else X_model
                )

                # Map [0,1,2] → [-1,0,1] for classification
                signals    = raw_preds - 1 if self.task_type == "classification" else raw_preds
                
                # Build results_df preserving the exact pandas series for timestamps
                results_df = pd.DataFrame({
                    "timestamp": features_df["timestamp"].reset_index(drop=True),
                    "signal": signals
                })

                # ── Compute Metrics ───────────────────────────────────────────────
                if "target" in features_with_target.columns:
                    # Force both to UTC to prevent merge conflicts
                    results_df["timestamp"] = pd.to_datetime(results_df["timestamp"], utc=True)
                    features_with_target["timestamp"] = pd.to_datetime(features_with_target["timestamp"], utc=True)

                    merged    = results_df.merge(
                        features_with_target[["timestamp", "target"]],
                        on="timestamp", how="inner"
                    )
                    actual    = merged["target"].values
                    predicted = merged["signal"].values
                    total     = len(actual)
                    correct   = int(np.sum(actual == predicted))
                    accuracy  = correct / total * 100.0 if total > 0 else 0.0

                    prec = precision_score(actual, predicted, average="macro", zero_division=0) * 100.0
                    rec  = recall_score(actual, predicted, average="macro", zero_division=0) * 100.0

                    # Count predicted signal distribution
                    preds_series   = pd.Series(predicted)
                    buy_count      = int((preds_series == 1).sum())
                    hold_count     = int((preds_series == 0).sum())
                    sell_count     = int((preds_series == -1).sum())

                    # Count actual signal distribution
                    actual_series  = pd.Series(actual)
                    actual_buy     = int((actual_series == 1).sum())
                    actual_hold    = int((actual_series == 0).sum())
                    actual_sell    = int((actual_series == -1).sum())

                    # Print to console
                    print("\n" + "=" * 65)
                    print(f"  INFERENCE  |  {symbol}  |  {model_name.upper()}  |  {self.tf}")
                    print("=" * 65)
                    print(f"  Period    : {self.start_date}  →  {self.end_date}")
                    print(f"  Total Rows: {total}")
                    print(f"  Correct   : {correct} rows where Actual == Predicted")
                    print(f"  Accuracy  : {correct}/{total} ({accuracy:.2f}%)")
                    print(f"  Precision : {prec:.2f}%    Recall: {rec:.2f}%")
                    print("-" * 65)
                    print(f"  {'Signal':<12} {'Actual':>10} {'Predicted':>12}")
                    print(f"  {'Buy  (+1)':<12} {actual_buy:>10} {buy_count:>12}")
                    print(f"  {'Hold (0)':<12} {actual_hold:>10} {hold_count:>12}")
                    print(f"  {'Sell (-1)':<12} {actual_sell:>10} {sell_count:>12}")
                    print("-" * 65)
                    print(f"  {'Timestamp':<26} {'Actual':>8} {'Predicted':>12} {'':>6}")
                    print("-" * 65)
                    for _, row in merged.head(20).iterrows():
                        mark = "✓" if row["target"] == row["signal"] else "✗"
                        print(f"  {str(row['timestamp']):<26} {int(row['target']):>8} {int(row['signal']):>12}  {mark}")
                    print("=" * 65)

                    # Append into the single report dict under this model's key
                    inference_report["models"][model_name] = {
                        "total_rows":       total,
                        "correct":          correct,
                        "accuracy":         f"{accuracy:.2f}%",
                        "precision":        f"{prec:.2f}%",
                        "recall":           f"{rec:.2f}%",
                        "signal_distribution": {
                            "buy  (+1)": {"actual": actual_buy,  "predicted": buy_count},
                            "hold (0)":  {"actual": actual_hold, "predicted": hold_count},
                            "sell (-1)": {"actual": actual_sell, "predicted": sell_count},
                        }
                    }

                # Save individual model's inference CSV to ml/csv_files/inference/
                csv_dir = Path(__file__).resolve().parent.parent / "csv_files" / "inference"
                csv_dir.mkdir(parents=True, exist_ok=True)
                model_csv_path = csv_dir / f"{symbol}_{self.tf}_{model_name}_inference.csv"
                results_df.to_csv(model_csv_path, index=False, encoding="utf-8")

                # Add this model's signals to the unified CSV DataFrame
                results_df["timestamp"] = pd.to_datetime(results_df["timestamp"], utc=True)
                combined_csv_df = combined_csv_df.merge(results_df, on="timestamp", how="left")
                combined_csv_df.rename(columns={"signal": f"{model_name}_predicted_signal"}, inplace=True)

                all_results[f"{symbol}_{model_name}"] = results_df

            # ── STEP 6: Save ONE unified inference report to artifacts ────────────
            save_config_artifact(
                inference_report,
                f"inference_{symbol}_{self.tf}.yaml",
                asset_type="config"
            )
            logger.info(f"[{symbol}] Saved inference report to artifacts/configs/inference_{symbol}_{self.tf}.yaml")
            
            # ── STEP 7: Save ONE unified easy-to-read CSV inside ml/csv_files/inference/ ────────────
            csv_dir = Path(__file__).resolve().parent.parent / "csv_files" / "inference"
            csv_dir.mkdir(parents=True, exist_ok=True)
            csv_path = csv_dir / f"{symbol}_{self.tf}_combined_inference.csv"
            combined_csv_df.to_csv(csv_path, index=False)
            logger.info(f"[{symbol}] Saved combined CSV to {csv_path}")

        return all_results


if __name__ == "__main__":
    engine = InferencePipeline()
    all_signals = engine.predict()