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
    Fast, Modular Quantitative Preprocessor.
    Scales and transforms features dynamically driven by `pconfig.yaml` without changing pipeline code.
    Strictly guarantees zero data leakage by fitting parameters on training data only.

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
        """
        Returns the scikit-learn scaler object based on `method`.
        Returns `None` for custom mathematical techniques (`fracdiff`, `winsorize`, `log`, `none`).
        """
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
        """Returns numeric feature columns while cleanly excluding target and timestamp."""
        return [
            col for col in df.columns
            if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]

    def sanitize(self, df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
        """
        Vectorized cleaning that replaces Inf with NaN, then forward/backward fills cleanly.
        Executes across the entire block at once for maximum speed.
        """
        if not feature_cols:
            return df
        df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0.0)
        return df

    def apply_custom_transforms(self, df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
        """
        Applies custom quantitative transformations (fracdiff, winsorize, log).
        Strictly preserves training parameters to prevent out-of-sample data leakage.
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
                    lower = float(np.percentile(df[col], limits * 100.0))
                    upper = float(np.percentile(df[col], (1.0 - limits) * 100.0))
                    self.winsor_bounds[col] = (lower, upper)
                else:
                    lower, upper = self.winsor_bounds[col]
                df[col] = np.clip(df[col], lower, upper)

        elif self.method == "log":
            # Sign-preserving log1p: handles positive and negative returns cleanly
            df[feature_cols] = np.sign(df[feature_cols]) * np.log1p(np.abs(df[feature_cols]))

        return df

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fits scaler on training data and transforms IN-PLACE without touching target or timestamp."""
        feature_cols = self.get_numeric_features(df)
        self.sanitize(df, feature_cols)
        self.is_fitting = True

        if self.scaler:
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        else:
            self.apply_custom_transforms(df, feature_cols)

        self.is_fitting = False
        self.sanitize(df, feature_cols)
        logger.info(f"Successfully ran fit_transform | Method: [{self.method.upper()}] | Features Scaled: {len(feature_cols)}")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms test/validation features using pre-fitted scaler parameters.
        Zero data leakage since parameters are NOT re-learned here.
        """
        feature_cols = self.get_numeric_features(df)
        self.sanitize(df, feature_cols)
        self.is_fitting = False

        if self.scaler:
            df[feature_cols] = self.scaler.transform(df[feature_cols])
        else:
            self.apply_custom_transforms(df, feature_cols)

        self.sanitize(df, feature_cols)
        logger.info(f"Successfully ran transform | Method: [{self.method.upper()}] | Features Scaled: {len(feature_cols)}")
        return df

    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reverses transformations back to original scale where supported (Reversibility check).
        NOTE: fracdiff and winsorize are NOT reversible by mathematical definition.
        """
        feature_cols = self.get_numeric_features(df)
        self.sanitize(df, feature_cols)

        if self.scaler and hasattr(self.scaler, "inverse_transform"):
            df[feature_cols] = self.scaler.inverse_transform(df[feature_cols])
        elif self.method == "log":
            df[feature_cols] = np.sign(df[feature_cols]) * np.expm1(np.abs(df[feature_cols]))

        self.sanitize(df, feature_cols)
        logger.info(f"Successfully ran inverse_transform | Method: [{self.method.upper()}]")
        return df
