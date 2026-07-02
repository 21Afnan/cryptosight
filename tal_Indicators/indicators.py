from talib import abstract
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.tal_Indicators.tal_ind_con import INDICATOR_CONFIG

logger = get_logger("Indicators")


class Indicators:
    """
    Magic class-based wrapper around every TA-Lib function (158 total).
    Uses INDICATOR_CONFIG for default parameters and input validation.
    Enables calling any indicator directly as a method using __getattr__!
    e.g. ind.rsi(timeperiod=14) or ind.macd()
    """

    def __init__(self, df: pd.DataFrame, **custom_params):
        # df must have lowercase columns: open, high, low, close, volume
        self.df = df
        # Normalize custom parameter override keys to uppercase (e.g. rsi -> RSI)
        self.custom_params = {k.upper(): v for k, v in custom_params.items()}

    def __getattr__(self, name: str):
        """
        Magic method intercepting dynamic indicator calls like ind.rsi() or ind.macd().
        Resolves defaults from INDICATOR_CONFIG -> class custom_params -> method call params.
        """
        upper_name = name.upper()
        if upper_name not in INDICATOR_CONFIG:
            raise AttributeError(f"'Indicators' object has no indicator '{name}' in config.")

        def caller(**params) -> pd.DataFrame:
            cfg = INDICATOR_CONFIG[upper_name]

            # 1. Start with default parameters from config
            final_params = {k: v["default"] for k, v in cfg.get("parameters", {}).items()}
            # 2. Override with global custom parameters passed at __init__
            final_params.update(self.custom_params.get(upper_name, {}))
            # 3. Override with parameters passed directly in method call
            final_params.update(params)

            # TA-Lib abstract interface directly computes on pandas DataFrames!
            res = abstract.Function(upper_name)(self.df, **final_params)

            # If multi-output (DataFrame), map column names to config; if single-output (Series), convert to DataFrame
            output_names = [o["name"] for o in cfg["outputs"]]
            if isinstance(res, pd.DataFrame):
                res.columns = output_names
            else:
                res = res.to_frame(name=output_names[0])

            # Stash params/category — needed for column naming
            res.attrs["used_params"] = final_params
            res.attrs["category"] = cfg.get("category", "")
            return res

        return caller

    def get_dataframe(
        self,
        names: list = None,
        include_ohlcv: bool = True,
        indicator_config: dict = None,
        **params_per_name
    ) -> pd.DataFrame:
        """
        ONE function to build any indicator DataFrame you need.
        Accepts either a list of indicator names or a structured indicator_config dictionary.
        """
        names = names or []
        result_df = self.df.copy() if include_ohlcv else pd.DataFrame(index=self.df.index)

        # 1. Process explicit indicator names list (uses default naming)
        for n in names:
            try:
                caller = getattr(self, n)
                res = caller(**params_per_name.get(n, {}))
                for col in res.columns:
                    col_name = f"ind_{n.lower()}_{col.lower()}"
                    result_df[col_name] = res[col]
            except Exception as e:
                logger.warning(f"Skipped calculating {n}: {e}")

        # 2. Process YAML configuration dictionary (uses custom config aliases)
        if indicator_config:
            for ind_name, configs in indicator_config.items():
                for cfg in configs:
                    params = cfg.get("parameters", {})
                    aliases_map = cfg.get("aliases", {})
                    try:
                        caller = getattr(self, ind_name)
                        res = caller(**params)
                        for col in res.columns:
                            col_name = aliases_map.get(col, f"ind_{ind_name.lower()}_{col.lower()}")
                            result_df[col_name] = res[col]
                    except Exception as e:
                        logger.warning(f"Skipped calculating {ind_name}: {e}")

        return result_df

def apply_indicators_from_config(df: pd.DataFrame, indicator_config: dict) -> pd.DataFrame:
    """
    Helper function to calculate and merge all indicators based on the YAML config.
    """
    ind = Indicators(df)
    indicator_df = ind.get_dataframe(names=[], include_ohlcv=False, indicator_config=indicator_config)
    
    # Shift entire indicators dataframe by 1 to prevent Look-Ahead Bias
    # To ADD Look-Ahead Bias (NOT RECOMMENDED for live trading), remove the .shift(1)
    shifted_indicators = indicator_df.shift(1)
    
    merged_df = pd.concat([df, shifted_indicators], axis=1)
    
    # Drop rows with NaN values caused by indicator calculation periods (e.g. first 200 rows for SMA200)
    merged_df.dropna(inplace=True)
    
    return merged_df

if __name__ == "__main__":
    from cryptosight.data.downloader import Downloader
    
    print("=" * 60)
    # 1. Load the 1h resampled data from the database
    print("Loading 1h BTC data from DB...")
    dl = Downloader(exchange="bybit", symbol="btc", timeframe="1h")
    # Fetching starting from 2025-07-02 to now
    df = dl.get_data(start_time="2025-07-02 00:00:00", end_time="now", max_retries=3, retry_delay=2)
    
    if df.empty:
        print("[FAILED] No 1h data found in the DB. Please run the Binance ingestion pipeline first to store 1h candles.")
    else:
        print(f"[SUCCESS] Loaded {len(df)} candles from DB.")
        
        # 2. Initialize Indicators wrapper
        ind = Indicators(df)
        
        # 3. Calculate SMA (Simple Moving Average)
        print("Calculating SMA (20 period)...")
        sma_df = ind.sma(timeperiod=20)
        
        # 4. Merge SMA and lag it by 1 row using .shift(1) (prevents Look-Ahead Bias)
        df["ind_SMA_20"] = sma_df["sma"].shift(1)
        # 6. Save the results to a CSV file
        output_path = "btc_1h_indicators_bybit_with_bias.csv"
        df.to_csv(output_path)
        print(f"[SUCCESS] Saved resampled data with ind_SMA_20 (lagged) to: {output_path}")
        print("\nLast 5 rows:")
        print(df.tail(5))
        print("=" * 60)
