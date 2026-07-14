# ==============================================================================
# CRYPTOSIGHT QUANTITATIVE TREND PRESERVATION ANALYZER (`trend_preservation.py`)
# ==============================================================================
# PDF Step 5: Evaluates whether each preprocessing method preserves meaningful market trends.
# Measures both Long-Term Trend Retention (Macro Cycles) and Local Trend Retention (Momentum).
# NOTE: Pure computational module — all CSV exporting is centralized inside `main.py`.
# ==============================================================================

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr
from cryptosight.utils.logger import get_logger

logger = get_logger("TrendPreservationAnalyzer")


class TrendPreservationAnalyzer:
    """
    Step 5: Evaluates Long-Term and Local Trend Retention across preprocessing techniques vs Raw Baseline (`NONE`).

    Quantitative Metrics Applied:
    1. Long-Term Trend Retention: Spearman rank correlation of 100-candle Rolling Macro SMA.
       - Evaluates if macro Bull/Bear cycles are preserved without direction inversion.
    2. Local Trend Retention: Pearson correlation of 10-candle Momentum (`diff(10)`).
       - Evaluates if immediate short-term breakouts and price action shocks keep their exact shape.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.exclude_cols = set(self.config.get("exclude_columns", ["timestamp", "target"]))

        # Explicit Quantitative Constants (`Clean & Self-Contained without external config complexity`)
        self.min_series_len = 30
        self.long_term_window = 100
        self.long_term_window_divisor = 3
        self.local_term_lag = 10
        self.burn_in_rows = 50

        # Institutional Correlation Thresholds
        self.preserved_corr_threshold = 0.65
        self.excellent_pct_cutoff = 80.0
        self.excellent_corr_cutoff = 0.70
        self.moderate_pct_cutoff = 50.0
        self.moderate_corr_cutoff = 0.50

        logger.info(
            f"Initialized TrendPreservationAnalyzer (`Self-Contained Institutional Constants`) | "
            f"long_term_window={self.long_term_window}, local_term_lag={self.local_term_lag}"
        )

    def analyze_feature_trend(self, raw_series: pd.Series, proc_series: pd.Series) -> dict:
        """
        Function 1: Compares a single preprocessed numerical series against the raw (`none`) baseline.
        Returns Long-Term Correlation and Local Momentum Correlation.
        """
        min_len = min(len(raw_series), len(proc_series))
        if min_len < self.min_series_len:
            return {"long_term_corr": 0.0, "local_term_corr": 0.0, "is_preserved": False}

        raw_clean = raw_series.iloc[:min_len].ffill().bfill().fillna(0.0).to_numpy(dtype=float, copy=True)
        proc_clean = proc_series.iloc[:min_len].ffill().bfill().fillna(0.0).to_numpy(dtype=float, copy=True)

        # Drop burn-in rows so transform edge-effects (e.g. fracdiff convolution warm-up)
        # don't contaminate the trend-retention read
        if min_len > self.burn_in_rows * 2:
            raw_clean = raw_clean[self.burn_in_rows:]
            proc_clean = proc_clean[self.burn_in_rows:]

        valid_idx = np.isfinite(raw_clean) & np.isfinite(proc_clean)
        if np.sum(valid_idx) < self.min_series_len:
            return {"long_term_corr": 0.0, "local_term_corr": 0.0, "is_preserved": False}

        raw_clean = raw_clean[valid_idx]
        proc_clean = proc_clean[valid_idx]

        # 1. Long-Term Trend Retention (`Rolling 100-candle Macro SMA`)
        window_long = min(self.long_term_window, len(raw_clean) // self.long_term_window_divisor)
        if window_long > 5:
            raw_macro = pd.Series(raw_clean).rolling(window=window_long).mean().dropna()
            proc_macro = pd.Series(proc_clean).rolling(window=window_long).mean().dropna()
            try:
                # Spearman Rank Correlation handles non-linear/monotonic transforms (`Robust/MinMax/Log/Gaussian`)
                long_term_corr, _ = spearmanr(raw_macro, proc_macro)
                if np.isnan(long_term_corr): long_term_corr = 0.0
            except Exception:
                long_term_corr = 0.0
        else:
            long_term_corr = 0.0

        # 2. Local Trend Retention (`10-candle Immediate Momentum / First Difference`)
        try:
            lag = self.local_term_lag
            if len(raw_clean) > lag * 2:
                raw_local = raw_clean[lag:] - raw_clean[:-lag]
                proc_local = proc_clean[lag:] - proc_clean[:-lag]
                local_corr, _ = pearsonr(raw_local, proc_local)
                if np.isnan(local_corr): local_corr = 0.0
            else:
                local_corr = 0.0
        except Exception:
            local_corr = 0.0

        # Institutional Thresholds: both macro and local correlation must clear the bar
        is_preserved = (long_term_corr >= self.preserved_corr_threshold) and (local_corr >= self.preserved_corr_threshold)

        return {
            "long_term_corr": round(float(long_term_corr), 4),
            "local_term_corr": round(float(local_corr), 4),
            "is_preserved": is_preserved
        }

    def evaluate_preprocessed_datasets(self, preprocessed_dfs: dict) -> pd.DataFrame:
        """
        Function 2: Loops across all preprocessed DataFrames (`from main.py / CryptoMLClassifier`),
        uses `none` (`raw baseline`) as reference, computes average retention across numeric features,
        and returns a clean structured DataFrame report for `main.py` to display and save.
        """
        if not preprocessed_dfs:
            logger.error("No preprocessed datasets provided for trend preservation evaluation!")
            return pd.DataFrame()

        # Find raw baseline dataset (`none` or first available)
        raw_df = preprocessed_dfs.get("none")
        if raw_df is None:
            raw_df = preprocessed_dfs.get("NONE")
        if raw_df is None:
            raw_df = next(iter(preprocessed_dfs.values()))
            logger.warning("Baseline (`NONE`) not explicitly found. Using first available dataset as reference.")

        feature_cols = [c for c in raw_df.columns if c not in self.exclude_cols and pd.api.types.is_numeric_dtype(raw_df[c])]
        if not feature_cols:
            logger.error("No numeric feature columns found in baseline dataset!")
            return pd.DataFrame()

        results = []

        for method_name, proc_df in preprocessed_dfs.items():
            logger.info(f"Running Trend Preservation analysis for method: [{method_name.upper()}]...")
            long_corrs, local_corrs, preserved_counts = [], [], 0
            missing_cols = []

            for col in feature_cols:
                if col not in proc_df.columns:
                    missing_cols.append(col)
                    continue
                metrics = self.analyze_feature_trend(raw_df[col], proc_df[col])
                long_corrs.append(metrics["long_term_corr"])
                local_corrs.append(metrics["local_term_corr"])
                if metrics["is_preserved"]:
                    preserved_counts += 1

            if missing_cols:
                logger.warning(f"[{method_name.upper()}] Missing {len(missing_cols)} columns vs baseline: {missing_cols}")

            if not long_corrs:
                logger.warning(f"[{method_name.upper()}] No comparable columns found — skipping.")
                continue

            avg_long = float(np.mean(long_corrs))
            avg_local = float(np.mean(local_corrs))
            evaluated_count = len(long_corrs)
            retention_pct = round((preserved_counts / evaluated_count) * 100.0, 1)

            # Assign institutional status label
            if retention_pct >= self.excellent_pct_cutoff or (avg_long >= self.excellent_corr_cutoff and avg_local >= self.excellent_corr_cutoff):
                status_label = "EXCELLENT PRESERVATION ✅"
            elif retention_pct >= self.moderate_pct_cutoff or (avg_long >= self.moderate_corr_cutoff and avg_local >= self.moderate_corr_cutoff):
                status_label = "MODERATE PRESERVATION ⚠️"
            else:
                status_label = "DISTORTED / LOST ❌"

            results.append({
                "method": method_name.upper(),
                "long_term_trend_corr": round(avg_long, 4),
                "local_term_momentum_corr": round(avg_local, 4),
                "trend_retention_score": f"{retention_pct}% ({preserved_counts}/{evaluated_count})",
                "preservation_status": status_label
            })

        report_df = pd.DataFrame(results)
        logger.info("Successfully completed Trend Preservation evaluation across all methods.")
        return report_df


if __name__ == "__main__":
    print("📈 TrendPreservationAnalyzer is a quantitative module. Please run via `python preprocessing/main.py`.")
