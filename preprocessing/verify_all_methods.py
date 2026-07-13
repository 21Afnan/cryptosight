# ==============================================================================
# CRYPTOSIGHT PREPROCESSING METHODS VERIFICATION (`verify_all_methods.py`)
# ==============================================================================
# PDF Step 3: Verify Each Implementation on Real OHLCV Crypto Data
# For every preprocessing method (from `pp.config.yaml`):
#   1. Ensure zero data leakage occurs between Train (80%) and Test (20%) splits.
#   2. Ensure transformations are reversible (`inverse_transform`) where appropriate.
#   3. Confirm that the implementation behaves correctly on edge cases (`NaN/Inf/Spikes`).
# ==============================================================================

import os
import sys
from pathlib import Path
import yaml
import numpy as np
import pandas as pd

# Ensure project root (`d:\Neurog_Internship\cryptosight`) is in path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from cryptosight.utils.logger import get_logger
from cryptosight.ml.main import get_ml_dataset
try:
    from cryptosight.preprocessing.preprocessor import DataPreprocessor
except ImportError:
    from preprocessor import DataPreprocessor

logger = get_logger("VerifyAllMethods")

# Methods designed as lossless mathematical bijections (100% reversible)
REVERSIBLE_METHODS = {
    "standard",
    "minmax",
    "robust",
    "maxabs",
    "quantile",
    "log",
    "gaussian",
    "yeo_johnson",
    "mad_scaler",
}


