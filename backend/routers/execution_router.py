"""
execution_router.py
FastAPI router for Strategy Execution endpoints.
Connects frontend UI execution components directly to PostgreSQL DB schemas:
  - execution.stats
  - execution.active_positions
  - execution_ledgers.<strategy_slug>
"""

from fastapi import APIRouter, Query, HTTPException
from cryptosight.backend.services import execution_service

router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"])
def get_db_health():
    """Real PostgreSQL Execution schema health status indicator."""
    return execution_service.check_execution_db_health()


@router.api_route("", methods=["GET", "HEAD"])
def list_executions(
    search: str = Query("", description="Search by strategy name, symbol, or exchange"),
    status: str = Query("all", description="all | active | paused | stopped | inactive"),
):
    """
    GET /api/v1/execution
    Returns live strategy execution list directly from PostgreSQL DB tables.
    Returns empty list if zero execution runs exist in database. ZERO mock data inserted.
    """
    try:
        data = execution_service.get_all_executions(search=search, status=status)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/{id}", methods=["GET", "HEAD"])
def get_execution_details(id: str):
    """
    GET /api/v1/execution/{id}
    Returns detailed execution instance for strategy_id or exec-ID.
    """
    try:
        data = execution_service.get_execution_by_id(id)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Execution instance for '{id}' not found in database: {e}")


@router.put("/{id}/pause")
def pause_execution(id: str):
    """PUT /api/v1/execution/{id}/pause"""
    try:
        data = execution_service.pause_execution_run(id)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}/stop")
def stop_execution(id: str):
    """PUT /api/v1/execution/{id}/stop"""
    try:
        data = execution_service.stop_execution_run(id)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
