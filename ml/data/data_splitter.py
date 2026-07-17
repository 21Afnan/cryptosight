import pandas as pd
from cryptosight.utils.logger import get_logger

logger = get_logger("DataSplitter")

def split_data_chronological(
    df: pd.DataFrame, 
    train_ratio: float, 
    val_ratio: float, 
    test_ratio: float,
    config: dict = None,
    save_yaml: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """
    Splits a DataFrame chronologically into train, validation, and test sets.
    Generates metadata about rows and timestamps to be stored in the unified quant pipeline JSON.
    
    Args:
        df: Input DataFrame containing historical features.
        train_ratio: Proportion of data to assign to the training set.
        val_ratio: Proportion of data to assign to the validation set.
        test_ratio: Proportion of data to assign to the test set.
        config: Configuration dictionary from ml_config.yaml for metadata extraction.
        save_yaml: Deprecated (defaults to False, unified JSON is used instead).
        
    Returns:
        tuple containing (train_df, val_df, test_df, split_info_dict)
    """
    # Safety check: Ensure the ratios sum to approximately 1.0
    total_ratio = train_ratio + val_ratio + test_ratio
    if not (0.99 <= total_ratio <= 1.01):
        raise ValueError(f"Ratios must sum to 1.0 (current sum: {total_ratio})")

    total_rows = len(df)
    train_end = int(total_rows * train_ratio)
    val_end = int(total_rows * (train_ratio + val_ratio))

    # Slice the DataFrame chronologically by index
    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]

    # Helper function to get start and end timestamps safely
    def get_time_bounds(subset_df: pd.DataFrame) -> tuple[str, str]:
        if subset_df.empty:
            return "N/A", "N/A"
        # Check if 'timestamp' is a column
        if "timestamp" in subset_df.columns:
            start = str(subset_df["timestamp"].iloc[0])
            end = str(subset_df["timestamp"].iloc[-1])
        else:
            # Check index
            start = str(subset_df.index[0])
            end = str(subset_df.index[-1])
        return start, end

    train_start, train_end_time = get_time_bounds(train_df)
    val_start, val_end_time = get_time_bounds(val_df)
    test_start, test_end_time = get_time_bounds(test_df)

    exchange = symbols = timeframe = target_timeframe = start_date = end_date = None
    if config:
        data_cfg = config.get("data", {})
        exchange = data_cfg.get("exchange")
        symbols = data_cfg.get("symbols")
        timeframe = data_cfg.get("timeframe")
        target_timeframe = data_cfg.get("target_timeframe")
        start_date = data_cfg.get("start_date")
        end_date = data_cfg.get("end_date")

    # 1. Extract feature columns dynamically from DataFrame
    feature_cols = [col for col in df.columns if col not in ["timestamp", "target"]]

    # 2. Extract technical indicators & patterns details from config if available
    indicators_info = []
    patterns_info = []
    
    if config:
        features_cfg = config.get("features", {})
        if features_cfg and features_cfg.get("enabled"):
            # Parse indicators
            indicators_dict = features_cfg.get("indicators", {})
            for ind_name, ind_list in indicators_dict.items():
                if isinstance(ind_list, list):
                    for item in ind_list:
                        params = item.get("parameters")
                        indicators_info.append({
                            "name": ind_name,
                            "parameters": params
                        })
                elif isinstance(ind_list, dict):
                    params = ind_list.get("parameters")
                    indicators_info.append({
                        "name": ind_name,
                        "parameters": params
                    })
            
            # Parse patterns
            patterns_dict = features_cfg.get("patterns", {})
            if patterns_dict:
                for pat_name in patterns_dict.keys():
                    patterns_info.append(pat_name)
    
    # Set default text labels if empty/disabled
    if not indicators_info:
        indicators_info = "no indicators"
    if not patterns_info:
        patterns_info = "no patterns"

    # Check if raw OHLCV columns are kept in the feature list
    ohlcv_cols = {"open", "high", "low", "close", "volume"}
    has_ohlcv = any(col in feature_cols for col in ohlcv_cols)
    ohlcv_status = "enabled" if has_ohlcv else "no ohlcv"

    # Compile the metadata config dictionary without any redundant dataset properties
    split_info = {
        "features_summary": {
            "ohlcv": ohlcv_status,
            "features_list": feature_cols,
            "indicators": indicators_info,
            "patterns": patterns_info
        },
        "splits_summary": {
            "train": {
                "rows": len(train_df),
                "start_timestamp": train_start,
                "end_timestamp": train_end_time
            },
            "validation": {
                "rows": len(val_df),
                "start_timestamp": val_start,
                "end_timestamp": val_end_time
            },
            "test": {
                "rows": len(test_df),
                "start_timestamp": test_start,
                "end_timestamp": test_end_time
            }
        }
    }

    logger.info(
        f"Chronological split complete | Total: {total_rows} rows | "
        f"Train: {len(train_df)} ({train_ratio*100:.0f}%) | "
        f"Val: {len(val_df)} ({val_ratio*100:.0f}%) | "
        f"Test: {len(test_df)} ({test_ratio*100:.0f}%)"
    )

    return train_df, val_df, test_df, split_info
