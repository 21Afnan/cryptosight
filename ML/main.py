from pathlib import Path
import json
import yaml
import pandas as pd

from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config, get_ml_artifacts_dir
from cryptosight.ml.preprocessing.features import MLFeatureBuilder
from cryptosight.ml.data.data_splitter import split_data_chronological
from cryptosight.ml.preprocessing.preproc import QuantPreprocessor

logger = get_logger("MLMain")


def get_ml_dataset(config_path: str | Path = None) -> tuple[dict, dict[str, pd.DataFrame]]:
    """
    ONE unified entry point returning clean, fully engineered and target-labeled DataFrames.
    Loads `ml_config.yaml` once from disk and passes the loaded dictionary `config` to `MLFeatureBuilder`.
    Returns the loaded config alongside the datasets so callers don't need to reload it.
    """
    logger.info("Starting Cryptosight Quant ML Data Pipeline ")
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "ml_config.yaml"

    # Load config once from disk (`Single Source of Truth`)
    config = load_config(config_path)

    # Pass pure dictionary to MLFeatureBuilder (in-memory quant engine)
    builder = MLFeatureBuilder(config=config)
    datasets = builder.build_dataset()
    logger.info(" ML Data Pipeline Execution Complete ")
    return config, datasets


def orchestrate_ml_pipeline(config_path: str | Path = None) -> dict[str, pd.DataFrame]:
    """
    Orchestrates the complete end-to-end ML pipeline:
    1. Dataset Generation & Feature Engineering
    2. Chronological Splitting & Preprocessing
    3. Model Training based on `model_type` (classification / regression / timeseries)
    4. Backtesting on Validation/Test Signals & Quant Metric Computation
    """
    # Execute the unified ML dataset generation pipeline (config loaded exactly once)
    config, datasets = get_ml_dataset(config_path)

    out_dir = Path(__file__).resolve().parent / "csv_files"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("  QUANT ML PIPELINE EXPORT SUMMARY")
    clean_tf = str(config.get("data").get("target_timeframe")).strip()
    exchange = str(config.get("data", {}).get("exchange", "binance")).lower().strip()

    for sym, df in datasets.items():
        clean_sym = str(sym).upper().strip()

        # Save raw features dataset
        raw_csv_path = out_dir / f"{exchange}_{clean_sym}_{clean_tf}_features.csv"
        df.to_csv(raw_csv_path, index=False, encoding="utf-8")
        print(f"  [{sym}] Successfully generated & saved freshest ML features -> {raw_csv_path} (Rows: {len(df)})")

        # 1. Get split ratios from config and split dataset chronologically
        split_cfg = config.get("splitting", {})
        train_ratio = float(split_cfg.get("train_ratio"))
        val_ratio = float(split_cfg.get("val_ratio"))
        test_ratio = float(split_cfg.get("test_ratio"))

        train_df, val_df, test_df, split_info = split_data_chronological(
            df,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            config=config
        )

        # 2. Fit and transform using QuantPreprocessor
        preprocessor = QuantPreprocessor()
        preprocessor.fit(train_df)

        # Transform train, val, and test datasets in-place (no data leakage)
        train_prep = preprocessor.transform(train_df)
        val_prep = preprocessor.transform(val_df)
        test_prep = preprocessor.transform(test_df)

        # Save preprocessor joblib and YAML artifact config
        preproc_path = preprocessor.save(clean_sym, exchange, clean_tf)
        print(f"  [{sym}] Saved preprocessor scaler joblib to {preproc_path}")

        # 3. Save preprocessed DataFrames to CSV files
        out_dir.mkdir(parents=True, exist_ok=True)
        train_prep_path = out_dir / f"{exchange}_{clean_sym}_{clean_tf}_train_preprocessed.csv"
        val_prep_path = out_dir / f"{exchange}_{clean_sym}_{clean_tf}_validation_preprocessed.csv"
        test_prep_path = out_dir / f"{exchange}_{clean_sym}_{clean_tf}_test_preprocessed.csv"

        train_prep.to_csv(train_prep_path, index=False, encoding="utf-8")
        val_prep.to_csv(val_prep_path, index=False, encoding="utf-8")
        test_prep.to_csv(test_prep_path, index=False, encoding="utf-8")

        print(f"  [{sym}] Saved preprocessed datasets:")
        print(f"    - Train preprocessed      -> {train_prep_path}")
        print(f"    - Validation preprocessed -> {val_prep_path}")
        print(f"    - Test preprocessed       -> {test_prep_path}")

        # 4. Dynamically run model training pipeline based on model_type
        model_type = config.get("model_type", "classification").lower()

        if model_type in ["classification", "regression"]:
            print(f"\n--- Running TRADITIONAL ML {model_type.upper()} for {sym} ---")
            if model_type == "classification":
                from cryptosight.ml.models.classification.train_classifiers import ClassifierPipeline as PipelineClass
                model_key = "3_classification_models"
            else:
                from cryptosight.ml.models.regression.train_regressors import RegressorPipeline as PipelineClass
                model_key = "3_regression_models"

            pipeline = PipelineClass(config)
            val_predictions, run_meta = pipeline.train(train_prep, val_prep, test_prep)

            # ── SAVE ONE MASTER SEQUENCED PIPELINE JSON ──────────────────────────
            # This is the single unified JSON file storing each and everything related
            # to the model type selected and models (zero redundancy, zero YAML files).
            if run_meta:
                back_cfg_path = Path(__file__).resolve().parent.parent / "backtesting" / "backt_config.yaml"
                back_cfg_data = {}
                if back_cfg_path.exists():
                    try:
                        with open(back_cfg_path, "r", encoding="utf-8") as _f:
                            back_cfg_data = yaml.safe_load(_f) or {}
                    except Exception:
                        pass

                preproc_meta = preprocessor.get_metadata()
                quant_pipeline_run = {
                    "1_dataset_info": {
                        "symbol": clean_sym,
                        "exchange": exchange,
                        "base_timeframe": config.get("data").get("timeframe"),
                        "target_timeframe": clean_tf,
                        "start_date": config.get("data").get("start_date"),
                        "end_date": config.get("data").get("end_date"),
                        "total_dataset_rows": len(df),
                        "features_generated_count": len([c for c in df.columns if c not in ["timestamp", "target"]]),
                        "features_summary": split_info.get("features_summary")
                    },
                    "2_preprocessing_info": {
                        "splitting_ratios": {
                            "train_ratio": train_ratio,
                            "val_ratio": val_ratio,
                            "test_ratio": test_ratio
                        },
                        "chronological_splits": split_info.get("splits_summary"),
                        "scaler_joblib_path": str(preproc_path),
                        "preprocessor_parameters": preproc_meta
                    },
                    model_key: run_meta.get(clean_sym, run_meta),
                    "4_system_configs": {
                        "backtesting_config": back_cfg_data
                    }
                }

                config_dir = get_ml_artifacts_dir("config")
                master_json_path = config_dir / f"{exchange}_{clean_sym}_{clean_tf}_{model_type}.json"
                try:
                    with open(master_json_path, "w", encoding="utf-8") as mj:
                        json.dump(quant_pipeline_run, mj, indent=4, default=str)
                        print(f"  Master Pipeline JSON -> {master_json_path}")
                except Exception as e_mj:
                    print(f"  Warning: Could not save master pipeline JSON: {e_mj}")

                # ── STEP 7: GENERATE DISCRETE SIGNALS FOR BACKTESTER ──────────────
                if model_type == "regression":
                    try:
                        from cryptosight.ml.signals.regression_signals import generate_regression_signals
                        test_preds_only = {m: dfs["test"] for m, dfs in val_predictions.get(clean_sym, {}).items()}
                        generate_regression_signals(test_preds_only, config, clean_sym)
                    except Exception as e_sig:
                        print(f"  Could not generate regression signals: {e_sig}")

                # ── STEP 6: RUN INFERENCE ON TEST SET RANGE & COMPARE ────────────
                print(f"\n--- RUNNING INFERENCE ON TEST SET RANGE FOR COMPARISON ---")
                try:
                    from cryptosight.ml.inference.inference_pipeline import InferencePipeline
                    inf_engine = InferencePipeline(config_path=config_path)
                    inference_results = inf_engine.predict()

                    compare_dir = out_dir / model_type / "test_vs_inference"
                    compare_dir.mkdir(parents=True, exist_ok=True)

                    test_pred_dir = out_dir / model_type / "model_predicted"

                    for model_name, dfs in val_predictions.get(clean_sym, {}).items():
                        test_csv = test_pred_dir / f"{exchange}_{clean_sym}_{clean_tf}_{model_type}_{model_name}_test_predicted.csv"
                        inf_key = f"{clean_sym}_{model_name}"

                        if not test_csv.exists():
                            print(f"  [{model_name}] test_predicted.csv not found at {test_csv}, skipping.")
                            continue
                        if inf_key not in inference_results:
                            print(f"  [{model_name}] inference result not found, skipping.")
                            continue

                        test_df_cmp = pd.read_csv(test_csv, parse_dates=["timestamp"])
                        test_df_cmp["timestamp"] = pd.to_datetime(test_df_cmp["timestamp"], utc=True)

                        inf_df = inference_results[inf_key][["timestamp", "signal"]].copy()
                        inf_df["timestamp"] = pd.to_datetime(inf_df["timestamp"], utc=True)
                        inf_df.rename(columns={"signal": "inference_signal"}, inplace=True)

                        merged = pd.merge(
                            test_df_cmp[["timestamp", "actual", "predicted"]],
                            inf_df,
                            on="timestamp",
                            how="inner"
                        )
                        merged["match"] = merged["predicted"] == merged["inference_signal"]
                        match_pct = merged["match"].mean() * 100 if len(merged) > 0 else 0.0

                        cmp_path = compare_dir / f"{exchange}_{clean_sym}_{clean_tf}_{model_type}_{model_name}_test_vs_inference.csv"
                        merged.to_csv(cmp_path, index=False, encoding="utf-8")
                        print(f"  [{model_name}] Test vs Inference: {len(merged)} rows matched | Agreement: {match_pct:.2f}% -> {cmp_path}")

                except Exception as e_inf:
                    print(f"  Warning: Inference comparison failed: {e_inf}")

        elif model_type == "timeseries":
            print(f"\n--- model_type is TIMESERIES (Milestone to be implemented next) ---")
        else:
            print(f"\nWarning: Unknown model_type [{model_type}] configured.")

    return datasets


if __name__ == "__main__":
    orchestrate_ml_pipeline()
