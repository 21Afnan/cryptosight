
import numpy as np
import pandas as pd
from sklearn.preprocessing import (
    MinMaxScaler,
    RobustScaler,
    QuantileTransformer,
)
from cryptosight.utils.logger import get_logger

logger = get_logger("Preprocessor")


class DataPreprocessor:
    """
    Modular Quantitative Preprocessor.
    Receives raw features from `cryptosight.ml`, reads `pp.config.yaml`,
    and scales/transforms data dynamically without changing pipeline code.

    Supported methods: robust, minmax, fracdiff, winsorize, log, gaussian
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
        If the method is custom (like `fracdiff`, `winsorize`, or `log`), returns `None`.
        """
        if self.method == "minmax":
            return MinMaxScaler()
        elif self.method == "robust":
            return RobustScaler()
        elif self.method == "gaussian":
            return QuantileTransformer(output_distribution="normal", random_state=42)
        else:
            # For custom techniques (none, fracdiff, winsorize, log)
            return None

    def apply_custom_transforms(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Function 2: Applies custom quantitative transformations (fracdiff, winsorize, log).
        Strictly IN-PLACE (No `df.copy()`) to save memory and maximize processing speed.
        """
        if self.method in ["none", "minmax", "robust", "gaussian"]:
            return df  # These are either baseline or handled by sklearn scalers

        # Get only numeric feature columns (excluding target and timestamp)
        feature_cols = [
            col for col in df.columns if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]

        if self.method == "fracdiff":
            if not hasattr(self, "frac_weights") or (hasattr(self, "_is_fitting") and self._is_fitting):
                d = float(self.params.get("frac_d", 0.35))
                # Calculate fast fixed window fractional weights strictly on train parameters
                weights = [1.0]
                for k in range(1, 100):
                    w = -weights[-1] / k * (d - k + 1)
                    if abs(w) < 1e-4:
                        break
                    weights.append(w)
                self.frac_weights = np.array(weights)

            for col in feature_cols:
                series = df[col].ffill().bfill().fillna(0.0).to_numpy(dtype=float, copy=True)
                df[col] = np.convolve(series, self.frac_weights, mode="full")[: len(series)]

        elif self.method == "winsorize":
            if not hasattr(self, "winsor_bounds"):
                self.winsor_bounds = {}
            limits = float(self.params.get("winsor_limits", 0.01))
            for col in feature_cols:
                if hasattr(self, "_is_fitting") and self._is_fitting:
                    # Compute 1st and 99th percentile (or custom limits) strictly on train split (No Leakage)
                    lower = float(np.percentile(df[col], limits * 100.0))
                    upper = float(np.percentile(df[col], (1.0 - limits) * 100.0))
                    self.winsor_bounds[col] = (lower, upper)
                else:
                    # BUG FIX: Never re-compute from test data. If col not seen in training, skip clipping.
                    if col not in self.winsor_bounds:
                        logger.warning(f"Winsorize: column '{col}' has no learned train bounds — skipping clip to prevent data leakage.")
                        continue
                    lower, upper = self.winsor_bounds[col]
                # Apply clipping using thresholds learned strictly from train split
                df[col] = np.clip(df[col], lower, upper)

        elif self.method == "log":
            for col in feature_cols:
                # Sign-preserving log (np.log1p) handles positive and negative returns safely without crashing
                df[col] = np.sign(df[col]) * np.log1p(np.abs(df[col]))

        return df

    def _sanitize_input(self, df: pd.DataFrame, feature_cols: list) -> None:
        """Sanitizes NaN and Inf values before and after processing using vectorized numpy to ensure zero crashes or NaNs."""
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
        Zero data leakage since mean/std/IQR are NOT re-learned here (.transform() only).
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
        Required for mapping predictions back to original price scale.
        NOTE: fracdiff and winsorize are NOT reversible by design (convolution / clipping lose information).
        """
        feature_cols = [col for col in df.columns if col not in self.exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
        self._sanitize_input(df, feature_cols)

        if self.scaler and hasattr(self.scaler, "inverse_transform"):
            df[feature_cols] = self.scaler.inverse_transform(df[feature_cols])
        elif self.method == "log":
            for col in feature_cols:
                df[col] = np.sign(df[col]) * np.expm1(np.abs(df[col]))

        self._sanitize_input(df, feature_cols)
        logger.info(f"Successfully ran inverse_transform | Method: [{self.method.upper()}]")
        return df



