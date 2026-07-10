from pathlib import Path
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config
from cryptosight.data.downloader import Downloader

logger = get_logger("MLFeatures")


class MLFeatureBuilder:
    """
    Step 1: Direct ML Dataset Resampling Pipeline.
    Loads `ml_config.yaml` and directly calls `dl.resample()` for all configured symbols.
    """

    def __init__(self, config: dict):
        if not isinstance(config, dict) or not config:
            raise ValueError("MLFeatureBuilder requires a valid loaded `config: dict` dictionary.")
        self.config = config
        data_cfg = self.config.get("data")

        logger.info("=== ML Module Config Initialized ===")
        logger.info(f"Model Type       : {self.config.get('model_type')}")
        logger.info(f"Exchange         : {data_cfg.get('exchange')}")
        logger.info(f"Symbols          : {data_cfg.get('symbols')}")
        logger.info(f"Base Timeframe   : {data_cfg.get('timeframe')}")
        logger.info(f"Target Timeframe : {data_cfg.get('target_timeframe')}")
        logger.info(f"Date Range       : {data_cfg.get('start_date')} to {data_cfg.get('end_date')}")

    def fetch_and_resample_data(self) -> dict[str, pd.DataFrame]:
        """
        Loops over all configured symbols (`symbols: ["BTC", "ETH"]`) in `ml_config.yaml`,
        directly runs `dl.resample()`, and returns a dictionary of clean resampled DataFrames:
        {"BTC": df_btc, "ETH": df_eth}.
        """
        data_cfg = self.config.get("data")
        if not data_cfg.get("enabled"):
            return {}

        cfg_exchange = data_cfg.get("exchange")
        exchange = cfg_exchange[0] if isinstance(cfg_exchange, list) else cfg_exchange

        cfg_symbols = data_cfg.get("symbols")
        if isinstance(cfg_symbols, str):
            cfg_symbols = [cfg_symbols]

        base_timeframe = data_cfg.get("timeframe")
        target_timeframe = data_cfg.get("target_timeframe")
        start_time = data_cfg.get("start_date")
        end_time = data_cfg.get("end_date")
        max_retries = data_cfg.get("max_retries")
        retry_delay = data_cfg.get("retry_delay")

        results = {}
        for symbol in cfg_symbols:
            logger.info(f"--- Resampling [{symbol.upper()}] from {base_timeframe} to {target_timeframe} ---")
            dl = Downloader(exchange=exchange, symbol=symbol, timeframe=base_timeframe)
            try:
                _, resampled_df = dl.resample(
                    target_timeframe=target_timeframe,
                    start_time=start_time,
                    end_time=end_time,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                )
                if resampled_df is not None and not resampled_df.empty:
                    logger.info(f"Ready: {len(resampled_df)} resampled candles for {symbol.upper()} [{target_timeframe}].")
                    results[symbol.upper()] = resampled_df
                else:
                    logger.warning(f"Resampled DataFrame for {symbol.upper()} is empty.")
            except Exception as e:
                logger.error(f"Failed to resample market data for {symbol.upper()}: {e}")

        return results

    def add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 2: Feature Engineering (Technical Indicators & Chart Patterns ONLY).
        Intelligently delegates all indicator and pattern calculations directly to `Indicators.get_dataframe()`.
        """
        features_cfg = self.config.get("features")
        if not features_cfg.get("enabled") or df.empty:
            return df

        from cryptosight.tal_Indicators.indicators import Indicators
        ind = Indicators(df)

        # 1. ONE intelligent call to get_dataframe for both standard indicators AND chart patterns!
        features_df = ind.get_dataframe(names=[], include_ohlcv=False, indicator_config=features_cfg)

        # 2. Merge features onto OHLCV DataFrame and drop initial warm-up NaNs
        merged_df = pd.concat([df, features_df], axis=1).dropna()
        logger.info(f"Feature Engineering complete --> Added {len(features_df.columns)} features | {len(merged_df)} clean rows ready.")
        return merged_df

    def add_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 3: Target Generation (`add_target`).
        Generates the target column (`target`) based on `model_type` (`regression`, `classification`, or `timeseries`).
        Drops trailing `horizon` rows where the future target is NaN (`unknown future`).
        """
        if df.empty:
            return df

        model_type = str(self.config.get("model_type")).lower()
        target_cfg = self.config.get("target")
        horizon = int(target_cfg.get("horizon"))
        source_col = target_cfg.get("source")
        threshold = float(target_cfg.get("threshold"))

        if source_col not in df.columns:
            logger.warning(f"Target source column '{source_col}' not found in DataFrame. Skipping target generation.")
            return df

        result_df = df.copy()

        if model_type == "regression":
            # Percentage return exactly `horizon` bars into the future
            # Bounded, stationary continuous return (`Quant State-of-the-Art`)
            result_df["target"] = (result_df[source_col].shift(-horizon) - result_df[source_col]) / result_df[source_col]
            logger.info(f"[Target: Regression] Generated {horizon}-bar future percentage return target.")

        elif model_type == "classification":
            # Threshold-filtered directional class: 1 (UP above fees), -1 (DOWN below fees), 0 (HOLD/NOISE)
            future_return = (result_df[source_col].shift(-horizon) - result_df[source_col]) / result_df[source_col]
            result_df["target"] = 0
            result_df.loc[future_return > threshold, "target"] = 1
            result_df.loc[future_return < -threshold, "target"] = -1
            logger.info(f"[Target: Classification] Generated {horizon}-bar directional target with {threshold*100:.2f}% threshold filter.")

        elif model_type == "timeseries":
            # Shifting raw source sequence by `horizon` bars for sequence-to-sequence deep forecasting
            result_df["target"] = result_df[source_col].shift(-horizon)
            logger.info(f"[Target: Time Series] Generated {horizon}-bar shifted raw sequence target.")

        else:
            logger.warning(f"Unknown model_type '{model_type}'. Defaulting to regression percentage return.")
            result_df["target"] = (result_df[source_col].shift(-horizon) - result_df[source_col]) / result_df[source_col]

        # Cleanly drop trailing unknown horizon rows and organize columns logically (`target` right next to OHLCV)
        clean_df = result_df.dropna(subset=["target"])
        base_cols = [c for c in ["open", "high", "low", "close", "volume", "target"] if c in clean_df.columns]
        other_cols = [c for c in clean_df.columns if c not in base_cols]
        clean_df = clean_df[base_cols + other_cols]

        logger.info(f"Target generation complete --> {len(clean_df)} clean rows ready (dropped {len(result_df) - len(clean_df)} trailing horizon rows).")
        return clean_df

    def build_dataset(self) -> dict[str, pd.DataFrame]:
        """
    Runs Step 1 (Resampling) + Step 2 (Technical Indicators & Chart Patterns) + Step 3 (Target Generation).
    Returns a dictionary of clean DataFrames: {"BTC": clean_df}.
        """
        resampled_data = self.fetch_and_resample_data()
        feature_data = {}

        for sym, df in resampled_data.items():
            logger.info(f"--- Building Features & Target for [{sym}] ---")
            processed_df = self.add_technical_features(df)
            processed_df = self.add_target(processed_df)
            feature_data[sym] = processed_df

            logger.info(f"=== {sym} Ready [{str(self.config.get('model_type', 'regression')).upper()} | Shape: {processed_df.shape}] ===")

            print("\n" + "=" * 85)
            print(f" [{sym}] QUANT ML DATASET PREVIEW (Total Columns: {len(processed_df.columns)})")
            print("=" * 85)
            preview_df = processed_df.tail(3).round(4)
            with pd.option_context("display.float_format", "{:.4f}".format):
                print(preview_df.T.to_string())
            print("=" * 85 + "\n")

        return feature_data