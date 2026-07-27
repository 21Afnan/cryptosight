"""
FastAPI Router for Machine Learning endpoints (/api/v1/ml).
"""

from fastapi import APIRouter, Query, HTTPException, Path as APIPath
from typing import Optional, Dict, Any
from cryptosight.backend.services.ml_service import (
    get_all_ml_models,
    get_ml_model_by_id,
    get_ml_model_ledger,
)
from cryptosight.utils.logger import get_logger

logger = get_logger("MLRouter")

router = APIRouter()


@router.get("/models")
def list_ml_models(
    task_type: Optional[str] = Query(None, description="Filter by classification or regression"),
    symbol: Optional[str] = Query(None, description="Filter by asset symbol (e.g. BTC)"),
) -> Dict[str, Any]:
    """
    1. Get all trained Machine Learning models with executive KPIs and summary metrics.
    Serves the main catalog page (/ml).
    """
    try:
        data = get_all_ml_models(task_type=task_type, symbol=symbol)
        return {
            "status": "success",
            "data": data,
        }
    except Exception as err:
        logger.error(f"Error in list_ml_models endpoint: {err}")
        raise HTTPException(status_code=500, detail=str(err))


@router.get("/models/{model_id}")
def get_ml_model_details(
    model_id: str = APIPath(..., description="The unique model_id (e.g. btc_15m_classification_xgboost)"),
) -> Dict[str, Any]:
    """
    2. Get deep model details including accuracy metrics, hyperparameters, dataset specs, and trade ledger.
    Serves the model details page (/ml/:id).
    """
    try:
        model = get_ml_model_by_id(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"ML Model '{model_id}' not found.")
        return {
            "status": "success",
            "data": model,
        }
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Error in get_ml_model_details endpoint: {err}")
        raise HTTPException(status_code=500, detail=str(err))


@router.get("/models/{model_id}/ledger")
def get_ml_model_trade_ledger(
    model_id: str = APIPath(..., description="The unique model_id (e.g. btc_15m_classification_xgboost)"),
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset index"),
) -> Dict[str, Any]:
    """
    3. Get paginated backtest trade executions for dedicated table ml_backtests.<model_id>.
    """
    try:
        ledger_data = get_ml_model_ledger(model_id=model_id, limit=limit, offset=offset)
        return {
            "status": "success",
            "data": ledger_data,
        }
    except Exception as err:
        logger.error(f"Error in get_ml_model_trade_ledger endpoint: {err}")
        raise HTTPException(status_code=500, detail=str(err))
