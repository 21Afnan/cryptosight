"""
metrics.py — Robust & Dynamic QuantStats Statistical Engine.

Calculates all available scalar trading metrics from a returns series
using dynamic introspection (inspect.getmembers). No hardcoded wrappers needed.
"""

import inspect
import json
import logging
import math
import os
import numpy as np
import pandas as pd
import quantstats as qs

logger = logging.getLogger("StatsMetrics")

# Functions in qs.stats that do NOT return a simple scalar metric from returns alone
# (e.g. they return DataFrames, run Monte Carlo simulations, or REQUIRE a benchmark
# series as a second positional arg). Excluded from the automatic scalar loop.
_NON_SCALAR_FUNCS = {
    "compsum",
    "comp",
    "compare",
    "drawdown_details",
    "to_drawdown_series",
    "monthly_returns",
    "montecarlo",
    "montecarlo_cagr",
    "montecarlo_drawdown",
    "montecarlo_sharpe",
    "montecarlo_distribution",
    "greeks",
    "rolling_greeks",
    "remove_outliers",
    "outliers",
    # Benchmark-required functions — signature check alone can't catch these,
    # since their first param is still 'returns'. No benchmark series available yet.
    "r2",
    "r_squared",
    "information_ratio",
    "rar",
    "ror",
    "treynor_ratio",
    # Internal utilities exported inside qs.stats that are not trading metrics
    "safe_concat",
}


def normalize_returns(returns: pd.Series, is_percentage: bool) -> pd.Series:
    """
    Ensures returns are in decimal format (e.g., 0.015 instead of 1.5%).

    QuantStats expects decimal returns where 1.0 = 100%. The caller MUST
    explicitly state whether the input is in raw percentage format —
    no auto-detection here. Crypto assets can legitimately post >100%
    single-period returns (decimal 1.0+), so guessing based on magnitude
    would silently corrupt valid data. Be explicit, not clever.
    """
    if isinstance(returns, pd.DataFrame):
        returns = returns.iloc[:, 0]

    returns = returns.dropna()
    if returns.empty:
        return returns

    if is_percentage:
        return returns / 100.0

    return returns


def get_all_stat_functions() -> dict:
    """
    Discovers all public scalar functions in `quantstats.stats`.
    Returns {function_name: function_object}.
    """
    all_members = inspect.getmembers(qs.stats, predicate=inspect.isfunction)

    scalar_funcs = {}
    for name, func in all_members:
        if name.startswith("_") or name in _NON_SCALAR_FUNCS:
            continue

        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            # Ensure at least 1 param, and exactly the first param has no default value (required positional)
            required_params = [
                p for p in params 
                if p.default == inspect.Parameter.empty and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]
            if len(required_params) == 1 and len(params) >= 1 and params[0].default == inspect.Parameter.empty:
                scalar_funcs[name] = func
        except ValueError:
            continue

    return scalar_funcs


def to_json_safe(value):
    """
    Converts pandas, numpy, and float/int outputs into JSON-serializable Python types.
    Handles NaN and Infinity cleanly. Recursively sanitizes dicts/lists and stringifies keys.
    """
    if isinstance(value, (pd.Series, pd.DataFrame)):
        value = value.to_dict()
    if isinstance(value, dict):
        return {
            str(k) if not isinstance(k, (str, int, float, bool, type(None))) else k: to_json_safe(v)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple, np.ndarray)):
        return [to_json_safe(v) for v in value]
    if isinstance(value, (np.floating, float)):
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return None
        return round(val, 6)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(value)
    return value


def save_metrics_to_json(metrics: dict, filepath: str = "cryptosight/stats/metrics_report.json") -> str:
    """
    Saves the computed metrics dictionary to a formatted JSON file.
    Creates parent directories if they do not exist.
    """
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    logger.info(f"Metrics JSON report saved to: {filepath}")
    return filepath


def compute_all_metrics(returns: pd.Series, is_percentage: bool = False, save_filepath: str = None) -> dict:
    """
    Runs all discovered QuantStats metrics against the returns series.

    Args:
        returns: Time series of returns (decimal or percentage — declare via is_percentage).
        is_percentage: Set True if passing raw percentage numbers like 1.85 (instead of 0.0185).
                       No auto-detection — caller must know their own data format.
        save_filepath: Optional path (e.g., 'stats/metrics_report.json') to automatically
                       export the computed metrics dict as a JSON file.

    Returns:
        dict: {metric_name: value}. Failed metrics are NEVER silently dropped —
              they appear as {"error": "..."} so a broken metric is never
              indistinguishable from a genuinely null result.
    """
    if returns is None or len(returns) == 0:
        raise ValueError("compute_all_metrics() received an empty or None returns series.")

    clean_returns = normalize_returns(returns, is_percentage=is_percentage)
    if clean_returns.empty:
        raise ValueError("Returns series is empty after removing NaNs.")

    stat_functions = get_all_stat_functions()
    results = {}

    for name, func in stat_functions.items():
        try:
            value = func(clean_returns)
            results[name] = to_json_safe(value)
        except Exception as e:
            logger.warning(f"Metric '{name}' failed to compute: {e}")
            results[name] = {"error": str(e)}

    if save_filepath:
        save_metrics_to_json(results, save_filepath)

    return results



