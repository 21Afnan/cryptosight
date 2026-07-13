import pandas as pd 
from pathlib import Path
import yaml
from cryptosight.utils.logger import get_logger
from cryptosight.ml.main import get_ml_dataset
from cryptosight.preprocessing.models import CryptoMLClassifier


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

        benchmark_df = classifier.run_preprocessing_comparison(df)

        # 4. Display Final Benchmark Table (`PDF Step 5 & 6 Institutional Report`)
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
        print(benchmark_df[available_cols].to_string(index=False))
        print("=" * 105 + "\n")

        # Save benchmark report to CSV for project records
        clean_sym = str(symbol).upper().replace("/", "_").replace(":", "_").replace("\\", "_").strip()
        report_path = Path(__file__).resolve().parent / f"{clean_sym}_preprocessing_benchmark_report.csv"
        try:
            benchmark_df.to_csv(report_path, index=False, encoding="utf-8")
            logger.info(f"Saved complete benchmark report table to: {report_path}")
        except OSError as e:
            fallback_path = Path(__file__).resolve().parent / f"benchmark_{clean_sym}.csv"
            benchmark_df.to_csv(fallback_path, index=False, encoding="utf-8")
            logger.info(f"Saved fallback benchmark report table to: {fallback_path}")


if __name__ == "__main__":
    run_pipeline()
