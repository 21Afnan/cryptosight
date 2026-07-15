"""
plots.py — Interactive Plotly Performance & Risk Visualizations.

Generates the exact 6 frontend-ready quant charts requested by user:
1. daily_returns: Daily resampled / period returns over time (%)
2. log_returns: Cumulative log returns trajectory (%)
3. returns: Baseline cumulative strategy equity curve (%)
4. yearly_returns: Annual / year-by-year compounded returns (%)
5. drawdown: Underwater drawdown depth & duration over time (%)
6. drawdowns_periods: Highlights top 5 worst drawdown periods overlaid on equity index ($100 Base)

Exports to both:
- Standalone interactive HTML files for browser verification.
- 1 master `all_charts.json` containing pure JSON `plotly_figure` dicts AND `raw_values` arrays (`[{time, value}]`) for effortless custom frontend rendering.
"""

import logging
import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import quantstats as qs

try:
    from cryptosight.stats.metrices import normalize_returns
except ImportError:
    try:
        from .metrices import normalize_returns
    except ImportError:
        def normalize_returns(returns: pd.Series, is_percentage: bool = False) -> pd.Series:
            if isinstance(returns, pd.DataFrame):
                returns = returns.iloc[:, 0]
            returns = returns.dropna()
            if returns.empty:
                return returns
            if is_percentage:
                return returns / 100.0
            return returns

logger = logging.getLogger("StatsPlots")


def save_chart(fig: go.Figure, filepath: str = None) -> str:
    """
    Saves a Plotly figure to standalone interactive HTML.
    """
    if not filepath or fig is None:
        return None
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    
    if not filepath.endswith(".html"):
        filepath = f"{filepath}.html"
    fig.write_html(filepath, include_plotlyjs="cdn")
    logger.info(f"Saved interactive chart HTML to: {filepath}")
    return filepath


