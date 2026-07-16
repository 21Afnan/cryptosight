import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from statsmodels.tsa.stattools import adfuller

class QuantPreprocessor:
    """
    State-of-the-Art Quantitative Preprocessing Pipeline.
    Chains three essential preprocessing techniques sequentially:
      1. Fractional Differencing (FracDiff) - achieves stationarity while preserving memory
      2. Winsorization - clips extreme outlier spikes
      3. RobustScaler - centers features around median and standardizes using IQR
      
    Guarantees zero data leakage by fitting parameters ONLY on the training dataset
    and applying the pre-fitted parameters to validation and test datasets.
    """

    def __init__(self, winsor_limit: float = 0.01, frac_step: float = 0.05):
        self.winsor_limit = winsor_limit
        self.frac_step = frac_step
        self.feature_cols = []
        self.optimal_d_values = {}
        self.winsor_bounds = {}
        self.scaler = RobustScaler()

    def get_frac_weights(self, d: float, size: int) -> np.ndarray:
        """Calculates fractional differencing weights with a threshold decay filter."""
        weights = [1.0]
        for k in range(1, size):
            w = -weights[-1] / k * (d - k + 1)
            # Decay filter to prevent massive NaN transient windows
            if abs(w) < 1e-4:
                break
            weights.append(w)
        return np.array(weights, dtype=float)

    def transform_frac_diff(self, series: pd.Series, d: float) -> pd.Series:
        """Applies fractional differencing to a single series using fast convolution."""
        # Clean/fill missing values temporarily for convolution stability
        clean_vals = series.ffill().bfill().fillna(0.0).values
        weights = self.get_frac_weights(d, len(series))
        
        # Convolve series with weights and truncate to original length
        convolved = np.convolve(clean_vals, weights, mode="full")[:len(series)]
        return pd.Series(convolved, index=series.index)

    def find_optimal_d(self, series: pd.Series) -> float:
        """Discovers the minimum d required to make the series stationary using the ADF test."""
        clean = series.dropna().values
        if len(clean) < 20 or np.var(clean) < 1e-12:
            return 0.0  # Already stationary or zero variance

        # Test if the raw series is already stationary
        try:
            if adfuller(clean, autolag="AIC")[1] < 0.05:
                return 0.0
        except Exception:
            pass

        # Loop to find the smallest d that achieves stationarity
        d_candidate = self.frac_step
        while d_candidate <= 1.0:
            diffed = self.transform_frac_diff(series, d_candidate)
            # Drop the transient warm-up bars to run a clean ADF test
            test_vals = diffed.iloc[100:].dropna().values
            if len(test_vals) < 20:
                d_candidate += self.frac_step
                continue
            try:
                p_val = adfuller(test_vals, autolag="AIC")[1]
                if p_val < 0.05:
                    return round(d_candidate, 2)
            except Exception:
                pass
            d_candidate += self.frac_step
        return 1.0  # Fallback to integer 1st difference

    def fit(self, train_df: pd.DataFrame):
        """
        Fits all preprocessing parameters STRICTLY on the training DataFrame.
        Learns optimal FracDiff d, Winsorization quantiles, and RobustScaler parameters.
        """
        # 1. Identify numeric feature columns (ignore timestamps and target column)
        self.feature_cols = [
            col for col in train_df.columns 
            if col not in ["timestamp", "target"] and pd.api.types.is_numeric_dtype(train_df[col])
        ]

        # Create a temporary DataFrame to step-by-step train the parameters
        temp_df = train_df.copy()

        # 2. Fit and apply FracDiff
        for col in self.feature_cols:
            opt_d = self.find_optimal_d(train_df[col])
            self.optimal_d_values[col] = opt_d
            if opt_d > 0.0:
                temp_df[col] = self.transform_frac_diff(temp_df[col], opt_d)

        # 3. Fit Winsorization bounds on the stationary (differenced) data
        for col in self.feature_cols:
            lower = np.percentile(temp_df[col].dropna(), self.winsor_limit * 100.0)
            upper = np.percentile(temp_df[col].dropna(), (1.0 - self.winsor_limit) * 100.0)
            self.winsor_bounds[col] = (lower, upper)
            
            # Apply Winsorization to temp_df before learning scaling parameters
            temp_df[col] = np.clip(temp_df[col], lower, upper)

        # 4. Fit RobustScaler on the stationary & winsorized training features
        # Fill any transient NaNs to ensure RobustScaler fits cleanly
        clean_features = temp_df[self.feature_cols].ffill().bfill().fillna(0.0)
        self.scaler.fit(clean_features)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms any DataFrame (train, validation, or test) using the pre-fitted parameters.
        Maintains strict separation to prevent look-ahead data leakage.
        """
        transformed_df = df.copy()

        for col in self.feature_cols:
            # Step 1: Apply Fractional Differencing
            opt_d = self.optimal_d_values.get(col, 0.0)
            if opt_d > 0.0:
                transformed_df[col] = self.transform_frac_diff(transformed_df[col], opt_d)

            # Step 2: Apply Winsorization (outlier clipping)
            lower, upper = self.winsor_bounds.get(col, (-np.inf, np.inf))
            transformed_df[col] = np.clip(transformed_df[col], lower, upper)

        # Step 3: Apply RobustScaler centering & scaling
        clean_features = transformed_df[self.feature_cols].ffill().bfill().fillna(0.0)
        transformed_df[self.feature_cols] = self.scaler.transform(clean_features)

        return transformed_df

    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reverses the RobustScaler scaling back to the winsorized/differenced scale.
        Note: Winsorization clipping and Fractional Differencing are lossy operations 
        that cannot be fully mathematically reversed on features without historical raw price bounds.
        """
        transformed_df = df.copy()
        
        # 1. Reverse RobustScaler
        clean_features = transformed_df[self.feature_cols].ffill().bfill().fillna(0.0)
        transformed_df[self.feature_cols] = self.scaler.inverse_transform(clean_features)
        
        return transformed_df

    def save(self) -> str:
        """
        Saves the fitted preprocessor object (.joblib) to the ml/artifacts/preprocessors/ directory,
        and saves its learned parameters (YAML) to the ml/artifacts/configs/ directory.
        """
        import joblib
        from cryptosight.utils.config import get_ml_artifacts_dir, save_config_artifact

        # 1. Save preprocessor metadata as YAML
        preproc_meta = {
            "winsor_limit": self.winsor_limit,
            "frac_step": self.frac_step,
            "feature_cols": self.feature_cols,
            "optimal_d_values": self.optimal_d_values,
            # Convert winsor bounds to standard float lists for YAML serializability
            "winsor_bounds": {
                col: [float(bounds[0]), float(bounds[1])] 
                for col, bounds in self.winsor_bounds.items()
            }
        }
        # Save YAML in ml/artifacts/configs/preproc.yaml
        save_config_artifact(preproc_meta, "preproc.yaml", asset_type="config")

        # 2. Save fitted object using joblib in ml/artifacts/preprocessors/preprocessor.joblib
        preproc_dir = get_ml_artifacts_dir("preprocessor")
        target_path = preproc_dir / "preprocessor.joblib"
        try:
            joblib.dump(self, target_path)
            return str(target_path)
        except Exception as e:
            print(f"Warning: Failed to save preprocessor joblib object to {target_path}: {e}")
            return ""

  