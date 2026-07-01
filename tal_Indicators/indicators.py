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

            # Stash params actually used — needed for unique column naming
            res.attrs["used_params"] = final_params
            return res

        return caller

    def get_dataframe(self, names: list = None, include_ohlcv: bool = True, **params_per_name) -> pd.DataFrame:
        """
        ONE function to build any indicator DataFrame you need.

        names          : list of indicators to calculate, e.g. ["rsi", "macd", "atr"]
        include_ohlcv  : True  -> returns OHLCV + indicator columns (for saving/signals)
                         False -> returns indicator columns only (for quick inspection/plotting)
        params_per_name: per-indicator param overrides, e.g. rsi={"timeperiod": 14}

        Column naming is always collision-safe: INDICATORNAME_OUTPUT_PARAMVALUES
        e.g. RSI_RSI_14, MACD_MACD_12_26_9, MACD_SIGNAL_12_26_9
        Safe to call the same indicator more than once with different params.
        """
        names = names or []

        # Base: either a copy of OHLCV, or an empty frame sharing the same index
        result_df = self.df.copy() if include_ohlcv else pd.DataFrame(index=self.df.index)

        for n in names:
            try:
                caller = getattr(self, n)
                call_params = params_per_name.get(n, {})
                res = caller(**call_params)

                # Build param suffix like "14" or "12_26_9" from the params actually used
                used_params = res.attrs.get("used_params", {})
                suffix = "_".join(str(v) for v in used_params.values())

                for col in res.columns:
                    col_name = f"{n.upper()}_{col.upper()}"
                    if suffix:
                        col_name += f"_{suffix}"
                    result_df[col_name] = res[col]

            except Exception as e:
                logger.warning(f"Skipped calculating {n}: {e}")

        return result_df


if __name__ == "__main__":
    from cryptosight.data.downloader import Downloader

    dl = Downloader(exchange="bybit", symbol="btc", timeframe="1m")
    df = dl.get_data(start_time="2026-06-22 00:00:00", end_time="now", max_retries=5, retry_delay=3)
    df = df.tail(1000)

    ind = Indicators(
        df,
        RSI={"timeperiod": 14},
        ATR={"timeperiod": 14}
    )

    # Indicators only, no OHLCV — quick look
    quick_df = ind.get_dataframe(["rsi", "macd"], include_ohlcv=False)
    print("Indicators only:")
    print(quick_df.tail(5))

    # Full OHLCV + indicators — for saving/signals module
    full_df = ind.get_dataframe(["rsi", "macd", "atr"], include_ohlcv=True)
    print("\nFull OHLCV + indicators:")
    print(full_df.tail(10))

    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "indicators_output.csv")
    
    full_df.to_csv(csv_path)
    print(f"\nSaved to {csv_path}")