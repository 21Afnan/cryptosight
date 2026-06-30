import talib
from talib import abstract
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from cryptosight.utils.logger import get_logger
from cryptosight.tal_Indicators.config import INDICATOR_CONFIG

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
                return res
            return res.to_frame(name=output_names[0])

        return caller

    def plot(self, names: list = None, **params_per_name) -> None:
        """
        ONE master plotting function!
        Plots Price + any list of requested indicators stacked vertically on a single unified dashboard.
        e.g. indicators.plot(["RSI", "MACD", "ATR"], RSI={"timeperiod": 14})
        """
        names = names or []
        num_rows = 1 + len(names)
        row_heights = [0.4] + [0.6 / len(names)] * len(names) if names else [1.0]

        fig = make_subplots(
            rows=num_rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=["Price"] + [n.upper() for n in names]
        )

        # Row 1: Candlesticks
        fig.add_trace(go.Candlestick(
            x=self.df.index, open=self.df["open"], high=self.df["high"],
            low=self.df["low"], close=self.df["close"], name="Price"
        ), row=1, col=1)

        # Rows 2+: Indicators
        for i, n in enumerate(names, start=2):
            try:
                # Call __getattr__ dynamically to compute indicator with config defaults!
                caller = getattr(self, n)
                res = caller(**params_per_name.get(n, {}))
                for col in res.columns:
                    fig.add_trace(go.Scatter(x=res.index, y=res[col], name=col), row=i, col=1)
            except Exception as e:
                logger.warning(f"Skipped plotting {n}: {e}")

        fig.update_layout(
            title="CryptoSight Quant Trading Dashboard",
            height=280 * num_rows,
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
        )
        fig.show()


if __name__ == "__main__":
    from cryptosight.data.downloader import Downloader

    dl = Downloader(exchange="bybit", symbol="btc", timeframe="1m")
    df = dl.get_data(start_time="2026-06-22 00:00:00", end_time="now", max_retries=5, retry_delay=3)
    df = df.tail(1000)
    # Pass global custom parameters directly into Indicators initialization!
    ind = Indicators(
        df,
        RSI={"timeperiod": 14},
        ATR={"timeperiod": 14}
    )



    # ONE single plot call! (automatically uses settings passed into Indicators constructor above)
    ind.plot(["RSI", "MACD", "ATR"])

