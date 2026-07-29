from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from cryptosight.backend.services.strategy_builder_service import (
    get_playbook_strategies,
    save_new_strategy,
    run_dynamic_backtest
)

router = APIRouter()

class SaveStrategyRequest(BaseModel):
    strategy_name: str
    exchange: str = "bybit"
    symbol: str
    timeframe: str
    indicators_config: dict
    strategy_config: dict

@router.get("/playbook")
def get_playbook():
    try:
        return get_playbook_strategies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategies")
def save_strategy(req: SaveStrategyRequest):
    try:
        res = save_new_strategy(req.dict())
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("message"))
        return res
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
def run_custom_backtest(payload: dict):
    """
    Runs a dynamic backtest on a strategy configuration payload in-memory without saving to DB.
    """
    try:
        res = run_dynamic_backtest(payload)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("message"))
        return res
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
