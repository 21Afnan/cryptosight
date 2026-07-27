from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cryptosight.backend.routers import dashboard_router, strategy_router, backtest_router, wallet_router, ml_router, sentiment_router, execution_router
from cryptosight.utils.db import get_connection, create_backtest_stats_table
from cryptosight.utils.metadata import create_strategy_data
from cryptosight.utils.logger import get_logger

logger = get_logger("Main")

app = FastAPI(title="CryptoSight Quant Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router.router, prefix="/api/v1/dashboard",  tags=["Dashboard"])
app.include_router(strategy_router.router,  prefix="/api/v1/strategies", tags=["Strategies"])
app.include_router(backtest_router.router,  prefix="/api/v1/backtests",  tags=["Backtests"])
app.include_router(wallet_router.router,    prefix="/api/v1/wallets",    tags=["Wallets"])
app.include_router(execution_router.router, prefix="/api/v1/execution",  tags=["Execution"])
app.include_router(ml_router.router,        prefix="/api/v1/ml",         tags=["Machine Learning"])
app.include_router(sentiment_router.router, prefix="/api/v1/sentiment",  tags=["Sentiment"])

@app.get("/")
def root():
    return {"message": "CryptoSight Quant API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
