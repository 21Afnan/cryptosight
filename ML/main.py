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


def orchestrate_ml_pipeline(config_path: str | Path = None) -> dict[str, pd.DataFrame]:
    """
    Orchestrates the complete end-to-end ML pipeline:
    1. Dataset Generation & Feature Engineering
    2. Chronological Splitting & Preprocessing
    3. Model Training based on `model_type` (classification / regression / timeseries)
    4. Backtesting on Validation/Test Signals & Quant Metric Computation
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "ml_config.yaml"

    # Execute the unified ML dataset generation pipeline
    datasets = get_ml_dataset(config_path)
    
    # Confirm CSV generation and storage locations (ml/csv_files directory)
    out_dir = Path(__file__).resolve().parent / "csv_files"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("  QUANT ML PIPELINE EXPORT SUMMARY")
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
        preproc_path = preprocessor.save()
        print(f"  [{sym}] Saved preprocessor scaler joblib to {preproc_path}")

        # 3. Save preprocessed DataFrames to CSV files
        train_prep_path = out_dir / f"{clean_sym}_{clean_tf}_train_preprocessed.csv"
        val_prep_path = out_dir / f"{clean_sym}_{clean_tf}_validation_preprocessed.csv"
        test_prep_path = out_dir / f"{clean_sym}_{clean_tf}_test_preprocessed.csv"
        
        out_dir.mkdir(parents=True, exist_ok=True)  # Guarantee directory exists before write
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
                    # Save each model's backtest ledger CSV cleanly inside ml/csv_files/classification/backtest_ledger/
                    bt_ledger_dir = Path(__file__).resolve().parent / "csv_files" / model_type / "backtest_ledger"
                    bt_ledger_dir.mkdir(parents=True, exist_ok=True)
                    ledger_save_path = bt_ledger_dir / f"{clean_sym}_{model_name}_ledger.csv"
                    ledger.to_csv(ledger_save_path, index=False, encoding="utf-8")
                    print(f"  [{model_name}] Saved Backtest Ledger CSV -> {ledger_save_path}")

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
            
            # ── SAVE ONE MASTER SEQUENCED PIPELINE JSON ──────────────────────────
            # All other saves (classification_run.yaml/.json, all_metadata.json)
            # are already done inside train_classifiers.py. This is the single
            # authoritative record: every stage in chronological execution order.
            if run_meta:
                import yaml as _yaml, json as _json
                inf_cfg_path = Path(__file__).resolve().parent / "inference" / "config.yaml"
                back_cfg_path = Path(__file__).resolve().parent.parent / "backtesting" / "backt_config.yaml"

                inf_cfg_data = {}
                back_cfg_data = {}
                if inf_cfg_path.exists():
                    try:
                        with open(inf_cfg_path, "r", encoding="utf-8") as _f:
                            inf_cfg_data = _yaml.safe_load(_f) or {}
                    except Exception:
                        pass
                if back_cfg_path.exists():
                    try:
                        with open(back_cfg_path, "r", encoding="utf-8") as _f:
                            back_cfg_data = _yaml.safe_load(_f) or {}
                    except Exception:
                        pass

                quant_pipeline_run = {
                    "1_dataset_info": {
                        "symbol": clean_sym,
                        "exchange": config.get("data", {}).get("exchange", "binance"),
                        "base_timeframe": config.get("data", {}).get("timeframe", "1m"),
                        "target_timeframe": clean_tf,
                        "total_dataset_rows": len(df),
                        "features_generated_count": len([c for c in df.columns if c not in ["timestamp", "target"]]),
                        "raw_features_csv": str(raw_csv_path)
                    },
                    "2_preprocessing_info": {
                        "train_ratio": train_ratio,
                        "val_ratio": val_ratio,
                        "test_ratio": test_ratio,
                        "train_rows": len(train_df),
                        "validation_rows": len(val_df),
                        "test_rows": len(test_df),
                        "scaler_joblib_path": str(preproc_path),
                        "train_preprocessed_csv": str(train_prep_path),
                        "validation_preprocessed_csv": str(val_prep_path),
                        "test_preprocessed_csv": str(test_prep_path)
                    },
                    "3_classification_and_backtesting": run_meta,
                    "4_system_configs": {
                        "ml_config": config,
                        "backtesting_config": back_cfg_data,
                        "inference_config": inf_cfg_data
                    }
                }

                master_json_path = config_dir / f"{clean_sym}_{clean_tf}_quant_pipeline.json"
                try:
                    with open(master_json_path, "w", encoding="utf-8") as mj:
                        _json.dump(quant_pipeline_run, mj, indent=4, default=str)
                    print(f"\n✨ Master Quant Pipeline JSON -> {master_json_path}")
                except Exception as e_mj:
                    print(f"  Warning: Could not save master quant pipeline JSON: {e_mj}")

                # ── STEP 6: RUN INFERENCE ON TEST SET RANGE & COMPARE ────────────
                # We already saved {SYM}_{MODEL}_test_predicted.csv during training.
                # Now run inference on the SAME timestamps (2026-04-09 → 2026-06-30)
                # and merge both on timestamp → comparison CSV per model.
                print(f"\n--- RUNNING INFERENCE ON TEST SET RANGE FOR COMPARISON ---")
                try:
                    from cryptosight.ml.inference.inference_pipeline import InferencePipeline
                    inf_engine = InferencePipeline(config_path=config_path)
                    inference_results = inf_engine.predict()

                    # Comparison output directory
                    compare_dir = Path(__file__).resolve().parent / "csv_files" / model_type / "test_vs_inference"
                    compare_dir.mkdir(parents=True, exist_ok=True)

                    test_pred_dir = Path(__file__).resolve().parent / "csv_files" / model_type / "model_predicted"

                    for model_name in val_predictions.keys():
                        # Load test predictions saved during training
                        test_csv = test_pred_dir / f"{clean_sym}_{model_name}_test_predicted.csv"
                        inf_key = f"{clean_sym}_{model_name}"

                        if not test_csv.exists():
                            print(f"  [{model_name}] test_predicted.csv not found, skipping.")
                            continue
                        if inf_key not in inference_results:
                            print(f"  [{model_name}] inference result not found, skipping.")
                            continue

                        test_df_cmp = pd.read_csv(test_csv, parse_dates=["timestamp"])
                        test_df_cmp["timestamp"] = pd.to_datetime(test_df_cmp["timestamp"], utc=True)

                        inf_df = inference_results[inf_key][["timestamp", "signal"]].copy()
                        inf_df["timestamp"] = pd.to_datetime(inf_df["timestamp"], utc=True)
                        inf_df.rename(columns={"signal": "inference_signal"}, inplace=True)

                        # Merge on exact timestamp — inner join keeps only matching rows
                        merged = pd.merge(
                            test_df_cmp[["timestamp", "actual", "predicted"]],
                            inf_df,
                            on="timestamp",
                            how="inner"
                        )
                        merged["match"] = merged["predicted"] == merged["inference_signal"]
                        match_pct = merged["match"].mean() * 100 if len(merged) > 0 else 0.0

                        cmp_path = compare_dir / f"{clean_sym}_{model_name}_test_vs_inference.csv"
                        merged.to_csv(cmp_path, index=False, encoding="utf-8")
                        print(f"  [{model_name}] Test vs Inference: {len(merged)} rows matched | Agreement: {match_pct:.2f}% -> {cmp_path}")

                except Exception as e_inf:
                    print(f"  Warning: Inference comparison failed: {e_inf}")
                
        elif model_type == "regression":
            print(f"\n--- model_type is REGRESSION (Milestone to be implemented next) ---")
        elif model_type == "timeseries":
            print(f"\n--- model_type is TIMESERIES (Milestone to be implemented next) ---")
        else:
            print(f"\nWarning: Unknown model_type [{model_type}] configured.")
            
    return datasets


if __name__ == "__main__":
    orchestrate_ml_pipeline()

