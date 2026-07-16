from pathlib import Path
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config
from cryptosight.ml.preprocessing.features import MLFeatureBuilder
logger = get_logger("MLMain")

def get_ml_dataset(config_path: str | Path = None) -> dict[str, pd.DataFrame]:
    """
    ONE unified entry point returning clean, fully engineered and target-labeled DataFrames.
    Loads `ml_config.yaml` once from disk and passes the loaded dictionary `config` to `MLFeatureBuilder`.
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
    return datasets


if __name__ == "__main__":
    # Execute the unified ML dataset generation pipeline
    datasets = get_ml_dataset()
    
    # Confirm CSV generation and storage locations (Project Root's csv_files directory)
    out_dir = Path(__file__).resolve().parent.parent / "csv_files"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("  QUANT ML PIPELINE EXPORT SUMMARY")
    config_path = Path(__file__).resolve().parent / "ml_config.yaml"
    config = load_config(config_path)
    clean_tf = str(config.get("data").get("target_timeframe")).strip()

    from cryptosight.ml.data.data_splitter import split_data_chronological
    from cryptosight.ml.preprocessing.preproc import QuantPreprocessor

    for sym, df in datasets.items():
        clean_sym = str(sym).upper().strip()
        
        # Save raw features dataset
        raw_csv_path = out_dir / f"{clean_sym}_{clean_tf}_features.csv"
        df.to_csv(raw_csv_path, index=False, encoding="utf-8")
        print(f"  [{sym}] Successfully generated & saved freshest ML features -> {raw_csv_path} (Rows: {len(df)})")
        
        # 1. Get split ratios from config and split dataset chronologically
        split_cfg = config.get("splitting", {})
        train_ratio = float(split_cfg.get("train_ratio", 0.70))
        val_ratio = float(split_cfg.get("val_ratio", 0.15))
        test_ratio = float(split_cfg.get("test_ratio", 0.15))

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
        preproc_path = preprocessor.save()
        print(f"  [{sym}] Saved preprocessor scaler joblib to {preproc_path}")

        # 3. Save preprocessed DataFrames to CSV files
        train_prep_path = out_dir / f"{clean_sym}_{clean_tf}_train_preprocessed.csv"
        val_prep_path = out_dir / f"{clean_sym}_{clean_tf}_validation_preprocessed.csv"
        test_prep_path = out_dir / f"{clean_sym}_{clean_tf}_test_preprocessed.csv"
        
        train_prep.to_csv(train_prep_path, index=False, encoding="utf-8")
        val_prep.to_csv(val_prep_path, index=False, encoding="utf-8")
        test_prep.to_csv(test_prep_path, index=False, encoding="utf-8")
        
        print(f"  [{sym}] Saved preprocessed datasets:")
        print(f"    - Train preprocessed      -> {train_prep_path}")
        print(f"    - Validation preprocessed -> {val_prep_path}")
        print(f"    - Test preprocessed       -> {test_prep_path}")

        # 4. Dynamically run model training pipeline based on model_type
        model_type = config.get("model_type", "classification").lower()
        if model_type == "classification":
            print(f"\n--- Running TRADITIONAL ML CLASSIFICATION for {sym} ---")
            from cryptosight.ml.models.classification.train_classifiers import ClassifierPipeline
            pipeline = ClassifierPipeline(config)
            val_predictions = pipeline.train(train_prep, val_prep, test_prep)
        elif model_type == "regression":
            print(f"\n--- model_type is REGRESSION (Milestone to be implemented next) ---")
        elif model_type == "timeseries":
            print(f"\n--- model_type is TIMESERIES (Milestone to be implemented next) ---")
        else:
            print(f"\nWarning: Unknown model_type [{model_type}] configured.")

