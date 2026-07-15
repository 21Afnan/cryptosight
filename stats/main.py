"""
main.py — Master Execution Pipeline for CryptoSight.
Runs the historical backtest, extracts the returns series, computes all 59+ QuantStats
metrics, and generates all 6 interactive Plotly quant visualizations.
"""
import logging
import pandas as pd
from cryptosight.backtesting.backtest import BacktestingEngine
from cryptosight.stats.metrices import compute_all_metrics
from cryptosight.stats.plots import generate_all_plots

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("CryptoSightMain")


def main():
    # 1. Run historical backtesting engine
    logger.info("Starting backtest execution...")
    engine = BacktestingEngine()
    ledger_df = engine.run_pipeline()

    if ledger_df is None or ledger_df.empty:
        logger.warning("Backtest returned empty ledger. No trades executed.")
        return

    logger.info(f"Backtest completed: {len(ledger_df)} trades processed.")

    # 2. Extract required returns column ('perc_pnl') indexed chronologically by 'exit_time'
    if "exit_time" in ledger_df.columns:
        clean_ledger = ledger_df.sort_values(by="exit_time")
        clean_ledger["exit_time"] = pd.to_datetime(clean_ledger["exit_time"])
        returns_series = clean_ledger.set_index("exit_time")["perc_pnl"]
    else:
        returns_series = ledger_df["perc_pnl"]

    # 3. Calculate all QuantStats performance metrics and export JSON report
    logger.info("Computing QuantStats performance metrics...")
    metrics_path = "cryptosight/stats/metrics_report.json"
    metrics = compute_all_metrics(returns_series, is_percentage=True, save_filepath=metrics_path)

    # Display clean summary of top executive metrics
    print("\nCORE PERFORMANCE METRICS")
    top_metrics = ["cagr", "sharpe", "sortino", "calmar", "max_drawdown", "win_rate", "profit_factor"]
    for key in top_metrics:
        if key in metrics and metrics[key] is not None:
            val = metrics[key]
            if key in ["cagr", "max_drawdown", "win_rate"]:
                print(f"{key:<15}: {val * 100:.2f}%")
            else:
                print(f"{key:<15}: {val:.4f}")

    # 4. Generate all interactive Plotly stakeholder charts
    logger.info("Generating Plotly interactive charts...")
    charts_dir = "cryptosight/stats/charts"
    charts = generate_all_plots(returns_series, is_percentage=True, output_dir=charts_dir)

    print("\nGENERATED PLOTLY CHARTS")
    for chart_name in charts.keys():
        print(f"{chart_name:<18} -> {charts_dir}/{chart_name}.html")
    print(f"\n(All {len(charts)} chart definitions saved into 1 consolidated JSON: {charts_dir}/all_charts.json)")

    print("\nPipeline execution completed successfully.")


if __name__ == "__main__":
    main()