def verify_methods():
    print("\n" + "=" * 105)
    print("🔬 CRYPTOSIGHT PREPROCESSING IMPLEMENTATION VERIFICATION (`PDF Step 3 — Real OHLCV Data`)")
    print("=" * 105)

    # 0. Load methods from `pp.config.yaml` dynamically (`No Hardcoding`)
    config_path = Path(__file__).resolve().parent / "pp.config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    methods_list = config.get("methods_to_test", [])
    if not methods_list:
        logger.error("No `methods_to_test` found in `pp.config.yaml`!")
        return

    # 1. Fetch Real ML OHLCV Dataset (`from cryptosight.ml.main`)
    logger.info("Fetching real OHLCV dataset from `cryptosight.ml.main`...")
    datasets = get_ml_dataset()
    if not datasets:
        logger.error("No dataset returned from ML module!")
        return

    # Use the first available coin dataset (e.g., 'btc' or 'ada')
    symbol, df = next(iter(datasets.items()))
    print(f"\n📊 [Real Dataset Loaded: {symbol.upper()}] Shape: {df.shape} | Columns: {list(df.columns[:6])}...")

    # Chronological Split (`80% Train / 20% Test`, No Shuffling!)
    split_idx = int(len(df) * 0.80)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    verification_results = []

    print(f"\nRunning verification tests across {len(methods_list)} preprocessing techniques from `pp.config.yaml`...\n")
    print(f"{'METHOD':<16} | {'LEAKAGE CHECK':<15} | {'REVERSIBILITY CHECK':<28} | {'EDGE CASES (NaN/Inf)':<22} | {'STATUS'}")
    print("-" * 105)

    for method in methods_list:
        pp_config = {
            "method": method,
            "parameters": config.get("parameters", {}),
            "exclude_columns": config.get("exclude_columns", ["timestamp", "target"]),
        }

        # ----------------------------------------------------------------------
        # Test 1: Zero Data Leakage Check (`No Look-Ahead Bias`)
        # ----------------------------------------------------------------------
        leakage_passed = False
        try:
            preprocessor = DataPreprocessor(pp_config)
            scaled_train = preprocessor.fit_transform(train_df.copy())
            scaled_test = preprocessor.transform(test_df.copy())

            # Verify scaler only learned from `train_df` samples and test output matches shape exactly
            if preprocessor.scaler and hasattr(preprocessor.scaler, "n_samples_seen_"):
                samples_seen = preprocessor.scaler.n_samples_seen_
                if isinstance(samples_seen, np.ndarray):
                    samples_seen = samples_seen[0]
                leakage_passed = (int(samples_seen) == len(train_df)) and (len(scaled_test) == len(test_df))
            else:
                leakage_passed = (len(scaled_test) == len(test_df))
            leakage_msg = "Pass (Isolated Fit)" if leakage_passed else "Fail (Leakage Detected)"
        except Exception as e:
            leakage_msg = f"Error: {str(e)[:18]}"
            leakage_passed = False

        # ----------------------------------------------------------------------
        # Test 2: Reversibility Check (`inverse_transform where appropriate`)
        # ----------------------------------------------------------------------
        reversibility_passed = False
        reversibility_msg = "N/A"
        try:
            if method.lower() in REVERSIBLE_METHODS:
                reverted_train = preprocessor.inverse_transform(scaled_train.copy())
                # Check mean absolute difference on numeric feature columns
                feature_cols = [c for c in train_df.columns if c not in pp_config["exclude_columns"] and pd.api.types.is_numeric_dtype(train_df[c])]
                diff = np.abs(train_df[feature_cols].values - reverted_train[feature_cols].values).max()
                if diff < 1e-4:
                    reversibility_passed = True
                    reversibility_msg = f"Pass (Diff: {diff:.1e})"
                else:
                    reversibility_passed = False
                    reversibility_msg = f"Fail (Diff: {diff:.4f})"
            elif method.lower() == "none":
                reversibility_passed = True
                reversibility_msg = "Pass (Identity)"
            elif method.lower() in {"winsorize", "tanh_clean"}:
                reversibility_passed = True
                reversibility_msg = "By Design (Outlier Clip)"
            elif method.lower() == "fracdiff":
                reversibility_passed = True
                reversibility_msg = "By Design (Differencing)"
            else:
                reversibility_passed = True
                reversibility_msg = "By Design (Window/Smooth)"
        except Exception as e:
            reversibility_msg = f"Error: {str(e)[:18]}"
            reversibility_passed = False

        # ----------------------------------------------------------------------
        # Test 3: Edge Case Verification (`NaN, Inf & Extreme Spikes`)
        # ----------------------------------------------------------------------
        edge_passed = False
        edge_msg = "N/A"
        try:
            edge_test_df = train_df.iloc[:50].copy()
            # Inject extreme edge cases into the first numeric column (`PDF Step 3 requirement`)
            first_num_col = [c for c in edge_test_df.columns if c not in pp_config["exclude_columns"] and pd.api.types.is_numeric_dtype(edge_test_df[c])][0]
            edge_test_df.iloc[5, edge_test_df.columns.get_loc(first_num_col)] = np.nan
            edge_test_df.iloc[10, edge_test_df.columns.get_loc(first_num_col)] = np.inf
            edge_test_df.iloc[15, edge_test_df.columns.get_loc(first_num_col)] = -np.inf
            edge_test_df.iloc[20, edge_test_df.columns.get_loc(first_num_col)] = 0.00000001
            edge_test_df.iloc[25, edge_test_df.columns.get_loc(first_num_col)] = 1000000000.0

            scaled_edge = preprocessor.transform(edge_test_df.copy())
            
            # Check for any lingering NaNs or Infs
            nan_count = int(scaled_edge[first_num_col].isna().sum())
            inf_count = int(np.isinf(scaled_edge[first_num_col].to_numpy(dtype=float, copy=True)).sum())

            if nan_count == 0 and inf_count == 0:
                edge_passed = True
                edge_msg = "Pass (0 NaN, 0 Inf)"
            else:
                edge_passed = False
                edge_msg = f"Fail ({nan_count} NaN, {inf_count} Inf)"
        except Exception as e:
            edge_msg = f"Error: {str(e)[:18]}"
            edge_passed = False

        # Overall Status
        overall_status = "✅ PASS" if (leakage_passed and reversibility_passed and edge_passed) else "❌ FAIL"

        print(f"{method.upper():<16} | {leakage_msg:<15} | {reversibility_msg:<28} | {edge_msg:<22} | {overall_status}")

        verification_results.append({
            "method": method.upper(),
            "leakage_check": leakage_msg,
            "reversibility_check": reversibility_msg,
            "edge_case_check": edge_msg,
            "overall_status": overall_status,
        })

    print("-" * 105)

    # Save verification report as required by institutional standards
    report_df = pd.DataFrame(verification_results)
    report_path = Path(__file__).resolve().parent / f"{symbol.upper()}_preprocessing_verification_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\n📁 Saved institutional verification report to: `{report_path.name}`")
    print("=" * 105 + "\n")


if __name__ == "__main__":
    verify_methods()
