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
            from cryptosight.ml.models.classification.train_classifiers import ClassifierPipeline, get_signals
            from cryptosight.backtesting.backtest import BacktestingEngine
            from cryptosight.stats.metrices import compute_all_metrics
            from cryptosight.utils.config import get_ml_artifacts_dir, save_config_artifact
            import json
            
            pipeline = ClassifierPipeline(config)
            val_predictions = pipeline.train(train_prep, val_prep, test_prep)
            
            # Load the classification config saved by pipeline.train() so we can update it
            config_dir = get_ml_artifacts_dir("config")
            run_config_path = config_dir / "classification_run.yaml"
            if run_config_path.exists():
                import yaml
                with open(run_config_path, "r", encoding="utf-8") as f:
                    run_meta = yaml.safe_load(f) or {}
            else:
                run_meta = {}

            print(f"\n--- RUNNING BACKTEST ON VALIDATION/TEST SIGNALS ---")
            for model_name, pred_df in val_predictions.items():
                print(f"\n>> Backtesting ML Model: {model_name.upper()}")
                
                # Extract clean signals with DatetimeIndex
                signal_df = get_signals(pred_df)
                
                # Instantiate backtester
                bt_engine = BacktestingEngine()
                
                # Override backtester config to match ML validation data window
                bt_engine.config["symbol"] = clean_sym.lower()
                bt_engine.config["start_time"] = str(signal_df.index.min())
                bt_engine.config["end_time"] = str(signal_df.index.max())
                
                # Run the pipeline injecting ML signals
                ledger = bt_engine.run_pipeline(external_signals_df=signal_df)
                
                # Print high-level results and compute stats
                if not ledger.empty:
                    final_balance = ledger["balance"].iloc[-1]
                    net_profit = final_balance - bt_engine.config['initial_balance']
                    print(f"  [{model_name}] Backtest Complete | Net Profit: ${net_profit:.2f} | Trades: {len(ledger)}")
                    
                    # Compute Trading Strategy Metrics on Returns
                    clean_ledger = ledger.copy()
                    if "exit_time" in clean_ledger.columns:
                        clean_ledger = clean_ledger.sort_values(by="exit_time")
                        clean_ledger["exit_time"] = pd.to_datetime(clean_ledger["exit_time"])
                        returns_series = clean_ledger.set_index("exit_time")["perc_pnl"]
                    else:
                        returns_series = clean_ledger["perc_pnl"]
                    
                    # Compute all metrics (suppress console output from quantstats)
                    try:
                        all_metrics = compute_all_metrics(returns_series, is_percentage=True, save_filepath=None)
                    except Exception as e:
                        print(f"  [{model_name}] Warning: Could not compute metrics: {e}")
                        all_metrics = {}
                        
                    trading_metrics = {
                        "sharpe_ratio": all_metrics.get("sharpe", 0.0),
                        "sortino_ratio": all_metrics.get("sortino", 0.0),
                        "calmar_ratio": all_metrics.get("calmar", 0.0),
                        "total_return": all_metrics.get("cagr", 0.0),
                        "profit_factor": all_metrics.get("profit_factor", 0.0),
                        "max_drawdown": all_metrics.get("max_drawdown", 0.0),
                        "win_rate": all_metrics.get("win_rate", 0.0)
                    }
                    
                    print("  [Trading Metrics]")
                    for k, v in trading_metrics.items():
                        print(f"    - {k:<15}: {v}")
                        
                    # Inject trading metrics into the saved classification config
                    if "leaderboard" in run_meta:
                        for entry in run_meta["leaderboard"]:
                            if entry.get("model") == model_name:
                                entry["trading_metrics"] = trading_metrics
                else:
                    print(f"  [{model_name}] Backtest Complete | No trades executed.")
            
            # Re-save the updated configuration
            if run_meta:
                save_config_artifact(run_meta, "classification_run.yaml", asset_type="config")
                print(f"\nSaved Trading Metrics to artifacts/configs/classification_run.yaml")
                
        elif model_type == "regression":
            print(f"\n--- model_type is REGRESSION (Milestone to be implemented next) ---")
        elif model_type == "timeseries":
            print(f"\n--- model_type is TIMESERIES (Milestone to be implemented next) ---")
        else:
            print(f"\nWarning: Unknown model_type [{model_type}] configured.")

