# ==============================================================================
# CRYPTOSIGHT QUANTITATIVE STATIONARITY & MEMORY ANALYZER (`stationarity.py`)
# ==============================================================================
# PDF Step 4: Formal statistical time-series evaluation for quantitative finance.
# Evaluates whether each preprocessing technique achieves stationarity while preserving memory.
# NOTE: Pure computational module — all CSV exporting is centralized inside `main.py`.
# ==============================================================================

import numpy as np
import pandas as pd
try:
    from statsmodels.tsa.stattools import adfuller, kpss
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    adfuller, kpss = None, None
from cryptosight.utils.logger import get_logger

logger = get_logger("StationarityAnalyzer")


class StationarityAnalyzer:
    """
    Step 4: Evaluates time-series stationarity and memory retention across preprocessing techniques.
    
    Statistical Tests Applied:
    1. Augmented Dickey-Fuller (ADF): Null Hypothesis = Series has a Unit Root (Non-Stationary).
       - p-value < 0.05 => Reject Null (STATIONARY).
    2. KPSS Test: Null Hypothesis = Series is Trend-Stationary.
       - p-value > 0.05 => Fail to Reject Null (STATIONARY).
    3. Autocorrelation (Lag 1 & 5): Measures serial correlation / memory preservation (`Holy Grail for FracDiff`).
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.exclude_cols = set(self.config.get("exclude_columns", ["timestamp", "target"]))
        logger.info("Initialized StationarityAnalyzer (`ADF`, `KPSS`, `Autocorrelation`)")

    def analyze_series(self, series: pd.Series) -> dict:
        """
        Function 1: Runs ADF, KPSS, and Autocorrelation tests on a single 1D numerical series.
        Returns exact p-values, t-statistics, and lag correlations.
        """
        # Clean series: remove NaNs/Infs before feeding to statsmodels
        clean_s = series.ffill().bfill().fillna(0.0).to_numpy(dtype=float, copy=True)
        clean_s = clean_s[np.isfinite(clean_s)]

        if len(clean_s) < 30 or np.std(clean_s) < 1e-12:
            return {
                "adf_pvalue": 1.0,
                "kpss_pvalue": 0.0,
                "autocorr_lag1": 0.0,
                "autocorr_lag5": 0.0,
                "is_stationary": False
            }

        # 1. Augmented Dickey-Fuller (ADF) Test
        try:
            adf_res = adfuller(clean_s, autolag="AIC")
            adf_pvalue = float(adf_res[1])
        except Exception as e:
            logger.debug(f"ADF test convergence issue: {e}")
            adf_pvalue = 1.0

        # 2. KPSS Test (`c` = level stationary)
        try:
            # Suppress statsmodels interpolation warnings during KPSS calculation
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kpss_res = kpss(clean_s, regression="c", nlags="auto")
                kpss_pvalue = float(kpss_res[1])
        except Exception as e:
            logger.debug(f"KPSS test convergence issue: {e}")
            kpss_pvalue = 0.0

        # 3. Autocorrelation Analysis (`Memory Preservation at Lag 1 & 5`)
        try:
            s_obj = pd.Series(clean_s)
            ac_lag1 = float(s_obj.autocorr(lag=1)) if len(clean_s) > 1 else 0.0
            ac_lag5 = float(s_obj.autocorr(lag=5)) if len(clean_s) > 5 else 0.0
            if np.isnan(ac_lag1): ac_lag1 = 0.0
            if np.isnan(ac_lag5): ac_lag5 = 0.0
        except Exception:
            ac_lag1, ac_lag5 = 0.0, 0.0

        # Institutional Stationarity Criteria:
        # 1. ADF passed: Unit Root removed (`p < 0.05`) — Primary criterion for quantitative time-series modeling
        # 2. KPSS passed: Trend-Stationary (`p > 0.05`)
        adf_passed = (adf_pvalue < 0.05)
        kpss_passed = (kpss_pvalue > 0.05)

        return {
            "adf_pvalue": round(adf_pvalue, 4),
            "kpss_pvalue": round(kpss_pvalue, 4),
            "autocorr_lag1": round(ac_lag1, 4),
            "autocorr_lag5": round(ac_lag5, 4),
            "adf_passed": adf_passed,
            "kpss_passed": kpss_passed,
            "is_stationary": adf_passed
        }

    def evaluate_preprocessed_datasets(self, preprocessed_dfs: dict) -> pd.DataFrame:
        """
        Function 2: Loops across all preprocessed DataFrames (`from CryptoMLClassifier`),
        computes average stationarity & memory metrics across all numerical features,
        and returns a structured DataFrame report for `main.py` to display and save.
        """
        if not preprocessed_dfs:
            logger.error("No preprocessed datasets provided for stationarity evaluation!")
            return pd.DataFrame()

        results = []

        for method_name, df in preprocessed_dfs.items():
            logger.info(f"Running stationarity & memory analysis for method: [{method_name.upper()}]...")
            feature_cols = [c for c in df.columns if c not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
            
            if not feature_cols:
                continue

            adf_pvals, kpss_pvals, ac1_vals, ac5_vals = [], [], [], []
            adf_pass_counts, kpss_pass_counts = 0, 0

            for col in feature_cols:
                metrics = self.analyze_series(df[col])
                adf_pvals.append(metrics["adf_pvalue"])
                kpss_pvals.append(metrics["kpss_pvalue"])
                ac1_vals.append(metrics["autocorr_lag1"])
                ac5_vals.append(metrics["autocorr_lag5"])
                if metrics["adf_passed"]:
                    adf_pass_counts += 1
                if metrics["kpss_passed"]:
                    kpss_pass_counts += 1

            avg_adf = float(np.mean(adf_pvals))
            avg_kpss = float(np.mean(kpss_pvals))
            avg_ac1 = float(np.mean(ac1_vals))
            avg_ac5 = float(np.mean(ac5_vals))
            
            adf_pass_pct = round((adf_pass_counts / len(feature_cols)) * 100.0, 1)
            kpss_pass_pct = round((kpss_pass_counts / len(feature_cols)) * 100.0, 1)

            # Assign institutional status label based primarily on ADF Unit Root removal (`p < 0.05`)
            if adf_pass_pct >= 60.0:
                status_label = "STATIONARY"
            elif adf_pass_pct >= 40.0:
                status_label = "PARTIAL STATIONARY"
            else:
                status_label = "NON-STATIONARY"

            results.append({
                "method": method_name.upper(),
                "adf_pvalue_avg": round(avg_adf, 4),
                "kpss_pvalue_avg": round(avg_kpss, 4),
                "autocorr_lag1_avg": round(avg_ac1, 4),
                "autocorr_lag5_avg": round(avg_ac5, 4),
                "adf_pass_rate": f"{adf_pass_pct}% ({adf_pass_counts}/{len(feature_cols)})",
                "kpss_pass_rate": f"{kpss_pass_pct}% ({kpss_pass_counts}/{len(feature_cols)})",
                "stationarity_status": status_label
            })

        report_df = pd.DataFrame(results)
        logger.info("Successfully completed stationarity evaluation across all methods.")
        return report_df
