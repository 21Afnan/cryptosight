from pathlib import Path
import pandas as pd
from cryptosight.utils.logger import get_logger

logger = get_logger("RegressionSignals")

def generate_regression_signals(predictions_dict: dict, config: dict, symbol: str, model_thresholds: dict = None):
    """
    Takes the in-memory dictionary of test predictions directly from the ML pipeline,
    applies the threshold, and saves discrete signals (1, 0, -1) to the signals folder.
    
    predictions_dict: dict mapping model_name to its test prediction DataFrame.
    model_thresholds: optional dict mapping model_name -> threshold (auto-computed if not provided).
    """
    exchange = str(config.get("data", {}).get("exchange")).lower().strip()
    tf = str(config.get("data", {}).get("target_timeframe")).lower().strip()
    global_threshold = float(config.get("regression", {}).get("signal_threshold"))
    clean_sym = str(symbol).upper().strip()

    base_dir = Path(__file__).resolve().parent.parent / "csv_files" / "regression"
    signal_dir = base_dir / "signals"
    signal_dir.mkdir(parents=True, exist_ok=True)

    if not predictions_dict:
        logger.info("No predictions passed to signal generator.")
        return {}

    logger.info(f"[{clean_sym}] Generating signals for {len(predictions_dict)} models...")

    signals_returned = {}

    for model_name, df in predictions_dict.items():
        try:
            if "predicted_target" not in df.columns:
                logger.warning(f"Skipping {model_name}: 'predicted_target' column missing.")
                continue

            # Use per-model auto-threshold if provided, else fall back to config global threshold
            threshold = model_thresholds.get(model_name, global_threshold) if model_thresholds else global_threshold
            logger.info(f"  [{model_name}] Threshold: {threshold:.6f}")

            # Generate signals in-memory
            df_signal = df.copy()
            df_signal["signal"] = 0
            df_signal.loc[df_signal["predicted_target"] > threshold, "signal"] = 1
            df_signal.loc[df_signal["predicted_target"] < -threshold, "signal"] = -1

            signal_file = f"{exchange}_{clean_sym}_{tf}_regression_{model_name}_signals.csv"

            # Save only timestamp and signal
            out_df = df_signal[["timestamp", "signal"]].copy()
            out_df.to_csv(signal_dir / signal_file, index=False, encoding="utf-8")
            logger.info(f" -> Saved {signal_file} | Buys: {(out_df['signal']==1).sum()} | Sells: {(out_df['signal']==-1).sum()} | Holds: {(out_df['signal']==0).sum()}")

            # Prepare for backtester (timestamp as index)
            out_df["timestamp"] = pd.to_datetime(out_df["timestamp"], utc=True)
            out_df.set_index("timestamp", inplace=True)
            signals_returned[model_name] = out_df

        except Exception as e:
            logger.error(f"Error generating signals for {model_name}: {e}")

    return signals_returned
