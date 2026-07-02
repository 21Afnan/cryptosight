import os
import yaml
import pandas as pd
from cryptosight.tal_Indicators.indicators import apply_indicators_from_config
from cryptosight.signals.conditions import ConditionEvaluator
from cryptosight.signals.rules import RulesEvaluator
from cryptosight.utils.logger import get_logger

logger = get_logger("SignalsMain")


def run_signals_pipeline(df: pd.DataFrame, indicator_config: dict, strategy_config: dict) -> pd.DataFrame:
    """
    Master signals pipeline: Calculates indicators, evaluates conditions, and generates signals.

    Args:
        df:               OHLCV DataFrame (already downloaded/loaded).
        indicator_config: Indicators dictionary (from strategy_config.yaml -> "indicators").
        strategy_config:  Strategy dictionary (from strategy_config.yaml -> "strategy").

    Returns:
        DataFrame with OHLCV + shifted indicators + shifted conditions + shifted signals.
    """
    if df.empty:
        logger.error("Empty DataFrame received. Pipeline aborted.")
        return pd.DataFrame()

    # 1. Calculate indicators (shifted by 1 inside apply_indicators_from_config)
    logger.info("Calculating Indicators...")
    merged_df = apply_indicators_from_config(df, indicator_config)

    # 2. Evaluate conditions
    logger.info("Evaluating Conditions...")
    evaluator = ConditionEvaluator(merged_df)
    conditions_df = evaluator.process_strategy(strategy_config)

    # 3. Shift conditions by 1 to prevent look-ahead bias (condition on bar T -> act on bar T+1)
    conditions_df = conditions_df.shift(1).dropna().astype(bool)
    merged_df = pd.concat([merged_df, conditions_df], axis=1, join="inner")

    # 4. Generate signals from rules
    logger.info("Generating Signals...")
    rules = RulesEvaluator(conditions_df, strategy_config)
    final_signal = rules.generate_signals()

    # 5. Shift signal by 1 to prevent look-ahead bias (signal on bar T -> execute on bar T+1)
    final_signal = final_signal.shift(1).dropna().astype(int)
    merged_df["signal"] = final_signal

    # 6. Drop NaN rows resulting from indicator calculation periods and shifts
    merged_df.dropna(inplace=True)
    merged_df["signal"] = merged_df["signal"].astype(int)

    logger.info(f"Pipeline complete — {len(merged_df)} rows, {(final_signal != 0).sum()} active signals.")
    return merged_df


if __name__ == "__main__":
    from cryptosight.data.downloader import Downloader
    from cryptosight.utils.config import load_config

    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_config_path = os.path.join(current_dir, "..", "data", "binance", "config.yaml")
    strategy_config_path = os.path.join(current_dir, "strategy_config.yaml")

    # 1. Load Data Config & Download OHLCV
    data_cfg = load_config(data_config_path)
    dl = Downloader(
        exchange=data_cfg["exchange"],
        symbol=data_cfg["symbols"][0],
        timeframe=data_cfg.get("target_timeframe", data_cfg["timeframe"]),
    )
    ohlcv_df = dl.get_data(
        start_time=data_cfg["start_time"],
        end_time=data_cfg["end_time"],
        max_retries=data_cfg.get("max_retries", 5),
        retry_delay=data_cfg.get("retry_delay", 3),
    )

    # 2. Load Strategy Config (Indicators & Strategy rules dictionaries)
    with open(strategy_config_path, "r") as f:
        strat_file = yaml.safe_load(f)
    indicator_config = strat_file.get("indicators", {})
    strategy_config = strat_file.get("strategy", {})

    # 3. Run Pipeline
    print("=" * 50)
    print("  RUNNING SIGNALS PIPELINE TEST")
    print("=" * 50)

    final_df = run_signals_pipeline(ohlcv_df, indicator_config, strategy_config)

    if final_df.empty:
        print("[FAILED] Pipeline returned empty DataFrame.")
    else:
        print(f"\n[SUCCESS] Pipeline returned {len(final_df)} rows.")
        display_cols = [c for c in ["close", "ind_sma_20", "long_cond_1", "short_cond_1", "signal"] if c in final_df.columns]
        print(final_df[display_cols].tail(15))

        output_path = os.path.join(current_dir, "signals_pipeline_output.csv")
        try:
            final_df.to_csv(output_path)
            print(f"\nSaved to: {output_path}")
        except PermissionError:
            print(f"\n[WARNING] Could not save to {output_path} because the file is open in another program (e.g. Excel). Close it to overwrite.")
