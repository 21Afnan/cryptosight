import os
import yaml
import pandas as pd
from cryptosight.tal_Indicators.indicators import apply_indicators_from_config
from cryptosight.signals.conditions import ConditionEvaluator
from cryptosight.signals.rules import RulesEvaluator
from cryptosight.utils.logger import get_logger
from cryptosight.data.downloader import Downloader

logger = get_logger("SignalsMain")


def run_signals_pipeline(
    config_path: str = None,
) -> pd.DataFrame:
    """
    Master signals pipeline: loads market configuration from YAML, fetches and resamples data,
    calculates indicators, evaluates conditions, and generates trading signals.
    """
    if config_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "strategy_config.yaml")

    logger.info(f"Loading configuration from {config_path}...")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            strat_file = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return pd.DataFrame()

    market_cfg = strat_file.get("market", {})
    indicator_config = strat_file.get("indicators", {})
    strategy_config = strat_file.get("strategy", {})


    exchange = market_cfg.get("exchange")
    symbol = market_cfg.get("symbol")
    base_timeframe = market_cfg.get("timeframe")
    target_timeframe = market_cfg.get("target_timeframe")
    start_time = market_cfg.get("start_time")
    end_time = market_cfg.get("end_time")
    max_retries = market_cfg.get("max_retries")
    retry_delay = market_cfg.get("retry_delay")
    logger.info(f"Fetching {symbol} from {exchange} ({base_timeframe} resampled to {target_timeframe})...")
    dl = Downloader(exchange=exchange, symbol=symbol, timeframe=base_timeframe)
    try:
        # Always call resample() to fetch and resample the data directly
        _, df = dl.resample(
            target_timeframe=target_timeframe,
            start_time=start_time,
            end_time=end_time,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
    except Exception as e:
        logger.error(f"Failed to fetch/resample data: {e}")
        return pd.DataFrame()

    if df is None or df.empty:
        logger.error("No valid DataFrame available. Pipeline aborted.")
        return pd.DataFrame()

    # 3. Calculate indicators (already shifted by 1 inside apply_indicators_from_config)
    logger.info("Calculating indicators...")
    try:
        merged_df = apply_indicators_from_config(df.copy(), indicator_config)
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return pd.DataFrame()

    if merged_df.empty:
        logger.error("DataFrame empty after calculating indicators.")
        return pd.DataFrame()

    # 4. Evaluate strategy conditions
    logger.info("Evaluating conditions...")
    try:
        conditions_df = ConditionEvaluator(merged_df).process_strategy(strategy_config)
    except Exception as e:
        logger.error(f"Error evaluating strategy conditions: {e}")
        return pd.DataFrame()

    # 5. Shift conditions by 1 to prevent look-ahead bias (condition on bar T -> act on bar T+1)
    if not conditions_df.empty and len(conditions_df.columns) > 0:
        conditions_df = conditions_df.shift(1).fillna(False).astype(bool)
        merged_df = pd.concat([merged_df, conditions_df], axis=1)
    else:
        logger.warning("No strategy conditions generated. Proceeding without condition columns.")

    # 6. Generate signals from rules (conditions are ALREADY shifted from Step 5,
    #    so the signal here is already look-ahead safe — no second shift needed)
    logger.info("Generating signals...")
    try:
        final_signal = RulesEvaluator(conditions_df, strategy_config).generate_signals()
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        return pd.DataFrame()

    merged_df["signal"] = final_signal.fillna(0).astype(int)

    # 7. Drop residual NaN rows and finalize
    merged_df.dropna(inplace=True)
    merged_df["signal"] = merged_df["signal"].astype(int)

    active_signals = (merged_df["signal"] != 0).sum()
    logger.info(f"Pipeline complete — {len(merged_df)} rows, {active_signals} active signals.")
    return merged_df


def run_pipeline_from_config(config_path: str = None) -> pd.DataFrame:
    """Reusable entry point — runs the entire pipeline from YAML config alone. Call from anywhere."""
    return run_signals_pipeline(config_path=config_path)


if __name__ == "__main__":
    print("=" * 55)
    print("           RUNNING SIGNALS PIPELINE TEST")
    print("=" * 55)

    # Execute the pipeline with the default configuration
    final_df = run_signals_pipeline()

    if final_df.empty:
        print("\n[FAILED] Pipeline execution returned an empty DataFrame.")
    else:
        print(f"\n[SUCCESS] Pipeline successfully generated {len(final_df)} rows.")
        
        # Identify columns to display in print
        display_cols = [
            col for col in ["close", "ind_sma_20", "long_cond_1", "short_cond_1", "signal"] 
            if col in final_df.columns
        ]
        print("\n--- Last 15 rows of results ---")
        print(final_df[display_cols].tail(15))

        # Save to CSV
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signals_pipeline_output.csv")
        try:
            final_df.to_csv(output_path)
            print(f"\n[CSV SAVED] Output saved successfully to: {output_path}")
        except Exception as e:
            print(f"\n[WARNING] Could not save output to {output_path}: {e}")
        print("=" * 55)
