"""
strategy_router.py
FastAPI router for Strategies & Trade Ledgers endpoints.
"""
from fastapi import APIRouter
from cryptosight.backend.services.strategy_service import (
    get_all_strategies,
    get_strategy_by_id,
    get_strategy_ledgers,
)

router = APIRouter()

@router.get("")
def list_strategies():
    """
    GET /api/v1/strategies
    Returns all registered strategies from metadata.strategy_data.
    """
    return get_all_strategies()


@router.get("/{identifier}")
def get_strategy_details(identifier: str):
    """
    GET /api/v1/strategies/{identifier}
    Returns Performance Summary, Configuration, and Risk Management from DB.
    """
    res = get_strategy_by_id(identifier)
    if not res:
        return {"error": f"Strategy '{identifier}' not found"}
    return res


@router.get("/{strategy_name}/ledgers")
def list_strategy_ledgers(strategy_name: str):
    """
    GET /api/v1/strategies/{strategy_name}/ledgers
    Returns trade ledger history for a specific strategy from simulation_ledgers schema.
    """
    return get_strategy_ledgers(strategy_name)
