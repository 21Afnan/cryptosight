from talib import abstract
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.tal_Indicators.tal_ind_con import INDICATOR_CONFIG

logger = get_logger("Indicators")


class Indicators:
    """
    Magic wrapper around TA-Lib (158 functions).
    Resolves parameters from: INDICATOR_CONFIG defaults -> __init__ overrides -> method kwargs.
    e.g. ind.rsi(timeperiod=14) or ind.macd()
    """

    def __init__(self, df: pd.DataFrame, **custom_params):
        self.df = df
        self.custom_params = {k.upper(): v for k, v in custom_params.items()}

    def __getattr__(self, name: str):
        upper_name = name.upper()
        if upper_name not in INDICATOR_CONFIG:
            raise AttributeError(f"'Indicators' object has no indicator '{name}'.")

        def caller(**params) -> pd.DataFrame:
            cfg = INDICATOR_CONFIG[upper_name]
            allowed = cfg.get("parameters", {})

            # 1. Defaults -> 2. __init__ overrides -> 3. Valid call-time kwargs
            final_params = {k: v["default"] for k, v in allowed.items()}
            final_params.update(self.custom_params.get(upper_name, {}))
            final_params.update({k: v for k, v in params.items() if k in allowed})

            res = abstract.Function(upper_name)(self.df, **final_params)

            output_names = [o["name"] for o in cfg["outputs"]]
            if isinstance(res, pd.DataFrame):
                res.columns = output_names
            else:
                res = res.to_frame(name=output_names[0])

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
        """Builds a DataFrame containing requested indicators and/or patterns."""
        result_df = self.df if include_ohlcv else pd.DataFrame(index=self.df.index)

        # 1. Explicit indicator names list
        for n in (names or []):
            try:
                res = getattr(self, n)(**params_per_name.get(n, {}))
                for col in res.columns:
                    result_df[f"ind_{n.lower()}_{col.lower()}"] = res[col]
            except Exception as e:
                logger.warning(f"Skipped {n}: {e}")

        if not indicator_config:
            return result_df

        ind_dict = indicator_config.get("indicators", indicator_config)
        pat_dict = indicator_config.get("patterns", {})

        # 2a. Standard technical indicators (from YAML config)
        if isinstance(ind_dict, dict):
            for ind_name, configs in ind_dict.items():
                configs = [configs] if isinstance(configs, dict) else configs
                for cfg in (configs if isinstance(configs, list) else []):
                    try:
                        res = getattr(self, ind_name)(**cfg.get("parameters", {}))
                        for col in res.columns:
                            col_name = cfg.get("aliases", {}).get(col, f"ind_{ind_name.lower()}_{col.lower()}")
                            result_df[col_name] = res[col]
                    except Exception as e:
                        logger.warning(f"Skipped {ind_name}: {e}")

        # 2b. Chart patterns (from YAML config)
        if isinstance(pat_dict, dict):
            for pat_name, pat_cfg in pat_dict.items():
                pat_cfg = pat_cfg[0] if isinstance(pat_cfg, list) and pat_cfg else (pat_cfg if isinstance(pat_cfg, dict) else {})
                upper_name = pat_name.upper()
                base_name = upper_name.replace("BULLISH_", "").replace("BEARISH_", "")
                talib_name = next((c for c in [upper_name, f"CDL{upper_name}", base_name, f"CDL{base_name}"] if hasattr(self, c)), None)

                if not talib_name:
                    continue

                try:
                    res = getattr(self, talib_name)(**pat_cfg.get("parameters", {}))
                    if not res.empty and "integer" in res.columns:
                        col_data = res["integer"]
                        if "BULLISH" in upper_name:
                            col_data = col_data.apply(lambda x: 100 if x > 0 else 0)
                        elif "BEARISH" in upper_name:
                            col_data = col_data.apply(lambda x: -100 if x < 0 else 0)
                        aliases = pat_cfg.get("aliases", {})
                        target_col = aliases.get("pattern") or (list(aliases.values())[0] if aliases else f"pat_{pat_name}")
                        result_df[target_col] = col_data
                except Exception as e:
                    logger.warning(f"Skipped pattern {pat_name}: {e}")

        return result_df


def apply_indicators_from_config(df: pd.DataFrame, indicator_config: dict) -> pd.DataFrame:
    """Calculates, lags by 1 period (prevents Look-Ahead Bias), and merges indicators from YAML config."""
    ind = Indicators(df)
    indicator_df = ind.get_dataframe(names=[], include_ohlcv=False, indicator_config=indicator_config)
    merged_df = pd.concat([df, indicator_df.shift(1)], axis=1)
    return merged_df.dropna()

