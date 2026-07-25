"""
backtest_router.py
FastAPI router for Backtest & Strategy endpoints.
Connects frontend UI components directly to PostgreSQL DB metadata & backtest services.
"""

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from cryptosight.backend.services import backtest_service

router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"])
def get_db_health():
    """
    Real PostgreSQL connection health status indicator.
    Polled centrally by Topbar Navbar (● DB Active / ● DB Inactive).
    """
    return backtest_service.check_db_health()


@router.api_route("", methods=["GET", "HEAD"])
def list_backtests(
    search: str = Query("", description="Search by strategy name, symbol, or exchange"),
    status: str = Query("all", description="all | pending | running | completed | failed"),
):
    """
    GET /api/v1/backtests
    Returns strategies from metadata.strategy_data LEFT JOIN backtests.stats LEFT JOIN metadata.backtest_data.
    Each item exposes strategy_id (integer), strategy_name, exchange, symbol, timeframe,
    status, net_pnl, win_rate, sharpe, max_drawdown, total_trades.
    """
    try:
        data = backtest_service.get_all_backtests(search=search, status=status)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/{id}", methods=["GET", "HEAD"])
def get_backtest_details(id: str):
    """
    GET /api/v1/backtests/{id}
    Returns detailed backtest run for strategy_id (numeric or slug):
      - strategy metadata & backtest configuration
      - performance metrics (net_pnl, cagr, sharpe, sortino, calmar, win_rate, max_drawdown)
      - chart data series (equity_curve, drawdown_curve, monthly_returns, rolling_metrics)
      - trade ledger rows from backtests.<strategy_slug>
    """
    try:
        data = backtest_service.get_backtest_by_id(id)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Backtest details for '{id}' not found: {e}")


@router.post("")
def create_backtest_run(payload: dict, background_tasks: BackgroundTasks):
    """
    POST /api/v1/backtests
    Submits a new strategy backtest job request.
    """
    try:
        result = backtest_service.submit_backtest_request(payload)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
