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

    def clean(self, df_subset: pd.DataFrame) -> pd.DataFrame:
        """Cleans and fills missing values using forward fill, backward fill, and zero fill."""
        return df_subset.ffill().bfill().fillna(0.0)

    def apply_fracdiff_and_winsorize(self, series: pd.Series, col: str, fitting: bool = False) -> pd.Series:
        """Applies pre-fitted fractional differencing and winsorization clipping to a column series."""
        out = series
        opt_d = self.optimal_d_values.get(col, 0.0)
        if opt_d > 0.0:
            out = self.transform_frac_diff(out, opt_d)
        lower, upper = self.winsor_bounds.get(col, (-np.inf, np.inf))
        out = pd.Series(np.clip(out, lower, upper), index=series.index)
        return out

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
        clean_vals = self.clean(series).values
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

        # 2. Learn optimal FracDiff d values and Winsorization bounds on the stationary data
        for col in self.feature_cols:
            opt_d = self.find_optimal_d(train_df[col])
            self.optimal_d_values[col] = opt_d
            diffed = self.transform_frac_diff(train_df[col], opt_d) if opt_d > 0.0 else train_df[col]

            lower = np.percentile(diffed.dropna(), self.winsor_limit * 100.0)
            upper = np.percentile(diffed.dropna(), (1.0 - self.winsor_limit) * 100.0)
            self.winsor_bounds[col] = (lower, upper)

            # Reuse already-computed diffed series directly for winsorizing/clipping into temp_df[col]
            temp_df[col] = pd.Series(np.clip(diffed, lower, upper), index=train_df[col].index)

        # 3. Fit RobustScaler on the stationary & winsorized training features
        clean_features = self.clean(temp_df[self.feature_cols])
        self.scaler.fit(clean_features)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms any DataFrame (train, validation, or test) using the pre-fitted parameters.
        Maintains strict separation to prevent look-ahead data leakage.
        """
        transformed_df = df.copy()

        for col in self.feature_cols:
            transformed_df[col] = self.apply_fracdiff_and_winsorize(transformed_df[col], col, fitting=False)

        # Step 3: Apply RobustScaler centering & scaling
        clean_features = self.clean(transformed_df[self.feature_cols])
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
        clean_features = self.clean(transformed_df[self.feature_cols])
        transformed_df[self.feature_cols] = self.scaler.inverse_transform(clean_features)
        
        return transformed_df

    def get_metadata(self) -> dict:
        """
        Returns learned preprocessor metadata dictionary to be stored in the unified quant pipeline JSON.
        """
        return {
            "winsor_limit": self.winsor_limit,
            "frac_step": self.frac_step,
            "feature_cols": self.feature_cols,
            "optimal_d_values": self.optimal_d_values,
            "winsor_bounds": {
                col: [float(bounds[0]), float(bounds[1])] 
                for col, bounds in self.winsor_bounds.items()
            }
        }

    def save(self, symbol: str, exchange: str, timeframe: str) -> str:
        """
        Saves the fitted preprocessor object (.joblib) to the ml/artifacts/preprocessor/ directory.
        """
        import joblib
        from cryptosight.utils.config import get_ml_artifacts_dir

        preproc_dir = get_ml_artifacts_dir("preprocessor")
        target_path = preproc_dir / f"{exchange}_{symbol}_{timeframe}_preprocessor.joblib"
        try:
            joblib.dump(self, target_path)
            return str(target_path)
        except Exception as e:
            print(f"Warning: Failed to save preprocessor joblib object to {target_path}: {e}")
            return ""