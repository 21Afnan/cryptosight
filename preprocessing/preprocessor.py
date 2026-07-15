import numpy as np
import pandas as pd
from sklearn.preprocessing import (
    MinMaxScaler,
    RobustScaler,
    StandardScaler,
    QuantileTransformer,
)
from cryptosight.utils.logger import get_logger

logger = get_logger("Preprocessor")


class DataPreprocessor:
    """
    Fast, Memory-Optimized Quantitative Preprocessor.
    Scales and transforms features dynamically driven by `pconfig.yaml` without changing pipeline code.
    Guarantees zero data leakage and zero memory fragmentation by learning parameters on the
    training slice (`train_ratio`) and transforming in-place without `pd.concat` or extra copies.

    Supported methods: robust, minmax, standard, fracdiff, winsorize, log, gaussian, none
    """

    def __init__(self, config: dict):
        self.config = config or {}
        self.method = str(self.config.get("method", "robust")).lower()
        self.params = self.config.get("parameters") or {}
        self.exclude_cols = set(self.config.get("exclude_columns") or ["timestamp", "target"])
        self.scaler = self.get_scaler_object()
        self.is_fitting = False
        self.frac_weights = None
        self.winsor_bounds = {}
        logger.info(f"Initialized DataPreprocessor | Active Method: [{self.method.upper()}]")

    def get_scaler_object(self):
        """Returns the scikit-learn scaler object based on `method`."""
        if self.method == "minmax":
            return MinMaxScaler()
        elif self.method == "robust":
            return RobustScaler()
        elif self.method in ["standard", "zscore"]:
            return StandardScaler()
        elif self.method == "gaussian":
            return QuantileTransformer(output_distribution="normal", random_state=42)
        return None

    def get_numeric_features(self, df: pd.DataFrame) -> list[str]:
        """Returns numeric feature columns while excluding target and timestamp cleanly."""
        return [
            col for col in df.columns
            if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]

    def sanitize(self, df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
        """
        In-place vectorized cleaning replacing Inf with NaN, then forward/backward filling.
        Executes across the entire feature block at once for maximum speed and zero memory allocation.
        """
        if not feature_cols:
            return df
        df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0.0)
        return df

    def apply_custom_transforms(self, df: pd.DataFrame, feature_cols: list[str], split_idx: int = None) -> pd.DataFrame:
        """
        Applies custom quantitative transformations (`fracdiff`, `winsorize`, `log`) in-place.
        Learns limits strictly from `iloc[:split_idx]` (train slice) to prevent data leakage.
        """
        if self.method in ["none", "minmax", "robust", "standard", "zscore", "gaussian"] or not feature_cols:
            return df

        if self.method == "fracdiff":
            if self.frac_weights is None or self.is_fitting:
                d = float(self.params.get("frac_d", 0.35))
                weights = [1.0]
                for k in range(1, 100):
                    w = -weights[-1] / k * (d - k + 1)
                    if abs(w) < 1e-4:
                        break
                    weights.append(w)
                self.frac_weights = np.array(weights, dtype=float)

            for col in feature_cols:
                series = df[col].to_numpy(dtype=float, copy=True)
                df[col] = np.convolve(series, self.frac_weights, mode="full")[: len(series)]

        elif self.method == "winsorize":
            limits = float(self.params.get("winsor_limits", 0.01))
            for col in feature_cols:
                if self.is_fitting or col not in self.winsor_bounds:
                    # Learn clipping percentiles strictly on the training slice (iloc[:split_idx])
                    train_slice = df[col].iloc[:split_idx] if split_idx and split_idx > 0 else df[col]
                    lower = float(np.percentile(train_slice, limits * 100.0))
                    upper = float(np.percentile(train_slice, (1.0 - limits) * 100.0))
                    self.winsor_bounds[col] = (lower, upper)
                else:
                    lower, upper = self.winsor_bounds[col]
                # Clip entire feature in-place using exact thresholds learned from training data
                df[col] = np.clip(df[col], lower, upper)

        elif self.method == "log":
            # Sign-preserving log1p: in-place block transformation
            df[feature_cols] = np.sign(df[feature_cols]) * np.log1p(np.abs(df[feature_cols]))

        return df

    def fit_transform(self, df: pd.DataFrame, train_ratio: float = 0.80) -> pd.DataFrame:
        """
        Memory-Optimized Fit & Transform:
        1. Fits scaler strictly on the first `train_ratio` rows (`df.iloc[:split_idx]`).
        2. Transforms all rows (`df`) in-place without creating split copies or running `pd.concat`.
        """
        feature_cols = self.get_numeric_features(df)
        self.sanitize(df, feature_cols)
        self.is_fitting = True

        split_idx = int(len(df) * train_ratio)
        if split_idx <= 0 or split_idx >= len(df):
            split_idx = len(df)

        if self.scaler:
            # Fit strictly on train slice without copying the full DataFrame
            self.scaler.fit(df[feature_cols].iloc[:split_idx])
            # Transform full DataFrame in-place
            df[feature_cols] = self.scaler.transform(df[feature_cols])
        else:
            self.apply_custom_transforms(df, feature_cols, split_idx=split_idx)

        self.is_fitting = False
        self.sanitize(df, feature_cols)
        logger.info(f"Successfully ran fit_transform | Method: [{self.method.upper()}] | Features Scaled: {len(feature_cols)}")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms validation/test features in-place using pre-fitted parameters."""
        feature_cols = self.get_numeric_features(df)
        self.sanitize(df, feature_cols)
        self.is_fitting = False

        if self.scaler:
            df[feature_cols] = self.scaler.transform(df[feature_cols])
        else:
            self.apply_custom_transforms(df, feature_cols, split_idx=len(df))

        self.sanitize(df, feature_cols)
        logger.info(f"Successfully ran transform | Method: [{self.method.upper()}] | Features Scaled: {len(feature_cols)}")
        return df

    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reverses transformations back to original scale where supported."""
        feature_cols = self.get_numeric_features(df)
        self.sanitize(df, feature_cols)

        if self.scaler and hasattr(self.scaler, "inverse_transform"):
            df[feature_cols] = self.scaler.inverse_transform(df[feature_cols])
        elif self.method == "log":
            df[feature_cols] = np.sign(df[feature_cols]) * np.expm1(np.abs(df[feature_cols]))

        self.sanitize(df, feature_cols)
        logger.info(f"Successfully ran inverse_transform | Method: [{self.method.upper()}]")
        return df