def plot_cumulative_returns(returns: pd.Series, is_percentage: bool = False, save_path: str = None) -> (go.Figure, pd.Series):
    """
    3. 'returns' — Baseline cumulative strategy equity curve (%).
    """
    clean_r = normalize_returns(returns, is_percentage=is_percentage)
    cum_returns = (1 + clean_r).cumprod() - 1
    cum_returns_pct = cum_returns * 100.0

    # Ensure clean string list for x and float list for y to prevent Plotly base64 bdata serialization
    x_vals = cum_returns_pct.index.astype(str).tolist()
    y_vals = [round(float(v), 6) if pd.notnull(v) else None for v in cum_returns_pct.values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Cumulative Return (%)",
        line=dict(color="#00E676", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(0, 230, 118, 0.08)"
    ))

    fig.update_layout(
        title="<b>Cumulative Strategy Equity Curve (%)</b>",
        xaxis_title="Time",
        yaxis_title="Cumulative Return (%)",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    save_chart(fig, save_path)
    return fig, cum_returns_pct


def plot_daily_returns(returns: pd.Series, is_percentage: bool = False, save_path: str = None) -> (go.Figure, pd.Series):
    """
    1. 'daily_returns' — Daily resampled (or period) returns over time (%).
    """
    clean_r = normalize_returns(returns, is_percentage=is_percentage)
    
    # Resample to 1-Day compounded return if DatetimeIndex is present
    if isinstance(clean_r.index, pd.DatetimeIndex) or pd.api.types.is_datetime64_any_dtype(clean_r.index):
        try:
            daily_r = clean_r.resample("1D").apply(lambda r: (1 + r).prod() - 1 if len(r) > 0 else 0.0)
            daily_r_pct = daily_r * 100.0
        except Exception:
            daily_r_pct = clean_r * 100.0
    else:
        daily_r_pct = clean_r * 100.0

    x_vals = daily_r_pct.index.astype(str).tolist()
    y_vals = [round(float(v), 6) if pd.notnull(v) else None for v in daily_r_pct.values]
    colors = ["#00E676" if v is not None and v >= 0 else "#FF5252" for v in y_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_vals,
        y=y_vals,
        name="Daily Return (%)",
        marker_color=colors
    ))

    fig.update_layout(
        title="<b>Daily Strategy Returns (%)</b>",
        xaxis_title="Time",
        yaxis_title="Daily Return (%)",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    save_chart(fig, save_path)
    return fig, daily_r_pct


def plot_log_returns(returns: pd.Series, is_percentage: bool = False, save_path: str = None) -> (go.Figure, pd.Series):
    """
    2. 'log_returns' — Cumulative Log Returns trajectory (%).
    """
    clean_r = normalize_returns(returns, is_percentage=is_percentage)
    # Log return formula: ln(1 + r)
    log_r = np.log(1 + clean_r)
    cum_log_pct = log_r.cumsum() * 100.0

    x_vals = cum_log_pct.index.astype(str).tolist()
    y_vals = [round(float(v), 6) if pd.notnull(v) else None for v in cum_log_pct.values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Cumulative Log Return (%)",
        line=dict(color="#29B6F6", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(41, 182, 246, 0.08)"
    ))

    fig.update_layout(
        title="<b>Cumulative Strategy Log Returns (%)</b>",
        xaxis_title="Time",
        yaxis_title="Log Return (%)",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    save_chart(fig, save_path)
    return fig, cum_log_pct


def plot_yearly_returns(returns: pd.Series, is_percentage: bool = False, save_path: str = None) -> (go.Figure, pd.Series):
    """
    4. 'yearly_returns' — Annual / year-by-year compounded returns (%).
    """
    clean_r = normalize_returns(returns, is_percentage=is_percentage)
    
    if isinstance(clean_r.index, pd.DatetimeIndex) or pd.api.types.is_datetime64_any_dtype(clean_r.index):
        yearly_pct = clean_r.groupby(clean_r.index.year).apply(lambda r: (1 + r).prod() - 1) * 100.0
    else:
        yearly_pct = pd.Series([(1 + clean_r).prod() - 1] * 100.0, index=["Total"])

    x_vals = yearly_pct.index.astype(str).tolist()
    y_vals = [round(float(v), 6) if pd.notnull(v) else None for v in yearly_pct.values]
    colors = ["#00E676" if v is not None and v >= 0 else "#FF5252" for v in y_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_vals,
        y=y_vals,
        name="Yearly Return (%)",
        marker_color=colors,
        text=[f"{v:.2f}%" if v is not None else "" for v in y_vals],
        textposition="auto"
    ))

    fig.update_layout(
        title="<b>Yearly Compounded Strategy Returns (%)</b>",
        xaxis_title="Year",
        yaxis_title="Return (%)",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    save_chart(fig, save_path)
    return fig, yearly_pct


def plot_drawdown(returns: pd.Series, is_percentage: bool = False, save_path: str = None) -> (go.Figure, pd.Series):
    """
    5. 'drawdown' — Underwater drawdown depth & duration over time (%).
    """
    clean_r = normalize_returns(returns, is_percentage=is_percentage)
    dd_series = qs.stats.to_drawdown_series(clean_r) * 100.0

    x_vals = dd_series.index.astype(str).tolist()
    y_vals = [round(float(v), 6) if pd.notnull(v) else None for v in dd_series.values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Underwater Drawdown (%)",
        line=dict(color="#FF5252", width=2),
        fill="tozeroy",
        fillcolor="rgba(255, 82, 82, 0.25)"
    ))

    fig.update_layout(
        title="<b>Portfolio Underwater Drawdown (%)</b>",
        xaxis_title="Time",
        yaxis_title="Drawdown (%)",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    save_chart(fig, save_path)
    return fig, dd_series


def plot_drawdowns_periods(returns: pd.Series, top: int = 5, is_percentage: bool = False, save_path: str = None) -> (go.Figure, pd.Series):
    """
    6. 'drawdowns_periods' — Highlights worst drawdown periods directly on equity index ($100 Base).
    """
    clean_r = normalize_returns(returns, is_percentage=is_percentage)
    cum_index = (1 + clean_r).cumprod() * 100.0

    x_vals = cum_index.index.astype(str).tolist()
    y_vals = [round(float(v), 6) if pd.notnull(v) else None for v in cum_index.values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Portfolio Index ($100 Base)",
        line=dict(color="#29B6F6", width=2.5)
    ))

    try:
        dd_details = qs.stats.drawdown_details(clean_r)
        if dd_details is not None and not dd_details.empty:
            top_dds = dd_details.sort_values(by="max drawdown", ascending=True).head(top)
            colors = ["#FF1744", "#FF5252", "#FF8A80", "#FFCDD2", "#FFEBEE"]
            for idx, (_, row) in enumerate(top_dds.iterrows()):
                start_dt = str(row["start"])
                end_dt = str(row["end"])
                dd_val = row["max drawdown"] * 100.0
                
                fig.add_vrect(
                    x0=start_dt, x1=end_dt,
                    fillcolor=colors[idx % len(colors)],
                    opacity=0.2,
                    layer="below",
                    line_width=1,
                    line_color=colors[idx % len(colors)],
                    annotation_text=f"#{idx+1}: {dd_val:.1f}%",
                    annotation_position="top left",
                    annotation_font_color="#FF8A80"
                )
    except Exception as e:
        logger.warning(f"Could not overlay drawdown periods: {e}")

    fig.update_layout(
        title=f"<b>Top {top} Worst Drawdown Episodes Overlaid on Equity Index ($100 Base)</b>",
        xaxis_title="Time",
        yaxis_title="Portfolio Value ($)",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    save_chart(fig, save_path)
    return fig, cum_index


def generate_all_plots(returns: pd.Series, is_percentage: bool = False, output_dir: str = "cryptosight/stats/charts") -> dict:
    """
    Master function to compute and export the exact 6 quant charts requested by user.
    Returns {chart_name: plot_figure}.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Generating exact 6 requested interactive Plotly charts into directory: {output_dir}")

    fig_daily, s_daily = plot_daily_returns(returns, is_percentage=is_percentage, save_path=f"{output_dir}/daily_returns.html")
    fig_log, s_log = plot_log_returns(returns, is_percentage=is_percentage, save_path=f"{output_dir}/log_returns.html")
    fig_returns, s_returns = plot_cumulative_returns(returns, is_percentage=is_percentage, save_path=f"{output_dir}/returns.html")
    fig_yearly, s_yearly = plot_yearly_returns(returns, is_percentage=is_percentage, save_path=f"{output_dir}/yearly_returns.html")
    fig_dd, s_dd = plot_drawdown(returns, is_percentage=is_percentage, save_path=f"{output_dir}/drawdown.html")
    fig_dd_periods, s_dd_periods = plot_drawdowns_periods(returns, is_percentage=is_percentage, save_path=f"{output_dir}/drawdowns_periods.html")

    plots_and_data = {
        "daily_returns": (fig_daily, s_daily),
        "log_returns": (fig_log, s_log),
        "returns": (fig_returns, s_returns),
        "yearly_returns": (fig_yearly, s_yearly),
        "drawdown": (fig_dd, s_dd),
        "drawdowns_periods": (fig_dd_periods, s_dd_periods)
    }

    plots = {name: item[0] for name, item in plots_and_data.items()}

    # Consolidate and save into exactly 1 master frontend-ready JSON file (`all_charts.json`)
    # Each entry includes BOTH the Plotly JSON definition (`plotly_figure`) AND `raw_values` (`[{time, value}]`)
    master_json_path = f"{output_dir}/all_charts.json"
    try:
        master_json_data = {}
        for name, (fig, raw_s) in plots_and_data.items():
            if fig is not None:
                raw_records = []
                if raw_s is not None and not raw_s.empty:
                    for t, v in raw_s.items():
                        raw_records.append({"time": str(t), "value": round(float(v), 6) if pd.notnull(v) else None})
                
                master_json_data[name] = {
                    "plotly_figure": json.loads(fig.to_json()),
                    "raw_values": raw_records
                }

        with open(master_json_path, "w", encoding="utf-8") as f:
            json.dump(master_json_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved all {len(plots)} charts + raw frontend values into 1 consolidated JSON report: {master_json_path}")
    except Exception as e:
        logger.warning(f"Could not export master charts JSON report: {e}")

    return plots
