import numpy as np
import pandas as pd
from cryptosight.utils.logger import get_logger

logger = get_logger("PPTrendPreservation")


class TrendPreservationAnalyzer:
    """
    Quantitative Trend Preservation & Reversibility Evaluation Suite.
    Measures the exact trade-off between stationarity enforcement and memory retention
    by verifying long-term macro trend alignment, short-term local step alignment,
    directional consistency, and mathematical reversibility (inverse reconstruction error).
    """

    def __init__(self, long_window: int = 50, short_window: int = 5, exclude_cols: set = None):
        self.long_window = int(long_window)
        self.short_window = int(short_window)
        self.exclude_cols = exclude_cols or {"timestamp", "target"}
        logger.info(f"Initialized TrendPreservationAnalyzer | Long Window: {self.long_window} bars")

    def evaluate_feature_trend(self, raw_series: pd.Series, transformed_series: pd.Series) -> dict:
        """
        Evaluates trend preservation for a single feature by comparing raw vs preprocessed data.
        1. Long-term Pearson & Spearman rank correlation of rolling trends (`long_window` SMA).
        2. Short-term local correlation (`1-bar` first difference).
        3. Directional sign consistency (`sign(delta_raw) == sign(delta_transformed)`).
        """
        raw_clean = raw_series.dropna()
        trans_clean = transformed_series.dropna()
        common_idx = raw_clean.index.intersection(trans_clean.index)

        if len(common_idx) < self.long_window + 10:
            return {
                "long_term_pearson": 0.0,
                "long_term_spearman": 0.0,
                "short_term_corr": 0.0,
                "directional_accuracy": 0.0,
                "is_trend_preserved": False,
            }

        r = raw_clean.loc[common_idx]
        t = trans_clean.loc[common_idx]

        # 1. Long-term rolling trend correlation (Pearson & Spearman)
        r_trend = r.rolling(window=self.long_window, min_periods=10).mean().dropna()
        t_trend = t.rolling(window=self.long_window, min_periods=10).mean().dropna()

        if len(r_trend) > 10 and np.var(r_trend) > 1e-12 and np.var(t_trend) > 1e-12:
            pearson_corr = float(r_trend.corr(t_trend, method="pearson"))
            spearman_corr = float(r_trend.corr(t_trend, method="spearman"))
        else:
            pearson_corr, spearman_corr = 0.0, 0.0

        # 2. Short-term local 1-step delta correlation
        r_diff = r.diff().dropna()
        t_diff = t.diff().dropna()
        if len(r_diff) > 10 and np.var(r_diff) > 1e-12 and np.var(t_diff) > 1e-12:
            short_corr = float(r_diff.corr(t_diff, method="pearson"))
        else:
            short_corr = 0.0

        # 3. Directional sign consistency (What % of bars move in the exact same direction + / -)
        r_sign = np.sign(r_diff)
        t_sign = np.sign(t_diff)
        dir_acc = float(np.mean(r_sign == t_sign)) if len(r_sign) > 0 else 0.0

        if np.isnan(pearson_corr): pearson_corr = 0.0
        if np.isnan(spearman_corr): spearman_corr = 0.0
        if np.isnan(short_corr): short_corr = 0.0
        if np.isnan(dir_acc): dir_acc = 0.0

        # A preprocessing technique preserves trend if long-term Pearson > 0.40 OR Directional Accuracy > 55%
        is_preserved = abs(pearson_corr) > 0.40 or dir_acc > 0.55

        return {
            "long_term_pearson": round(pearson_corr, 4),
            "long_term_spearman": round(spearman_corr, 4),
            "short_term_corr": round(short_corr, 4),
            "directional_accuracy": round(dir_acc, 4),
            "is_trend_preserved": is_preserved,
        }

    def verify_reversibility(self, raw_series: pd.Series, inverse_series: pd.Series) -> dict:
        """
        Verifies mathematical reversibility / reconstruction fidelity after `inverse_transform()`.
        Measures Mean Squared Error (MSE) and Maximum Absolute Error between raw and inverted series.
        """
        raw_clean = raw_series.dropna()
        inv_clean = inverse_series.dropna()
        common_idx = raw_clean.index.intersection(inv_clean.index)

        if len(common_idx) == 0:
            return {"reconstruction_mse": 999.0, "max_abs_error": 999.0, "is_reversible": False}

        r = raw_clean.loc[common_idx].to_numpy(dtype=float)
        i = inv_clean.loc[common_idx].to_numpy(dtype=float)

        diff = np.abs(r - i)
        mse = float(np.mean(diff ** 2))
        max_err = float(np.max(diff))

        return {
            "reconstruction_mse": round(mse, 10),
            "max_abs_error": round(max_err, 8),
            "is_reversible": mse < 1e-8,
        }

    def evaluate_dataframe(self, raw_df: pd.DataFrame, transformed_df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs complete trend preservation analysis across all numeric features in `raw_df` vs `transformed_df`.
        Returns a cleanly structured Trend Preservation & Memory Retention Leaderboard table.
        """
        feature_cols = [
            col for col in raw_df.columns
            if col not in self.exclude_cols and col in transformed_df.columns and pd.api.types.is_numeric_dtype(raw_df[col])
        ]

        if not feature_cols:
            logger.warning("No matching numeric features found between raw and transformed DataFrames.")
            return pd.DataFrame()

        rows = []
        for col in feature_cols:
            res = self.evaluate_feature_trend(raw_series=raw_df[col], transformed_series=transformed_df[col])
            rows.append({
                "feature": col,
                "long_term_pearson": res["long_term_pearson"],
                "long_term_spearman": res["long_term_spearman"],
                "short_term_corr": res["short_term_corr"],
                "directional_accuracy": res["directional_accuracy"],
                "trend_preserved": res["is_trend_preserved"],
            })

        summary_df = pd.DataFrame(rows)
        logger.info(f"Completed Trend Preservation evaluation across {len(feature_cols)} features.")
        return summary_df
