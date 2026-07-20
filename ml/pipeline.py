import sys
from pathlib import Path
import json
import yaml
import pandas as pd
import numpy as np

# Add the parent folder of the workspace to sys.path to enable cryptosight package imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config, get_ml_artifacts_dir
from cryptosight.ml.preprocessing.features import MLFeatureBuilder
from cryptosight.ml.data.data_splitter import split_data_chronological
from cryptosight.ml.preprocessing.preproc import QuantPreprocessor

logger = get_logger("MLMain")


class QuantMLPipeline:
    """
    End-to-end Quant ML Pipeline.

    Usage:
        QuantMLPipeline().run_pipeline()
    """

    # 9 professional quant metrics stored in Master JSON per model
    TRADING_METRICS = {
        "sharpe", "sortino", "calmar", "max_drawdown",
        "cagr", "profit_factor", "win_rate",
        "recovery_factor", "risk_of_ruin"
    }

    def __init__(self, config_path: str | Path = None):
        self.config_path = Path(config_path or Path(__file__).resolve().parent / "ml_config.yaml")
        self.config      = load_config(self.config_path)
        self.model_type  = self.config.get("model_type").lower()
        self.exchange    = self.config["data"].get("exchange").lower().strip()
        self.clean_tf    = str(self.config["data"]["target_timeframe"]).strip()

        # Output directories
        ml_root               = Path(__file__).resolve().parent
        self.out_dir          = ml_root / "csv_files"
        self.backtest_out_dir = self.out_dir / "backtesting"
        self.config_dir       = get_ml_artifacts_dir("config")
        self.backt_cfg_path   = ml_root.parent / "backtesting" / "backt_config.yaml"

        for d in [self.out_dir, self.backtest_out_dir]:
            d.mkdir(parents=True, exist_ok=True)

        logger.info(f"QuantMLPipeline | task={self.model_type} | exchange={self.exchange} | tf={self.clean_tf}")

    # ── STEP 1 ────────────────────────────────────────────────────────────────
    def build_features(self) -> dict[str, pd.DataFrame]:
        """Downloads OHLCV data, resamples, computes indicators, attaches target."""
        logger.info("STEP 1 — Feature Engineering")
        datasets = MLFeatureBuilder(config=self.config).build_dataset()

        for sym, df in datasets.items():
            path = self.out_dir / f"{self.exchange}_{sym.upper()}_{self.clean_tf}_features.csv"
            df.to_csv(path, index=False, encoding="utf-8")
            print(f"  [{sym}] Features → {path}  ({len(df)} rows)")

        return datasets

    # ── STEP 2 ────────────────────────────────────────────────────────────────
    def split_data(self, df: pd.DataFrame) -> tuple:
        """Splits df chronologically into Train / Val / Test. Returns (train, val, test, split_info)."""
        logger.info("STEP 2 — Chronological Split")
        split_cfg = self.config.get("splitting", {})
        return split_data_chronological(
            df,
            train_ratio=float(split_cfg["train_ratio"]),
            val_ratio=float(split_cfg["val_ratio"]),
            test_ratio=float(split_cfg["test_ratio"]),
            config=self.config
        )

    # ── STEP 3 ────────────────────────────────────────────────────────────────
    def preprocess(self, clean_sym: str, train_df: pd.DataFrame,
                   val_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
        """
        Fits scaler on Train only (zero data leakage), transforms all 3 splits.
        Returns (train_prep, val_prep, test_prep, preprocessor).
        """
        logger.info("STEP 3 — Preprocessing")
        preprocessor = QuantPreprocessor()
        preprocessor.fit(train_df)

        train_prep = preprocessor.transform(train_df)
        val_prep   = preprocessor.transform(val_df)
        test_prep  = preprocessor.transform(test_df)

        preproc_path = preprocessor.save(clean_sym, self.exchange, self.clean_tf)
        print(f"  [{clean_sym}] Preprocessor → {preproc_path}")

        for name, split_df in [("train", train_prep), ("validation", val_prep), ("test", test_prep)]:
            p = self.out_dir / f"{self.exchange}_{clean_sym}_{self.clean_tf}_{name}_preprocessed.csv"
            split_df.to_csv(p, index=False, encoding="utf-8")
            print(f"    {name.capitalize()} → {p}")

        return train_prep, val_prep, test_prep, preprocessor

    # ── STEP 4 ────────────────────────────────────────────────────────────────
    def train_models(self, train_prep: pd.DataFrame, val_prep: pd.DataFrame,
                     test_prep: pd.DataFrame) -> tuple[dict, dict, str]:
        """
        Trains all configured models. Returns (val_predictions, run_meta, model_key).
        Returns (None, None, None) if model_type is unsupported.
        """
        logger.info(f"STEP 4 — Training {self.model_type.upper()} models")

        if self.model_type == "classification":
            from cryptosight.ml.models.classification.train_classifiers import ClassifierPipeline as Pipeline
            model_key = "3_classification_models"
        elif self.model_type == "regression":
            from cryptosight.ml.models.regression.train_regressors import RegressorPipeline as Pipeline
            model_key = "3_regression_models"
        else:
            print(f"  model_type='{self.model_type}' not yet implemented.")
            return None, None, None

        val_predictions, run_meta = Pipeline(self.config).train(train_prep, val_prep, test_prep)
        return val_predictions, run_meta, model_key

    # ── STEP 5 ────────────────────────────────────────────────────────────────
    def save_pipeline_json(self, clean_sym: str, df: pd.DataFrame, split_info: dict,
                           train_ratio: float, val_ratio: float, test_ratio: float,
                           preprocessor: QuantPreprocessor, run_meta: dict,
                           model_key: str) -> tuple[dict, Path]:
        """
        Builds and saves the unified Master Pipeline JSON.
        Returns (quant_pipeline_run dict, master_json_path).
        trading_metrics are injected later by backtest() which resaves the JSON.
        """
        logger.info("STEP 5 — Saving Master Pipeline JSON")

        back_cfg = {}
        if self.backt_cfg_path.exists():
            try:
                back_cfg = yaml.safe_load(self.backt_cfg_path.read_text(encoding="utf-8")) or {}
            except Exception:
                pass

        quant_pipeline_run = {
            "1_dataset_info": {
                "symbol":                   clean_sym,
                "exchange":                 self.exchange,
                "base_timeframe":           self.config["data"].get("timeframe"),
                "target_timeframe":         self.clean_tf,
                "start_date":               self.config["data"].get("start_date"),
                "end_date":                 self.config["data"].get("end_date"),
                "total_dataset_rows":       len(df),
                "features_generated_count": len([c for c in df.columns if c not in ["timestamp", "target"]]),
                "features_summary":         split_info.get("features_summary"),
            },
            "2_preprocessing_info": {
                "splitting_ratios":        {"train": train_ratio, "val": val_ratio, "test": test_ratio},
                "chronological_splits":    split_info.get("splits_summary"),
                "preprocessor_parameters": preprocessor.get_metadata(),
            },
            model_key:          run_meta.get(clean_sym, run_meta),
            "4_system_configs": {"backtesting_config": back_cfg},
        }

        master_json_path = (
            self.config_dir / f"{self.exchange}_{clean_sym}_{self.clean_tf}_{self.model_type}.json"
        )
        master_json_path.write_text(
            json.dumps(quant_pipeline_run, indent=4, default=str), encoding="utf-8"
        )
        print(f"  Master JSON → {master_json_path}")
        return quant_pipeline_run, master_json_path

    # ── STEP 6 & 7 ───────────────────────────────────────────────────────────
    def backtest(self, clean_sym: str, val_predictions: dict, model_key: str,
                 quant_pipeline_run: dict, master_json_path: Path) -> None:
        """
        Builds signals from predictions, runs BacktestingEngine (in-memory),
        saves ledger CSV, computes TRADING_METRICS, injects into Master JSON.
        """
        logger.info("STEP 6-7 — Backtesting + Trading Metrics")
        from cryptosight.backtesting.backtest import BacktestingEngine
        from cryptosight.stats.metrices import compute_all_metrics

        engine  = BacktestingEngine(config_path=str(self.backt_cfg_path))
        signals = self.build_signals(clean_sym, val_predictions)

        for m_name, sig_df in signals.items():
            try:
                print(f"  [{m_name}] Running Backtest...")
                ledger_df = engine.run_pipeline(external_signals_df=sig_df)

                ledger_path = (
                    self.backtest_out_dir /
                    f"{self.exchange}_{clean_sym}_{self.clean_tf}_{m_name}_ledger.csv"
                )
                ledger_df.to_csv(ledger_path, index=False)
                print(f"  [{m_name}] Ledger → {ledger_path}  ({len(ledger_df)} trades)")

                if not ledger_df.empty and "perc_pnl" in ledger_df.columns:
                    all_stats       = compute_all_metrics(ledger_df["perc_pnl"], is_percentage=True)
                    trading_metrics = {k: v for k, v in all_stats.items() if k in self.TRADING_METRICS}
                    models_block    = quant_pipeline_run.get(model_key, {}).get("models", {})
                    if m_name in models_block:
                        models_block[m_name]["trading_metrics"] = trading_metrics
                        print(f"  [{m_name}] Trading metrics injected ✓")
                    
                    # Also inject into the corresponding leaderboard entry for full consistency
                    leaderboard_block = quant_pipeline_run.get(model_key, {}).get("leaderboard", [])
                    for entry in leaderboard_block:
                        if entry.get("model") == m_name:
                            entry["trading_metrics"] = trading_metrics
                else:
                    print(f"  [{m_name}] No trades — trading_metrics skipped.")

            except Exception as e:
                print(f"  [{m_name}] Backtest error: {e}")

        master_json_path.write_text(
            json.dumps(quant_pipeline_run, indent=4, default=str), encoding="utf-8"
        )
        print(f"  Master JSON updated → {master_json_path}")

    # ── STEP 8 ────────────────────────────────────────────────────────────────
    def check_inference(self, clean_sym: str, val_predictions: dict) -> None:
        """
        Runs InferencePipeline on the test date range and compares output
        against training predictions. 100% = no data leakage.
        """
        logger.info("STEP 8 — Inference Consistency Check")
        from cryptosight.ml.inference.inference_pipeline import InferencePipeline

        print("\n  ── STEP 8: Inference Consistency Check ──")
        inference_results = InferencePipeline(config_path=self.config_path).predict()

        compare_dir   = self.out_dir / self.model_type / "test_vs_inference"
        test_pred_dir = self.out_dir / self.model_type / "model_predicted"
        compare_dir.mkdir(parents=True, exist_ok=True)

        for model_name, dfs in val_predictions.get(clean_sym, {}).items():
            test_csv = test_pred_dir / (
                f"{self.exchange}_{clean_sym}_{self.clean_tf}"
                f"_{self.model_type}_{model_name}_test_predicted.csv"
            )
            inf_key = f"{clean_sym}_{model_name}"

            if not test_csv.exists():
                print(f"  [{model_name}] test_predicted.csv not found — skipping.")
                continue
            if inf_key not in inference_results:
                print(f"  [{model_name}] inference result not found — skipping.")
                continue

            test_df = pd.read_csv(test_csv, parse_dates=["timestamp"])
            test_df["timestamp"] = pd.to_datetime(test_df["timestamp"], utc=True)

            inf_df = inference_results[inf_key][["timestamp", "signal"]].copy()
            inf_df["timestamp"] = pd.to_datetime(inf_df["timestamp"], utc=True)
            inf_df.rename(columns={"signal": "inference_signal"}, inplace=True)

            actual_col = "actual"    if "actual"    in test_df.columns else "target"
            pred_col   = "predicted" if "predicted" in test_df.columns else "predicted_target"

            merged = pd.merge(
                test_df[["timestamp", actual_col, pred_col]],
                inf_df, on="timestamp", how="inner"
            )

            if self.model_type == "regression":
                # Compare continuous regression predictions directly to verify mathematical consistency
                merged["match"] = np.isclose(merged[pred_col], merged["inference_signal"], atol=1e-6)
            else:
                merged["match"] = merged[pred_col] == merged["inference_signal"]

            match_pct = merged["match"].mean() * 100 if len(merged) > 0 else 0.0
            cmp_path  = compare_dir / (
                f"{self.exchange}_{clean_sym}_{self.clean_tf}"
                f"_{self.model_type}_{model_name}_test_vs_inference.csv"
            )
            merged.to_csv(cmp_path, index=False, encoding="utf-8")
            print(f"  [{model_name}] Agreement: {match_pct:.2f}%  ({len(merged)} rows) → {cmp_path}")

    # ── STEP 6 HELPER ─────────────────────────────────────────────────────────
    def build_signals(self, clean_sym: str, val_predictions: dict) -> dict:
        """
        Converts test-set predictions into backtester-compatible signal DataFrames.
        Regression    → auto-threshold = 0.5 × pred_std per model
        Classification → predictions are already [-1, 0, 1]
        Returns: {model_name: signal_df}  (timestamp as index, 'signal' column)
        """
        signals = {}

        if self.model_type == "regression":
            from cryptosight.ml.signals.regression_signals import generate_regression_signals

            test_preds = {m: dfs["test"]
                          for m, dfs in val_predictions.get(clean_sym, {}).items()}

            model_thresholds = {}
            for m, pdf in test_preds.items():
                pred_std            = float(pdf["predicted_target"].std())
                model_thresholds[m] = max(pred_std * 0.5, 1e-6)
                print(f"  [{m}] Auto threshold = {model_thresholds[m]:.6f} (0.5 × std {pred_std:.6f})")

            signals = generate_regression_signals(
                test_preds, self.config, clean_sym, model_thresholds=model_thresholds
            )

        elif self.model_type == "classification":
            for m, dfs in val_predictions.get(clean_sym, {}).items():
                sig_df = dfs["test"][["timestamp", "predicted"]].copy()
                sig_df["timestamp"] = pd.to_datetime(sig_df["timestamp"], utc=True)
                sig_df = sig_df.rename(columns={"predicted": "signal"})
                sig_df.set_index("timestamp", inplace=True)
                signals[m] = sig_df

        return signals

    # ── ORCHESTRATOR ──────────────────────────────────────────────────────────
    def run_pipeline(self) -> dict[str, pd.DataFrame]:
        """Runs Steps 1-8 in order for every symbol defined in config."""
        print("\n  ══════════════  CRYPTOSIGHT QUANT ML PIPELINE  ══════════════")
        split_cfg = self.config.get("splitting", {})

        datasets = self.build_features()

        for sym, df in datasets.items():
            clean_sym = sym.upper().strip()
            print(f"\n  ── {clean_sym} | {self.model_type.upper()} ──")

            train_df, val_df, test_df, split_info = self.split_data(df)

            train_prep, val_prep, test_prep, preprocessor = self.preprocess(
                clean_sym, train_df, val_df, test_df
            )

            val_predictions, run_meta, model_key = self.train_models(
                train_prep, val_prep, test_prep
            )
            if not run_meta:
                print(f"  [{clean_sym}] No models trained — skipping.")
                continue

            quant_pipeline_run, master_json_path = self.save_pipeline_json(
                clean_sym, df, split_info,
                float(split_cfg["train_ratio"]),
                float(split_cfg["val_ratio"]),
                float(split_cfg["test_ratio"]),
                preprocessor, run_meta, model_key
            )

            try:
                self.backtest(clean_sym, val_predictions, model_key,
                              quant_pipeline_run, master_json_path)
            except Exception as e:
                print(f"  Backtest error: {e}")

            try:
                self.check_inference(clean_sym, val_predictions)
            except Exception as e:
                print(f"  inference check error: {e}")

        print("\n  ══════════════  PIPELINE COMPLETE  ══════════════\n")
        return datasets
