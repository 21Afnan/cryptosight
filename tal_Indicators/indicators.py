import talib
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

    def generate_alias(self, indicator_name: str, output_name: str, params: dict, category: str) -> str:
        """
        Auto-generates a Signals-module-compliant alias string.
        Pattern indicators  -> pat_<NAME>              (e.g. pat_DOJI)
        Single-output       -> ind_<INDICATOR>_<params> (e.g. ind_RSI_14)
        Multi-output primary-> ind_<INDICATOR>_<params> (e.g. ind_MACD_12_26_9)
        Multi-output other  -> ind_<INDICATOR>_<OUTPUT>_<params> (e.g. ind_MACD_SIGNAL_12_26_9)
        """
        upper_ind = indicator_name.upper()
        param_suffix = "_".join(str(v) for v in params.values())

        if category == "Pattern Recognition":
            pat_name = upper_ind[3:] if upper_ind.startswith("CDL") else upper_ind
            return f"pat_{pat_name}"

        is_primary = output_name.upper() == upper_ind
        alias = f"ind_{upper_ind}" if is_primary else f"ind_{upper_ind}_{output_name.upper()}"

        if param_suffix:
            alias += f"_{param_suffix}"
        return alias

    def get_dataframe(
        self,
        names: list = None,
        include_ohlcv: bool = True,
        alias_style: bool = False,
        **params_per_name
    ) -> pd.DataFrame:
        """
        ONE function to build any indicator DataFrame you need.

        names          : list of indicators to calculate, e.g. ["rsi", "macd", "atr"]
        include_ohlcv  : True  -> returns OHLCV + indicator columns
                         False -> returns indicator columns only
        alias_style    : False -> original naming, e.g. RSI_RSI_14           (default, backward compatible)
                         True  -> Signals-module naming, e.g. ind_RSI_14     (for signals/main.py)
        params_per_name: per-indicator param overrides, e.g. rsi={"timeperiod": 14}

        Safe to call the same indicator more than once with different params —
        column names always stay unique either way.
        """
        names = names or []
        result_df = self.df.copy() if include_ohlcv else pd.DataFrame(index=self.df.index)

        for n in names:
            try:
                caller = getattr(self, n)
                call_params = params_per_name.get(n, {})
                res = caller(**call_params)

                used_params = res.attrs.get("used_params", {})
                category = res.attrs.get("category", "")
                suffix = "_".join(str(v) for v in used_params.values())

                for col in res.columns:
                    if alias_style:
                        col_name = self.generate_alias(n, col, used_params, category)
                    else:
                        col_name = f"{n.upper()}_{col.upper()}"
                        if suffix:
                            col_name += f"_{suffix}"

                    result_df[col_name] = res[col]

            except Exception as e:
                logger.warning(f"Skipped calculating {n}: {e}")

        return result_df

def apply_indicators_from_config(df: pd.DataFrame, indicator_config: dict) -> pd.DataFrame:
    """
    Helper function to calculate and merge all indicators based on the YAML config.
    """
    ind = Indicators(df)
    merged_df = df.copy()

    for ind_name, configs in indicator_config.items():
        for cfg in configs:
            params = cfg.get("parameters", {})
            try:
                caller = getattr(ind, ind_name)
                res = caller(**params)
            
                used_params = res.attrs.get("used_params", {})
                category = res.attrs.get("category", "")
                aliases_map = cfg.get("aliases", {})
            
                for col in res.columns:
                    if col in aliases_map:
                        col_alias = aliases_map[col]
                    else:
                        col_alias = ind.generate_alias(ind_name, col, used_params, category)
                    
                    # To ADD Look-Ahead Bias (NOT RECOMMENDED for live trading), change the line below to:
                    # merged_df[col_alias] = res[col]
                    merged_df[col_alias] = res[col].shift(1)
            except Exception as e:
                logger.error(f"Failed to calculate {ind_name}: {e}")
            
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
