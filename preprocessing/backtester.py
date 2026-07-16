import sys
from pathlib import Path

# Ensure root workspace is in sys.path
root_workspace = Path(__file__).resolve().parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

import numpy as np
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config
from cryptosight.backtesting.backtest import BacktestingEngine

logger = get_logger("PPBacktester")


class PreprocessingBacktester(BacktestingEngine):
    """
    Quantitative Preprocessing Backtester Suite.
    Reuses 100% of the trade simulation, friction (`commission/slippage`), TP/SL, and
    balance accounting functionality from `cryptosight.backtesting.backtest` without altering `backtest.py`.
    Evaluates trades strictly on original unscaled market prices (`raw_df`) using `model_predicted` signals (`+1, 0, -1`).
    """

    def __init__(self, config_path: str | Path = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent / "backtesting" / "backt_config.yaml"
        
        super().__init__(config_path=str(config_path))
        logger.info("Initialized PreprocessingBacktester (Reusing BacktestingEngine functionality)")

    def run_preprocessing_backtest(
        self,
        ohlcv_df: pd.DataFrame,
        signals_df: pd.DataFrame,
        method: str = "none",
        model: str = "unknown",
        model_metrics: dict = None,
        output_csv_path: str | Path = None,
    ) -> dict:
        """
        Executes step-by-step backtest simulation directly on original OHLCV candles
        and `model_predicted` signals (`+1, 0, -1`) using inherited `BacktestingEngine` methods.
        Returns a dictionary containing the trade ledger DataFrame and quantitative summary
        (including method, model, accuracy/metrics, win rate, total trades, and total return pct).
        """
        if ohlcv_df.empty or "close" not in ohlcv_df.columns:
            raise ValueError("Invalid ohlcv_df passed to PreprocessingBacktester.")

        ohlcv_copy = ohlcv_df.copy()
        if "timestamp" in ohlcv_copy.columns:
            ohlcv_copy["timestamp"] = pd.to_datetime(ohlcv_copy["timestamp"], utc=True)
            ohlcv_copy.set_index("timestamp", inplace=True)
        elif not isinstance(ohlcv_copy.index, pd.DatetimeIndex):
            ohlcv_copy.index = pd.to_datetime(ohlcv_copy.index, utc=True)

        signals_copy = signals_df.copy()
        if "timestamp" in signals_copy.columns:
            signals_copy["timestamp"] = pd.to_datetime(signals_copy["timestamp"], utc=True)
            signals_copy.set_index("timestamp", inplace=True)
        elif not isinstance(signals_copy.index, pd.DatetimeIndex):
            signals_copy.index = pd.to_datetime(signals_copy.index, utc=True)

        logger.info(f"Running vectorized trade simulation across {len(ohlcv_copy)} bars | Method: [{method}] | Model: [{model}]...")

        # Step 1: Merge raw OHLCV candles with model-predicted signals
        merged_df = self.merge_data(ohlcv_copy, signals_copy)

        # Step 2: Locate entry bars and calculate execution prices (open/close)
        entries_df = self.determine_entries(merged_df)
        if entries_df.empty:
            logger.warning("No entry signals triggered during this backtest simulation.")
            return {
                "ledger_df": pd.DataFrame(),
                "summary": self.compute_performance_summary(
                    ledger_df=pd.DataFrame(),
                    method=method,
                    model=model,
                    model_metrics=model_metrics,
                ),
            }

        # Step 3: Calculate position size based on balance and risk parameters
        entries_df = self.calculate_position_size(entries_df)

        # Step 4: Calculate Take Profit and Stop Loss target prices
        entries_df = self.calculate_tp_sl(entries_df)

        # Step 5: Simulate forward price action to determine exit time, price, and reason
        entries_df = self.determine_exits(merged_df, entries_df)

        # Step 6: Apply commissions, slippage frictions, and compute net PnL
        entries_df = self.calculate_fees_and_pnl(entries_df)

        # Step 7: Update running cumulative account balance
        ledger_df = self.update_balance(entries_df)

        # Clean up ledger output formatting
        cols_to_drop = ["commission", "slippage", "gross_pnl"]
        ledger_df.drop(columns=[c for c in cols_to_drop if c in ledger_df.columns], inplace=True)

        desired_order = [
            "direction", "signal", "entry_price", "quantity", "take_profit",
            "stop_loss", "exit_price", "exit_time", "exit_reason", "status",
            "net_pnl", "perc_pnl", "cumulative_pnl", "balance"
        ]
        ordered_cols = [c for c in desired_order if c in ledger_df.columns] + [c for c in ledger_df.columns if c not in desired_order]
        ledger_df = ledger_df[ordered_cols]

        if output_csv_path:
            out_path = Path(output_csv_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            ledger_df.to_csv(out_path, index=True, encoding="utf-8")
            logger.info(f"Saved backtest trade ledger to: {out_path}")

        # Compute Quantitative Performance Metrics
        summary = self.compute_performance_summary(
            ledger_df=ledger_df,
            method=method,
            model=model,
            model_metrics=model_metrics,
        )
        return {
            "ledger_df": ledger_df,
            "summary": summary,
        }

    def compute_performance_summary(
        self,
        ledger_df: pd.DataFrame,
        method: str = "none",
        model: str = "unknown",
        model_metrics: dict = None,
    ) -> dict:
        """
        Computes summary metrics: method, model, model accuracy/MAE/RMSE,
        total trades, win rate, total return pct, and max drawdown pct (without sharpe ratio).
        """
        summary = {
            "method": method,
            "model": model,
        }
        if model_metrics:
            summary.update(model_metrics)

        if ledger_df.empty or "net_pnl" not in ledger_df.columns:
            summary.update({
                "total_trades": 0,
                "win_rate": 0.0,
                "total_return_pct": 0.0,
                "max_drawdown_pct": 0.0,
            })
            return summary

        closed_trades = ledger_df[ledger_df["status"].str.lower().isin(["completed", "closed"])] if "status" in ledger_df.columns else ledger_df
        total_trades = len(closed_trades)
        if total_trades == 0:
            summary.update({
                "total_trades": 0,
                "win_rate": 0.0,
                "total_return_pct": 0.0,
                "max_drawdown_pct": 0.0,
            })
            return summary

        winning_trades = len(closed_trades[closed_trades["net_pnl"] > 0])
        win_rate = (winning_trades / total_trades) * 100.0

        initial_bal = float(self.config.get("initial_balance", 10000.0))
        final_bal = float(closed_trades["balance"].iloc[-1]) if "balance" in closed_trades.columns else initial_bal + closed_trades["net_pnl"].sum()
        total_return_pct = ((final_bal - initial_bal) / initial_bal) * 100.0

        # Peak-to-trough max drawdown
        balances = closed_trades["balance"].to_numpy(dtype=float) if "balance" in closed_trades.columns else initial_bal + closed_trades["net_pnl"].cumsum().to_numpy(dtype=float)
        peaks = np.maximum.accumulate(balances)
        drawdowns = (peaks - balances) / peaks
        max_dd_pct = float(np.max(drawdowns)) * 100.0 if len(drawdowns) > 0 else 0.0

        summary.update({
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_return_pct": round(total_return_pct, 4),
            "max_drawdown_pct": round(max_dd_pct, 2),
        })
        return summary
