# ==============================================================================
# CRYPTOSIGHT BACKTEST LEDGER & THRESHOLD ANALYSIS (`analyze_backtest_ledger.py`)
# ==============================================================================
import sys
import codecs
import pandas as pd
import numpy as np
from pathlib import Path

# Fix Windows console encoding for smooth printing
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def analyze_ledger(file_name: str = "BTC_1m_ACTUAL_DF_NO_MODEL (Test Split 20%)_backtest_ledger.csv", threshold: float = 0.002):
    csv_dir = Path(__file__).resolve().parent.parent / "csv_files"
    file_path = csv_dir / file_name

    if not file_path.exists():
        print(f"\n[Error] Ledger file not found at: {file_path}")
        print("Available ledgers in `csv_files/`:")
        for f in csv_dir.glob("*ledger*.csv"):
            print(f"  -> {f.name}")
        return

    print("\n" + "=" * 105)
    print(f"[INSTITUTIONAL TRADE LEDGER & THRESHOLD ANALYSIS]: {file_name}")
    print("=" * 105)

    df = pd.read_csv(file_path)
    total_trades = len(df)

    if total_trades == 0:
        print("[Warning] Ledger is empty (No trades recorded).")
        return

    # 1. Direction Breakdown (`Long vs Short`)
    long_trades = df[df["direction"] == "Long"]
    short_trades = df[df["direction"] == "Short"]
    num_long = len(long_trades)
    num_short = len(short_trades)

    # 2. Outcome Breakdown (`Winners vs Losers`)
    winners = df[df["net_pnl"] > 0]
    losers = df[df["net_pnl"] < 0]
    num_win = len(winners)
    num_loss = len(losers)

    total_profit = winners["net_pnl"].sum()
    total_loss = losers["net_pnl"].sum()
    net_pnl = df["net_pnl"].sum()
    win_rate = (num_win / total_trades) * 100 if total_trades > 0 else 0.0

    long_win_rate = (len(long_trades[long_trades["net_pnl"] > 0]) / num_long * 100) if num_long > 0 else 0.0
    short_win_rate = (len(short_trades[short_trades["net_pnl"] > 0]) / num_short * 100) if num_short > 0 else 0.0

    # 3. Exit Reason Breakdown
    tp_exits = len(df[df["exit_reason"] == "take_profit"])
    sl_exits = len(df[df["exit_reason"] == "stop_loss"])

    print(f"--> SUMMARY OVERVIEW:")
    print(f"   * Total Trades Executed : {total_trades}")
    print(f"   * Long Trades           : {num_long} ({num_long/total_trades*100:.1f}%) | Win Rate: {long_win_rate:.2f}%")
    print(f"   * Short Trades          : {num_short} ({num_short/total_trades*100:.1f}%) | Win Rate: {short_win_rate:.2f}%")
    print("-" * 105)
    print(f"--> PROFIT & LOSS STATS:")
    print(f"   * Winning Trades (TP)   : {num_win} ({win_rate:.2f}% Win Rate) | Total Profit: +${total_profit:,.2f}")
    print(f"   * Losing Trades (SL)    : {num_loss} ({100-win_rate:.2f}% Loss Rate) | Total Loss  : -${abs(total_loss):,.2f}")
    print(f"   * NET PnL ($)           : {'+' if net_pnl >= 0 else ''}${net_pnl:,.2f}")
    print(f"   * Exits via Take Profit : {tp_exits}")
    print(f"   * Exits via Stop Loss   : {sl_exits}")
    print("=" * 105)

    # 4. Quantitative Threshold Analysis (`0.002` Conviction Filter vs Noise)
    print("\n" + "=" * 105)
    print(f"--> THRESHOLD ({threshold} / {threshold*100:.2f}%) & NOISE REDUCTION INSTITUTIONAL BREAKDOWN")
    print("=" * 105)
    
    if "target" in df.columns:
        if df["target"].nunique() > 10:
            noisy_trades = df[df["target"].abs() < threshold]
            conviction_trades = df[df["target"].abs() >= threshold]
            print(f"   * Total Trades in Raw Ledger      : {total_trades}")
            print(f"   * Noisy/Sideways Trades (< 0.2%)  : {len(noisy_trades)} (Net PnL: ${noisy_trades['net_pnl'].sum():,.2f})")
            print(f"   * High-Conviction Trades (>= 0.2%): {len(conviction_trades)} (Net PnL: ${conviction_trades['net_pnl'].sum():,.2f})")
        else:
            print(f"   * Target Column Format : Discrete Classification ({sorted(df['target'].unique())})")
            print(f"   * When Target is Discrete (-1, 0, +1), every single directional bar triggers a trade without")
            print(f"     checking the magnitude of expected return. Across {total_trades} trades, 0.2% round-trip fees")
            print(f"     ($140 per trade on $70k BTC) eat ~${total_trades * 14.0:.2f} in total commissions!")

    print("\n--> 3 INSTITUTIONAL SOLUTIONS TO REDUCE NOISE IN CLASSIFICATION:")
    print("   1. Switch to Regression Task (`model_task: regression` in `pp.config.yaml`):")
    print(f"      -> Regression predicts continuous return (e.g. +0.0035). By applying `regression_signal_threshold: {threshold}`,")
    print("         the model blocks 90% of sideways/noisy trades and only trades strong breakouts (where return > 0.2%).")
    print("   2. Add Probability Confidence Filter in Classification:")
    print("      -> Instead of entering when `predict_proba() > 0.50`, enforce `predict_proba() > 0.65 or 0.70`.")
    print("         This filters out weak 51% vs 49% coin-flip candles.")
    print("   3. Add ATR / Volatility Gate:")
    print("      -> Only allow trade entries (`signal = +1/-1`) if `ind_ATR_14 > 0.002 * close` (i.e. bar volatility >= 0.2%).")
    print("=" * 105 + "\n")


if __name__ == "__main__":
    analyze_ledger("BTC_1m_ACTUAL_DF_NO_MODEL (Test Split 20%)_backtest_ledger.csv", threshold=0.002)
