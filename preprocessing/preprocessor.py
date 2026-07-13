
import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize
from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    MaxAbsScaler,
    QuantileTransformer,
    PowerTransformer,
)
from cryptosight.utils.logger import get_logger

logger = get_logger("Preprocessor")


class DataPreprocessor:
    """
    Modular Quantitative Preprocessor.
    Receives raw features from `cryptosight.ml`, reads `pp.config.yaml`,
    and scales/transforms data dynamically without changing pipeline code.
    """

    def __init__(self, config: dict):
        self.config = config
        self.method = str(self.config.get("method")).lower()
        self.params = self.config.get("parameters")
        self.exclude_cols = set(self.config.get("exclude_columns"))
        self.scaler = self.get_scaler_object()
        logger.info(f"Initialized DataPreprocessor | Active Method: [{self.method.upper()}]")

    def get_scaler_object(self):
        """
        Function 1: Returns the appropriate scikit-learn scaler object based on `self.method`.
        If the method is custom (like `fracdiff` or `winsorize`), returns `None`.
        """
        if self.method == "standard":
            return StandardScaler()
        elif self.method == "minmax":
            return MinMaxScaler()
        elif self.method == "robust":
            return RobustScaler()
        elif self.method == "maxabs":
            return MaxAbsScaler()
        elif self.method == "quantile":
            return QuantileTransformer(output_distribution="uniform", random_state=42)
        elif self.method == "gaussian":
            return QuantileTransformer(output_distribution="normal", random_state=42)
        elif self.method == "yeo_johnson":
            return PowerTransformer(method="yeo-johnson")
        else:
            # For custom techniques (none, fracdiff, winsorize, rolling_zscore, mad_scaler, tanh_clean, kalman_filter)
            return None

    def apply_custom_transforms(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Function 2: Applies custom quantitative transformations (fracdiff, winsorize, rolling_zscore, log, mad_scaler, tanh_clean).
        Strictly IN-PLACE (No `df.copy()`) to save memory and maximize processing speed.
        """
        if self.method in ["none", "standard", "minmax", "robust", "maxabs", "quantile", "gaussian", "yeo_johnson"]:
            return df  # These are either baseline or handled by sklearn scalers

        # Get only numeric feature columns (excluding target and timestamp)
        feature_cols = [
            col for col in df.columns if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]

        if self.method == "fracdiff":
            d = float(self.params.get("frac_d", 0.35))
            # Calculate fast fixed window fractional weights
            weights = [1.0]
            for k in range(1, 100):
                w = -weights[-1] / k * (d - k + 1)
                if abs(w) < 1e-4:
                    break
                weights.append(w)
            weights = np.array(weights)

            for col in feature_cols:
                series = df[col].ffill().bfill().fillna(0.0).to_numpy(dtype=float, copy=True)
                df[col] = np.convolve(series, weights, mode="full")[: len(series)]

        elif self.method == "winsorize":
            limits = float(self.params.get("winsor_limits"))
            for col in feature_cols:
                df[col] = winsorize(df[col].to_numpy(dtype=float, copy=True), limits=(limits, limits))

        elif self.method == "log":
            for col in feature_cols:
                # Sign-preserving log (`np.log1p`) handles positive and negative returns safely without crashing
                df[col] = np.sign(df[col]) * np.log1p(np.abs(df[col]))

        elif self.method == "rolling_zscore":
            window = int(self.params.get("rolling_window", 100))
            for col in feature_cols:
                mean = df[col].rolling(window=window, min_periods=1).mean()
                std = df[col].rolling(window=window, min_periods=1).std().fillna(1e-8).replace(0, 1e-8)
                df[col] = (df[col] - mean) / std

        elif self.method == "mad_scaler":
            if not hasattr(self, "mad_stats"):
                self.mad_stats = {}
            for col in feature_cols:
                if hasattr(self, "_is_fitting") and self._is_fitting:
                    median = float(df[col].median())
                    mad = float((df[col] - median).abs().median())
                    self.mad_stats[col] = (median, mad)
                else:
                    median, mad = self.mad_stats.get(col, (float(df[col].median()), float((df[col] - df[col].median()).abs().median())))
                df[col] = (df[col] - median) / (1.4826 * mad + 1e-8)

        elif self.method == "tanh_clean":
            scale_factor = float(self.params.get("scale_factor", 0.01))
            for col in feature_cols:
                median = df[col].median()
                std = df[col].std() + 1e-8
                df[col] = 0.5 * (np.tanh(scale_factor * (df[col] - median) / std) + 1.0)

        return df

    def _sanitize_input(self, df: pd.DataFrame, feature_cols: list) -> None:
        """Sanitizes NaN and Inf values before and after processing using vectorized numpy to ensure zero crashes or NaNs (`PDF Step 3`)."""
        for col in feature_cols:
            arr = df[col].to_numpy(dtype=float, copy=True)
            arr[~np.isfinite(arr)] = np.nan
            s = pd.Series(arr, index=df.index).ffill().bfill().fillna(0.0)
            df[col] = s

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Function 3: Fits scaler on train data and transforms IN-PLACE without touching target/timestamp.
        """
        feature_cols = [col for col in df.columns if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
        self._sanitize_input(df, feature_cols)
        self._is_fitting = True

        if self.scaler:
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        else:
            self.apply_custom_transforms(df)

        self._is_fitting = False
        self._sanitize_input(df, feature_cols)
        logger.info(f"Successfully ran fit_transform | Method: [{self.method.upper()}] | Features Scaled: {len(feature_cols)}")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Function 4: Transforms test/validation features IN-PLACE using pre-fitted scaler.
        Zero data leakage since mean/std/IQR are NOT re-learned here (`.transform()` only).
        """
        feature_cols = [col for col in df.columns if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
        self._sanitize_input(df, feature_cols)
        self._is_fitting = False

        if self.scaler:
            df[feature_cols] = self.scaler.transform(df[feature_cols])
        else:
            self.apply_custom_transforms(df)

        self._sanitize_input(df, feature_cols)
        logger.info(f"Successfully ran transform | Method: [{self.method.upper()}] | Features Scaled: {len(feature_cols)}")
        return df

    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Function 5: Reverses transformations back to original values where supported (Reversibility check).
        Required by PDF Step 3 for mapping predictions back to original price scale.
        """
        feature_cols = [col for col in df.columns if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
        self._sanitize_input(df, feature_cols)

        if self.scaler and hasattr(self.scaler, "inverse_transform"):
            df[feature_cols] = self.scaler.inverse_transform(df[feature_cols])
        elif self.method == "log":
            for col in feature_cols:
                df[col] = np.sign(df[col]) * np.expm1(np.abs(df[col]))
        elif self.method == "mad_scaler" and hasattr(self, "mad_stats"):
            for col in feature_cols:
                if col in self.mad_stats:
                    median, mad = self.mad_stats[col]
                    df[col] = (df[col] * (1.4826 * mad + 1e-8)) + median

        self._sanitize_input(df, feature_cols)
        logger.info(f"Successfully ran inverse_transform | Method: [{self.method.upper()}]")
        return df



