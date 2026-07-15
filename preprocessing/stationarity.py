import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from cryptosight.utils.logger import get_logger

logger = get_logger("PPStationarity")


class StationarityAnalyzer:
    """
    Intelligent Quantitative Stationarity & Trend Preservation Suite.
    Executes ADF, KPSS, Autocorrelation, Half-Life of Mean Reversion,
    and automatically discovers the optimal Fractional Differencing order (`d`).
    """

    def __init__(self, exclude_cols: set = None):
        self.exclude_cols = exclude_cols or {"timestamp", "target"}
        logger.info("Initialized StationarityAnalyzer Suite")

    def run_adf_test(self, series: pd.Series) -> dict:
        """
        Augmented Dickey-Fuller (ADF) Test for Unit Root Stationarity.
        Null Hypothesis (H0): Series possesses a unit root (Non-Stationary).
        If p_value < 0.05, we reject H0 and confirm Stationarity.
        """
        clean_series = series.dropna()
        if len(clean_series) < 20 or np.var(clean_series) < 1e-12:
            return {"adf_stat": 0.0, "p_value": 1.0, "is_stationary": False}

        try:
            res = adfuller(clean_series, autolag="AIC")
            p_val = float(res[1])
            return {
                "adf_stat": float(res[0]),
                "p_value": p_val,
                "is_stationary": p_val < 0.05,
            }
        except Exception as e:
            logger.debug(f"ADF test failed for series ({e}). Defaulting to non-stationary.")
            return {"adf_stat": 0.0, "p_value": 1.0, "is_stationary": False}

    def run_kpss_test(self, series: pd.Series) -> dict:
        """
        Kwiatkowski-Phillips-Schmidt-Shin (KPSS) Test for Trend Stationarity.
        Null Hypothesis (H0): Series is stationary around a deterministic trend.
        If p_value > 0.05, we fail to reject H0 and confirm Stationarity.
        """
        clean_series = series.dropna()
        if len(clean_series) < 20 or np.var(clean_series) < 1e-12:
            return {"kpss_stat": 0.0, "p_value": 0.0, "is_stationary": False}

        try:
            res = kpss(clean_series, regression="c", nlags="auto")
            p_val = float(res[1])
            return {
                "kpss_stat": float(res[0]),
                "p_value": p_val,
                "is_stationary": p_val > 0.05,
            }
        except Exception as e:
            logger.debug(f"KPSS test failed for series ({e}). Defaulting to non-stationary.")
            return {"kpss_stat": 0.0, "p_value": 0.0, "is_stationary": False}

    def calculate_autocorrelation(self, series: pd.Series, lag: int = 1) -> dict:
        """
        Computes Autocorrelation coefficient (`rho`) at specified lag
        and calculates the Ornstein-Uhlenbeck Half-Life of Mean Reversion.
        Half-Life = -ln(2) / ln(|rho|) bars.
        """
        clean_series = series.dropna()
        if len(clean_series) < lag + 10 or np.var(clean_series) < 1e-12:
            return {"autocorr_lag1": 0.0, "half_life_bars": 0.0}

        try:
            rho = float(clean_series.autocorr(lag=lag))
            if np.isnan(rho):
                rho = 0.0

            if 0.0 < abs(rho) < 1.0:
                half_life = float(-np.log(2.0) / np.log(abs(rho)))
            else:
                half_life = 999.0  # Persistent drift / random walk

            return {"autocorr_lag1": rho, "half_life_bars": round(half_life, 2)}
        except Exception:
            return {"autocorr_lag1": 0.0, "half_life_bars": 0.0}

    def find_optimal_frac_d(self, series: pd.Series, step: float = 0.05, max_d: float = 1.0) -> float:
        """
        Intelligent Auto-Adjusting Fractional Differencing Order Discovery.
        Loops `d` from `step` up to `max_d` by increments of `step`.
        Returns the MINIMUM `d` where ADF p_value < 0.05 (stationary),
        thereby preserving the MAXIMUM possible historical memory.
        """
        clean_series = series.dropna().to_numpy(dtype=float, copy=True)
        if len(clean_series) < 50:
            return 0.35  # Fallback standard quant default if insufficient data

        d_candidate = step
        while d_candidate <= max_d:
            # Calculate fractional weights for candidate `d`
            weights = [1.0]
            for k in range(1, 100):
                w = -weights[-1] / k * (d_candidate - k + 1)
                if abs(w) < 1e-4:
                    break
                weights.append(w)
            w_arr = np.array(weights, dtype=float)

            # Convolve and run fast ADF test
            convolved = np.convolve(clean_series, w_arr, mode="full")[: len(clean_series)]
            test_series = pd.Series(convolved[len(w_arr):])  # Drop initial warm-up transient
            adf_res = self.run_adf_test(test_series)

            if adf_res["is_stationary"]:
                logger.debug(f"Discovered optimal frac_d={d_candidate:.2f} (ADF p={adf_res['p_value']:.4f})")
                return round(d_candidate, 2)

            d_candidate += step

        return 1.0  # Fall back to integer first difference (standard returns) if very stubborn

    def evaluate_trend_preservation(self, raw_series: pd.Series, transformed_series: pd.Series, long_window: int = 50) -> dict:
        """
        PDF Requirement 5: Trend Preservation Verification.
        Measures correlation between:
        1. Long-term rolling trends (`long_window` SMA correlation).
        2. Local step-by-step variations (1-bar delta correlation).
        """
        raw_clean = raw_series.dropna()
        trans_clean = transformed_series.dropna()
        common_idx = raw_clean.index.intersection(trans_clean.index)

        if len(common_idx) < long_window + 10:
            return {"long_term_corr": 0.0, "local_corr": 0.0, "trend_preserved": False}

        r = raw_clean.loc[common_idx]
        t = trans_clean.loc[common_idx]

        # 1. Long-term trend correlation (Rolling SMA)
        r_trend = r.rolling(window=long_window, min_periods=10).mean().dropna()
        t_trend = t.rolling(window=long_window, min_periods=10).mean().dropna()
        long_corr = float(r_trend.corr(t_trend)) if len(r_trend) > 10 else 0.0

        # 2. Local step delta correlation
        r_diff = r.diff().dropna()
        t_diff = t.diff().dropna()
        local_corr = float(r_diff.corr(t_diff)) if len(r_diff) > 10 else 0.0

        if np.isnan(long_corr):
            long_corr = 0.0
        if np.isnan(local_corr):
            local_corr = 0.0

        # A technique preserves meaningful trend if long-term correlation > 0.40 or local correlation > 0.50
        preserved = abs(long_corr) > 0.40 or abs(local_corr) > 0.50
        return {
            "long_term_corr": round(long_corr, 4),
            "local_corr": round(local_corr, 4),
            "trend_preserved": preserved,
        }

    def analyze_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs complete ADF, KPSS, Autocorrelation, and Half-Life tests across all numeric features in `df`.
        Returns a cleanly formatted Summary Leaderboard DataFrame.
        """
        feature_cols = [
            col for col in df.columns
            if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]

        if not feature_cols:
            logger.warning("No numeric features found to run stationarity analysis.")
            return pd.DataFrame()

        rows = []
        for col in feature_cols:
            series = df[col]
            adf = self.run_adf_test(series)
            kpss_res = self.run_kpss_test(series)
            acf = self.calculate_autocorrelation(series)

            rows.append({
                "feature": col,
                "adf_stat": round(adf["adf_stat"], 4),
                "adf_p_value": round(adf["p_value"], 4),
                "adf_stationary": adf["is_stationary"],
                "kpss_stat": round(kpss_res["kpss_stat"], 4),
                "kpss_p_value": round(kpss_res["p_value"], 4),
                "kpss_stationary": kpss_res["is_stationary"],
                "autocorr_lag1": round(acf["autocorr_lag1"], 4),
                "half_life_bars": acf["half_life_bars"],
            })

        summary_df = pd.DataFrame(rows)
        logger.info(f"Completed Stationarity Analysis across {len(feature_cols)} features.")
        return summary_df
