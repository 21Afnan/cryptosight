import yaml
import os
import pandas as pd
from cryptosight.data.downloader import Downloader
from cryptosight.tal_Indicators.indicators import Indicators, apply_indicators_from_config
from cryptosight.signals.conditions import ConditionEvaluator
from cryptosight.signals.rules import RulesEvaluator
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_strategy_config

logger = get_logger("SignalsMain")

def run_signals_pipeline(df: pd.DataFrame, config_path: str) -> pd.DataFrame:
    """
    Master pipeline: Reads OHLCV, calculates required indicators, evaluates conditions, and generates signals.
    """
    # 1. Load strategy_config.yaml
    config = load_strategy_config(config_path)
    indicator_config = config.get("indicators", {})
    strategy_config = config.get("strategy", {})
    
    # 2. Receive OHLCV data & Calculate indicators based on config
    logger.info("Calculating Indicators...")
    merged_df = apply_indicators_from_config(df, indicator_config)
    
    # 3. Pass data + strategy config to conditions.py
    logger.info("Evaluating Conditions...")
    evaluator = ConditionEvaluator(merged_df)
    conditions_df = evaluator.process_strategy(strategy_config)
    
    # Merge the True/False columns into the main dataframe so they show in CSV
    merged_df = pd.concat([merged_df, conditions_df], axis=1)
    
    # 4. Pass result to rules.py
    logger.info("Processing Rules to generate Final Signals...")
    rules = RulesEvaluator(conditions_df, strategy_config)
    final_signal = rules.generate_signals()
    
    # 5. Return final signal array (Adding it to the main dataframe for clarity)
    merged_df["signal"] = final_signal
    return merged_df

if __name__ == "__main__":
    from cryptosight.data.downloader import Downloader
    
    # Test the entire pipeline
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_dir, "strategy_config.yaml")
    
    # Receive OHLCV Data
    print("Downloading recent ByBit data for test...")
    dl = Downloader(exchange="bybit", symbol="btc", timeframe="1m")
    ohlcv_df = dl.get_data(start_time="2026-06-25 00:00:00", end_time="now", max_retries=5, retry_delay=3)
    ohlcv_df = ohlcv_df.tail(1000) # Use recent 1000 candles to give MACD/EMA time to calculate
    
    # Run the Pipeline
    print("\nStarting Signals Module Pipeline...")
    final_df = run_signals_pipeline(ohlcv_df, config_file)
    
    print("\n=========================================")
    print("      PIPELINE COMPLETED SUCCESSFULLY      ")
    print("=========================================\n")
    
    # Print the last 15 rows to verify signals
    # We only print essential columns to keep the terminal output clean
    display_cols = ["close", "ind_EMA_20", "ind_RSI_14", "long_cond_1", "long_cond_2", "signal"]
    print(final_df[display_cols].tail(15))
    
    # Save everything to CSV
    output_path = os.path.join(current_dir, "signals_pipeline_output.csv")
    final_df.to_csv(output_path)
    print(f"\n[+] Full results saved to: {output_path}")
