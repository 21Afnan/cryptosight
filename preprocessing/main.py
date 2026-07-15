import sys
from pathlib import Path

# Ensure root workspace (`d:\Neurog_Internship`) is in Python path so direct execution works anywhere
root_workspace = Path(__file__).resolve().parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

import numpy as np
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config
from cryptosight.ml.main import get_ml_dataset
from cryptosight.preprocessing.preprocessor import DataPreprocessor
from cryptosight.preprocessing.stationarity import StationarityAnalyzer
from cryptosight.preprocessing.trend_preservation import TrendPreservationAnalyzer
from cryptosight.preprocessing.models import ModelEvaluator
from cryptosight.preprocessing.backtester import PreprocessingBacktester

logger = get_logger("PPMain")


class PreprocessingMain:
    """
    Master orchestrator class for the Quantitative Preprocessing Module.
    Sets up config file paths, initializes output folders (`preprocessed_data`, `model_predicted`, `backtest_ledgers`),
    and runs the complete 5-step evaluation benchmark from start to finish.
    """

    def __init__(self, config_path: str | Path = None):
        if config_path is None:
            self.config_path = Path(__file__).resolve().parent / "pconfig.yaml"
        else:
            self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")

        self.config = load_config(self.config_path)
        self.model_task = str(self.config["model_task"]).lower()

        root_dir = Path(__file__).resolve().parent.parent / "csv_files" / self.model_task
        subfolders = self.config["output_dirs"]["subfolders"]

        self.output_dirs = {
            "preprocessed": root_dir / subfolders["preprocess"],
            "predicted_signals": root_dir / subfolders["predicted_signals"],
            "backtest_ledgers": root_dir / subfolders["backtest_ledgers"],
        }

        for name, path_obj in self.output_dirs.items():
            path_obj.mkdir(parents=True, exist_ok=True)

        self.methods = self.config.get("methods_to_test", [self.config.get("method", "robust")])
        self.models = self.config.get("models", ["lightgbm", "xgboost", "linear_regression"])
        logger.info(f"Initialized PreprocessingMain | Task: [{self.model_task.upper()}] | Config: {self.config_path.name}")

    def run_full_benchmark(self) -> dict[str, pd.DataFrame]:
        """
        Runs the complete end-to-end 5-step quantitative evaluation pipeline:
        1. Preprocesses datasets across all methods & exports CSVs.
        2. Runs Stationarity (ADF/KPSS) and Trend Preservation analysis.
        3. Trains ML models (`LightGBM`, `XGBoost`, `LinearRegression`) & exports predicted signals (`+1, 0, -1`).
        4. Runs step-by-step backtest simulation on original unscaled market prices (`raw_df`).
        5. Runs baseline backtest on actual raw targets (`actual_target`) to measure theoretical maximum performance.
        """
        logger.info("\n" + "=" * 70)
        logger.info(f" STARTING MASTER BENCHMARK PIPELINE | TASK: [{self.model_task.upper()}]")
        logger.info("=" * 70)

        raw_datasets = get_ml_dataset()
        if not raw_datasets:
            logger.error("No raw datasets received from get_ml_dataset(). Terminating benchmark.")
            return {}

        stationarity_analyzer = StationarityAnalyzer()
        trend_analyzer = TrendPreservationAnalyzer()
        # Calibrated threshold for 15m crypto returns (0.0006 = 0.06% return required per bar to trigger signal)
        model_evaluator = ModelEvaluator(task=self.model_task, threshold=0.0006)
        backtester = PreprocessingBacktester()

        leaderboard_by_symbol = {}

        for symbol, raw_df in raw_datasets.items():
            clean_sym = str(symbol).upper().replace("/", "_").replace(":", "_").strip()
            logger.info(f"\n======================================================================")
            logger.info(f" Analyzing Symbol: [{clean_sym}] | Total Bars: {len(raw_df)}")
            logger.info(f"======================================================================")

            leaderboard_rows = []

            for method in self.methods:
                logger.info(f"\n--- STEP 1 & 2: Preprocessing & Statistical Verification [{method.upper()}] ---")
                try:
                    method_cfg = dict(self.config)
                    method_cfg["method"] = method
                    preprocessor = DataPreprocessor(config=method_cfg)

                    processed_df = raw_df.copy()
                    preprocessor.fit_transform(processed_df, train_ratio=0.80)

                    # Save preprocessed dataset (with `timestamp` and `target` intact)
                    prep_csv_name = f"{clean_sym}_{method.lower()}_preprocessed.csv"
                    prep_csv_path = self.output_dirs["preprocessed"] / prep_csv_name
                    processed_df.to_csv(prep_csv_path, index=False, encoding="utf-8")
                    logger.info(f"[{clean_sym}] Saved preprocessed CSV to: {prep_csv_path}")

                    # Run statistical analysis
                    if self.config.get("run_stationarity_analysis", True):
                        stat_summary = stationarity_analyzer.analyze_dataframe(processed_df)
                        logger.debug(f"[{clean_sym}] Stationarity summary generated for {method.upper()}")

                    if self.config.get("run_trend_analysis", True):
                        trend_summary = trend_analyzer.evaluate_dataframe(raw_df, processed_df)
                        logger.debug(f"[{clean_sym}] Trend preservation summary generated for {method.upper()}")

                except Exception as e:
                    logger.error(f"[{clean_sym}] Preprocessing error on method [{method}]: {e}", exc_info=True)
                    continue

                # --- STEP 3 & 4: ML Model Training & Backtesting on Raw OHLCV ---
                for model_name in self.models:
                    logger.info(f"--- STEP 3: Training Model [{model_name.upper()}] on [{method.upper()}] ---")
                    try:
                        eval_res = model_evaluator.train_and_predict(df=processed_df, model_name=model_name)
                        metrics = eval_res["metrics"]
                        predictions_df = eval_res["predictions_df"]

                        # Save clean signal CSV with all related information
                        sig_csv_name = f"{clean_sym}_{method.lower()}_{model_name.lower()}_predicted.csv"
                        sig_csv_path = self.output_dirs["predicted_signals"] / sig_csv_name
                        predictions_df.to_csv(sig_csv_path, index=False, encoding="utf-8")
                        logger.info(f"[{clean_sym}] Saved model predictions CSV to: {sig_csv_path}")

                        # Run backtest on ORIGINAL unscaled raw prices (`raw_df`)
                        logger.info(f"--- STEP 4: Backtesting [{model_name.upper()}] signals against raw prices ---")
                        ledger_csv_name = f"{clean_sym}_{method.lower()}_{model_name.lower()}_ledger.csv"
                        ledger_csv_path = self.output_dirs["backtest_ledgers"] / ledger_csv_name

                        bt_res = backtester.run_preprocessing_backtest(
                            ohlcv_df=raw_df,
                            signals_df=predictions_df[["timestamp", "signal"]],
                            method=method,
                            model=model_name,
                            model_metrics=metrics,
                            output_csv_path=ledger_csv_path,
                        )
                        leaderboard_rows.append(bt_res["summary"])

                    except Exception as e:
                        logger.error(f"[{clean_sym}] Model/Backtest error for [{model_name}] on [{method}]: {e}", exc_info=True)

                # --- STEP 5: Theoretical Maximum Baseline Backtest on Actual Raw Target (`actual_target`) ---
                if method == self.methods[0]:
                    logger.info(f"\n--- STEP 5: Running Theoretical Maximum Baseline on ACTUAL RAW TARGET ---")
                    try:
                        if "actual_target" in predictions_df.columns:
                            act_target = predictions_df["actual_target"].values
                            if self.model_task == "regression":
                                # Exactly synchronize with model_evaluator threshold
                                perfect_sig = np.where(act_target > model_evaluator.threshold, 1, np.where(act_target < -model_evaluator.threshold, -1, 0))
                            else:
                                perfect_sig = act_target.astype(int)

                            perfect_signals_df = pd.DataFrame({
                                "timestamp": predictions_df["timestamp"].values,
                                "signal": perfect_sig,
                            })

                            baseline_csv_name = f"{clean_sym}_ACTUAL_TARGET_PERFECT_ledger.csv"
                            baseline_csv_path = self.output_dirs["backtest_ledgers"] / baseline_csv_name

                            bt_base_res = backtester.run_preprocessing_backtest(
                                ohlcv_df=raw_df,
                                signals_df=perfect_signals_df,
                                method="none (actual_target)",
                                model="PERFECT_FORESIGHT_BASELINE",
                                model_metrics={"accuracy" if self.model_task == "classification" else "r2": 1.0},
                                output_csv_path=baseline_csv_path,
                            )
                            leaderboard_rows.append(bt_base_res["summary"])
                    except Exception as e:
                        logger.error(f"[{clean_sym}] Error evaluating actual target baseline: {e}", exc_info=True)

            # --- STEP 6: Save and Print Master Leaderboard for this Symbol ---
            symbol_leaderboard = pd.DataFrame(leaderboard_rows)
            leaderboard_csv_path = self.output_dirs["backtest_ledgers"] / f"{clean_sym}_MASTER_LEADERBOARD.csv"
            symbol_leaderboard.to_csv(leaderboard_csv_path, index=False, encoding="utf-8")
            logger.info(f"\n[{clean_sym}] Saved Master Comparative Leaderboard to: {leaderboard_csv_path}")

            leaderboard_by_symbol[clean_sym] = symbol_leaderboard

            print("\n" + "=" * 80)
            print(f" FINAL PREPROCESSING LEADERBOARD FOR [{clean_sym}] | TASK: {self.model_task.upper()}")
            print("=" * 80)
            print(symbol_leaderboard.to_string(index=False))
            print("=" * 80 + "\n")

        return leaderboard_by_symbol


if __name__ == "__main__":
    app = PreprocessingMain()
    app.run_full_benchmark()
