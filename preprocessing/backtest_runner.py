# ==============================================================================
# CRYPTOSIGHT QUANTITATIVE BACKTESTING RUNNER (`backtest_runner.py`)
# ==============================================================================
# PDF Step 8 & 9: Evaluates each preprocessing technique by passing its generated
# model signals (+1, 0, -1) and unscaled original test prices directly into the
# built-in BacktestingEngine (`cryptosight.backtesting.backtest.BacktestingEngine`).
#
# NOTE: Uses exact timestamp join (`time map`) and calls built-in methods
# without modifying the `backtesting/` package at all.
# ==============================================================================

import numpy as np
import pandas as pd
from pathlib import Path
from cryptosight.utils.logger import get_logger
from cryptosight.backtesting.backtest import BacktestingEngine

logger = get_logger("PreprocessingBacktestRunner")


def run_preprocessing_backtest_leaderboard(raw_df: pd.DataFrame, predictions_dfs: dict, symbol: str = "BTC") -> pd.DataFrame:
    """
    Takes the original raw unscaled dataframe (containing open, high, low, close in USD)
    and the predictions_dfs (containing +1, 0, -1 signals for out-of-sample test tenure).
    Runs BacktestingEngine built-in methods for each preprocessing technique and returns
    the quantitative Step 8 & 9 PnL & Sharpe Leaderboard.
    """
    logger.info(f"[{symbol.upper()}] Initializing built-in BacktestingEngine for Step 8 & 9 evaluation...")
    try:
        engine = BacktestingEngine()
    except Exception as e:
        logger.error(f"Could not initialize BacktestingEngine: {e}")
        return pd.DataFrame()

    clean_sym = str(symbol).upper().replace("/", "_").replace(":", "_").replace("\\", "_").strip()
    target_tf = str(engine.config.get("timeframe", "15m")).replace("/", "_").replace(":", "_").strip()
    csv_dir = Path(__file__).resolve().parent.parent / "csv_files"
    csv_dir.mkdir(parents=True, exist_ok=True)

    leaderboard_rows = []

    # Ensure raw_df has timestamp index and clean unscaled USD OHLCV columns
    raw_ohlcv = raw_df.copy()
    if "timestamp" in raw_ohlcv.columns:
        raw_ohlcv["timestamp"] = pd.to_datetime(raw_ohlcv["timestamp"], utc=True)
        raw_ohlcv = raw_ohlcv.set_index("timestamp")
    elif isinstance(raw_ohlcv.index, pd.DatetimeIndex):
        if raw_ohlcv.index.tz is None:
            raw_ohlcv.index = pd.to_datetime(raw_ohlcv.index, utc=True)
    else:
        logger.error("Raw DataFrame has no datetime index or timestamp column!")
        return pd.DataFrame()

    required_cols = ["open", "high", "low", "close"]
    missing_cols = [c for c in required_cols if c not in raw_ohlcv.columns]
    if missing_cols:
        logger.error(f"Raw DataFrame missing required price columns for backtest: {missing_cols}")
        return pd.DataFrame()

    for pred_key, pred_df in predictions_dfs.items():
        # Key format is 'method_modelname' e.g. 'none_xgboost', 'robust_lightgbm'
        # Split on last underscore to separate method from model name
        if "_" in pred_key:
            parts = pred_key.rsplit("_", 1)
            method_name = parts[0]   # e.g. 'none', 'fracdiff'
            model_name = parts[1]    # e.g. 'xgboost', 'lightgbm'
        else:
            method_name = pred_key
            model_name = "unknown"
        logger.info(f"[{clean_sym}] Running built-in BacktestingEngine for technique: [{method_name.upper()}] | Model: [{model_name.upper()}]...")

        if pred_df.empty or "signal" not in pred_df.columns:
            logger.warning(f"[{clean_sym}] No signal column found for [{pred_key}]. Skipping...")
            continue

        # Extract only the test timestamps where predictions exist
        sig_df = pred_df.copy()
        if "timestamp" in sig_df.columns:
            sig_df["timestamp"] = pd.to_datetime(sig_df["timestamp"], utc=True)
            sig_df = sig_df.set_index("timestamp")
        elif isinstance(sig_df.index, pd.DatetimeIndex):
            if sig_df.index.tz is None:
                sig_df.index = pd.to_datetime(sig_df.index, utc=True)

        # Exact time map: Slice raw_ohlcv to the test tenure and left-join signal
        test_start = sig_df.index.min()
        test_end = sig_df.index.max()
        test_ohlcv = raw_ohlcv.loc[test_start:test_end].copy()

        # Step 3 built-in call: merge_data
        merged_df = engine.merge_data(test_ohlcv, sig_df[["signal"]])

        # Check if any trades are generated
        if (merged_df["signal"] != 0).sum() == 0:
            logger.info(f"[{clean_sym}] No trade signals (+1 / -1) triggered for [{method_name.upper()}_{model_name.upper()}].")
            leaderboard_rows.append({
                "method": method_name.upper(),
                "model": model_name.upper(),
                "status": "NO TRADES",
                "total_profit_usd": 0.0,
                "total_loss_usd": 0.0,
                "net_profit_usd": 0.0,
                "return_pct": 0.0,
                "win_rate_pct": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
            })
            continue

        # Call built-in BacktestingEngine execution step-by-step
        try:
            entries_df = engine.determine_entries(merged_df)
            if entries_df.empty:
                raise ValueError("No entries determined by engine.")
            entries_df = engine.calculate_position_size(entries_df)
            entries_df = engine.calculate_tp_sl(entries_df)
            entries_df = engine.determine_exits(merged_df, entries_df)
            entries_df = engine.calculate_fees_and_pnl(entries_df)
            ledger_df = engine.update_balance(entries_df)
        except Exception as exec_err:
            logger.warning(f"[{clean_sym}] Engine execution error for [{method_name.upper()}]: {exec_err}")
            continue

        # Clean and reorder ledger_df columns for clear Excel readability (`Trade Execution Up Front`)
        save_df = ledger_df.copy()
        if isinstance(save_df.index, pd.DatetimeIndex) or save_df.index.name in ["timestamp", "entry_time"]:
            save_df = save_df.reset_index()
            save_df.rename(columns={"index": "entry_time", "timestamp": "entry_time"}, inplace=True)

        desired_order = [
            "entry_time", "direction", "signal", "entry_price", "quantity", 
            "take_profit", "stop_loss", "exit_price", "exit_time", "exit_reason", 
            "status", "net_pnl", "perc_pnl", "cumulative_pnl", "balance"
        ]
        # Keep trade execution columns + target (`dropping open, high, low, close and 20+ indicator columns as requested`)
        extra_cols = [c for c in ["target"] if c in save_df.columns]
        keep_cols = [c for c in desired_order if c in save_df.columns] + extra_cols
        save_df = save_df[keep_cols]

        # Save individual ledger to CSV (filename includes both method and model)
        ledger_path = csv_dir / f"{clean_sym}_{target_tf}_{method_name}_{model_name}_backtest_ledger.csv"
        try:
            save_df.to_csv(ledger_path, index=False, encoding="utf-8-sig")
            logger.info(f"[{clean_sym}] Saved completed trade ledger ({method_name.upper()}) to `csv_files/`: {ledger_path}")
        except Exception as e:
            logger.warning(f"[{clean_sym}] Could not save trade ledger ({method_name.upper()}): {e}")

        # Compute Step 8 & Step 9 Institutional Performance Metrics from Ledger (`Easy Weasy Summary`)
        total_trades = len(ledger_df)
        if total_trades > 0:
            winning_trades_df = ledger_df[ledger_df["net_pnl"] > 0]
            losing_trades_df = ledger_df[ledger_df["net_pnl"] < 0]

            winning_trades = len(winning_trades_df)
            losing_trades = len(losing_trades_df)
            win_rate_pct = round((winning_trades / total_trades) * 100, 2)

            total_profit_usd = round(winning_trades_df["net_pnl"].sum(), 2)
            total_loss_usd = round(losing_trades_df["net_pnl"].sum(), 2)
            net_profit_usd = round(ledger_df["net_pnl"].sum(), 2)

            initial_balance = engine.config.get("initial_balance", 10000.0)
            return_pct = round((net_profit_usd / initial_balance) * 100, 2)
            status = "PROFITABLE ✅" if net_profit_usd > 0 else "LOSS ❌"
        else:
            winning_trades = 0
            losing_trades = 0
            win_rate_pct = 0.0
            total_profit_usd = 0.0
            total_loss_usd = 0.0
            net_profit_usd = 0.0
            return_pct = 0.0
            status = "NO TRADES"

        leaderboard_rows.append({
            "method": method_name.upper(),
            "model": model_name.upper(),
            "status": status,
            "total_profit_usd": total_profit_usd,
            "total_loss_usd": total_loss_usd,
            "net_profit_usd": net_profit_usd,
            "return_pct": return_pct,
            "win_rate_pct": win_rate_pct,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
        })

    leaderboard_df = pd.DataFrame(leaderboard_rows)
    if not leaderboard_df.empty:
        # Sort leaderboard by Net Profit & Win Rate descending (`Easy Weasy Summary`)
        leaderboard_df = leaderboard_df.sort_values(by=["net_profit_usd", "win_rate_pct"], ascending=False).reset_index(drop=True)

        # Save leaderboard CSV
        leaderboard_path = csv_dir / f"{clean_sym}_backtesting_leaderboard_report.csv"
        try:
            leaderboard_df.to_csv(leaderboard_path, index=False, encoding="utf-8-sig")
            logger.info(f"[{clean_sym}] Saved Final Backtesting Leaderboard to `csv_files/`: {leaderboard_path}")
        except Exception as e:
            logger.warning(f"Could not save leaderboard CSV: {e}")

    return leaderboard_df
