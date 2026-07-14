import pandas as pd
from pathlib import Path
import yaml
from cryptosight.utils.logger import get_logger
from cryptosight.ml.main import get_ml_dataset
from cryptosight.preprocessing.models import CryptoMLClassifier
from cryptosight.preprocessing.stationarity import StationarityAnalyzer
from cryptosight.preprocessing.trend_preservation import TrendPreservationAnalyzer
from cryptosight.preprocessing.backtest_runner import run_preprocessing_backtest_leaderboard


logger = get_logger("PreprocessingMain")


def run_pipeline():
    print("\n" + "=" * 95)
    print(" CRYPTOSIGHT QUANTITATIVE PREPROCESSING vs ML EVALUATION PIPELINE (`main.py`)")
    print("=" * 95)

    # 1. Load config
    config_path = Path(__file__).resolve().parent / "pp.config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # 2. Fetch Real ML Datasets (`features.csv` with Look-Ahead bias protection from `cryptosight.ML`)
    logger.info("Calling `cryptosight.ML.main.get_ml_dataset()` to fetch engineered features...")
    datasets = get_ml_dataset()

    if not datasets:
        logger.error("No dataset returned from ML module! Check `cryptosight/ML/` pipeline.")
        return

    classifier = CryptoMLClassifier(config)

    # 3. Loop across every crypto symbol (e.g. 'btc', 'eth') and run comparison
    for symbol, df in datasets.items():
        print(f"\n [Symbol: {symbol.upper()}] Loaded {len(df)} candles | Target Distribution: {df['target'].value_counts().to_dict()}")
        logger.info(f"Starting Preprocessing vs ML Evaluation loop for symbol [{symbol.upper()}]...")

        # 4. Run ML Evaluation, Leaderboard & Signal Generation (`PDF Step 6 & 7.1`)
        benchmark_df, preprocessed_dfs, predictions_dfs = classifier.run_preprocessing_comparison(df, symbol=symbol)

        # Display Final Benchmark Table (`PDF Step 6 Institutional Report`)
        print("\n" + "=" * 105)
        print(f"🏆 FINAL BENCHMARK TABLE FOR [{symbol.upper()}] (`Top Preprocessing Technique vs ML Model`)")
        print("=" * 105)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        cols_to_show = [
            "method",
            "model",
            "accuracy_pct",
            "correct_predictions",
            "wrong_predictions",
            "f1_score_pct",
            "log_loss",
        ]
        available_cols = [c for c in cols_to_show if c in benchmark_df.columns]
        if not benchmark_df.empty:
            print(benchmark_df[available_cols].to_string(index=False))
        print("=" * 105 + "\n")

        clean_sym = str(symbol).upper().replace("/", "_").replace(":", "_").replace("\\", "_").strip()
        target_tf = str(config.get("data", {}).get("target_timeframe", "15m")).replace("/", "_").replace(":", "_").strip()
        csv_dir = Path(__file__).resolve().parent.parent / "csv_files"
        csv_dir.mkdir(parents=True, exist_ok=True)

        # Save all 7 preprocessed dataset CSVs (`BTC_15m_robust.csv`, etc.)
        for method_name, full_df in preprocessed_dfs.items():
            dataset_path = csv_dir / f"{clean_sym}_{target_tf}_{method_name}.csv"
            try:
                full_df.to_csv(dataset_path, index=False, encoding="utf-8-sig")
                logger.info(f"[{clean_sym}] Saved preprocessed CSV ({method_name.upper()}) to `csv_files/` | Shape: {full_df.shape}")
            except Exception as e:
                logger.warning(f"[{clean_sym}] Could not save preprocessed CSV ({method_name.upper()}): {e}")

        # Save benchmark evaluation report table
        report_path = csv_dir / f"{clean_sym}_preprocessing_benchmark_report.csv"
        if not benchmark_df.empty:
            try:
                benchmark_df.to_csv(report_path, index=False, encoding="utf-8-sig")
                logger.info(f"Saved complete benchmark report table to `csv_files/`: {report_path}")
            except Exception as e:
                logger.warning(f"Could not save benchmark report: {e}")

        # Save Model Predictions & Signals (`+1, 0, -1 with actual vs predicted targets`)
        for method_name, pred_df in predictions_dfs.items():
            pred_path = csv_dir / f"{clean_sym}_{target_tf}_{method_name}_model_predictions.csv"
            try:
                pred_df.to_csv(pred_path, index=False, encoding="utf-8-sig")
                logger.info(f"[{clean_sym}] Saved Model Predictions & Signals ({method_name.upper()}) to `csv_files/`: {pred_path}")
            except Exception as e:
                logger.warning(f"[{clean_sym}] Could not save model prediction CSV ({method_name.upper()}): {e}")

        # Print Sample of Signal Generation Output for Visual Verification
        # New key format is 'method_modelname' (e.g. 'minmax_xgboost') after Bug #2 fix
        best_method_name = benchmark_df.iloc[0]["method"].lower() if not benchmark_df.empty else "none"
        best_model_name = benchmark_df.iloc[0]["model"].lower() if not benchmark_df.empty else "xgboost"
        best_key = f"{best_method_name}_{best_model_name}"
        if best_key in predictions_dfs:
            print("\n" + "=" * 105)
            print(f"📡 MODEL SIGNAL GENERATION SAMPLE (`Method: {best_method_name.upper()} | Model: {best_model_name.upper()}` — Actual vs Predicted Targets & +1/0/-1 Signals)")
            print("=" * 105)
            sample_cols = [c for c in ["timestamp", "actual_target", "predicted_target", "is_correct", "predicted_prob", "signal", "close"] if c in predictions_dfs[best_key].columns]
            print(predictions_dfs[best_key][sample_cols].tail(10).to_string(index=False))
            print("=" * 105 + "\n")

        # 5. Run Step 8 & Step 9: Built-in Backtesting Engine Execution & Leaderboard (`PnL, Sharpe, Sortino across all Techniques`)
        backtest_leaderboard_df = run_preprocessing_backtest_leaderboard(df, predictions_dfs, symbol=symbol)
        if not backtest_leaderboard_df.empty:
            print("\n" + "=" * 115)
            print(f"🏆 FINAL STEP 8 & 9 INSTITUTIONAL BACKTESTING LEADERBOARD FOR [{symbol.upper()}] (`Top Preprocessing Technique by PnL & Sharpe`)")
            print("=" * 115)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", 1000)
            print(backtest_leaderboard_df.to_string(index=False))
            print("=" * 115 + "\n")

        # 6. Build Master Final Summary Table combining ML Classification & Backtesting Profit/Loss (`Easy & Understandable Summary`)
        if not benchmark_df.empty and not backtest_leaderboard_df.empty:
            master_df = pd.merge(benchmark_df, backtest_leaderboard_df, on=["method", "model"], how="outer")
            
            # Rename columns to super friendly, crystal clear names (`As requested: easy weasy profit/loss + precision/accuracy`)
            master_df.rename(columns={
                "method": "preprocessing_method",
                "model": "model_type",
                "accuracy_pct": "ml_accuracy_pct",
                "precision_pct": "ml_precision_pct",
                "f1_score_pct": "ml_f1_score_pct",
                "status": "final_status"
            }, inplace=True)

            desired_summary_cols = [
                "preprocessing_method", "model_type", "final_status", 
                "total_profit_usd", "total_loss_usd", "net_profit_usd", 
                "return_pct", "win_rate_pct", "total_trades", "winning_trades", "losing_trades",
                "ml_accuracy_pct", "ml_precision_pct", "ml_f1_score_pct"
            ]
            ordered_cols = [c for c in desired_summary_cols if c in master_df.columns]
            master_df = master_df[ordered_cols]

            # Print Master Summary to Console
            print("\n" + "=" * 125)
            print(f"🌟 FINAL INSTITUTIONAL SUMMARY MASTER TABLE (`ML Classification + Backtest Profitability`) FOR [{symbol.upper()}]")
            print("=" * 125)
            print(master_df.to_string(index=False))
            print("=" * 125 + "\n")

            # Save to root csv_files/ folder
            master_csv_path = csv_dir / f"{clean_sym}_final_summary_master_table.csv"
            try:
                master_df.to_csv(master_csv_path, index=False, encoding="utf-8-sig")
                logger.info(f"Saved Final Summary Master Table to `csv_files/`: {master_csv_path}")
            except Exception as e:
                logger.warning(f"Could not save final summary table: {e}")

        # --- Stationarity & Trend Preservation Commented out (`As requested, running JUST fast Model Signal Generation`) ---
        # # 6. Run PDF Step 4: Stationarity Analysis (`ADF, KPSS, Autocorrelation`) directly inside `main.py`
        # analyzer = StationarityAnalyzer(config)
        # stationarity_df = analyzer.evaluate_preprocessed_datasets(preprocessed_dfs)
        # 
        # if not stationarity_df.empty:
        #     print("\n" + "=" * 105)
        #     print(f"🔬 FINAL STATIONARITY & MEMORY TABLE FOR [{symbol.upper()}] (`PDF Step 4 Institutional Report`)")
        #     print("=" * 105)
        #     print(stationarity_df.to_string(index=False))
        #     print("=" * 105 + "\n")
        #
        #     stat_report_path = csv_dir / f"{clean_sym}_stationarity_analysis_report.csv"
        #     try:
        #         stationarity_df.to_csv(stat_report_path, index=False, encoding="utf-8-sig")
        #         logger.info(f"Saved stationarity & memory report to `csv_files/`: {stat_report_path}")
        #     except Exception as e:
        #         logger.warning(f"Could not save stationarity report: {e}")
        #
        # # 7. Run PDF Step 5: Trend Preservation Analysis (`Long-Term Macro & Local Breakouts`) directly inside `main.py`
        # trend_analyzer = TrendPreservationAnalyzer(config)
        # trend_df = trend_analyzer.evaluate_preprocessed_datasets(preprocessed_dfs)
        #
        # if not trend_df.empty:
        #     print("\n" + "=" * 105)
        #     print(f"📈 FINAL TREND PRESERVATION TABLE FOR [{symbol.upper()}] (`PDF Step 5 Institutional Report`)")
        #     print("=" * 105)
        #     print(trend_df.to_string(index=False))
        #     print("=" * 105 + "\n")
        #
        #     trend_report_path = csv_dir / f"{clean_sym}_trend_preservation_report.csv"
        #     try:
        #         trend_df.to_csv(trend_report_path, index=False, encoding="utf-8-sig")
        #         logger.info(f"Saved trend preservation report to `csv_files/`: {trend_report_path}")
        #     except Exception as e:
        #         logger.warning(f"Could not save trend preservation report: {e}")


if __name__ == "__main__":
    run_pipeline()
