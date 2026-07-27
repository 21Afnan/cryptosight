"""
sentiment_router.py
FastAPI router for Sentiment & NLP endpoints (/api/v1/sentiment).
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
from cryptosight.backend.services.sentiment_service import (
    get_sentiment_summary,
    get_sentiment_posts,
)
from cryptosight.utils.logger import get_logger

logger = get_logger("SentimentRouter")

router = APIRouter()


@router.get("/summary")
def sentiment_summary() -> Dict[str, Any]:
    """
    GET /api/v1/sentiment/summary
    Returns market sentiment overall scores and symbol breakdowns from metadata.sentiment_data.
    """
    try:
        return get_sentiment_summary()
    except Exception as err:
        logger.error(f"Error in sentiment_summary endpoint: {err}")
        raise HTTPException(status_code=500, detail=str(err))


@router.get("/posts")
def list_sentiment_posts(
    symbol: Optional[str] = Query(None, description="Filter by asset symbol (BTC or ADA)"),
    limit: int = Query(50, ge=1, le=500, description="Limit rows"),
    offset: int = Query(0, ge=0, description="Offset index"),
) -> Dict[str, Any]:
    """
    GET /api/v1/sentiment/posts
    Returns scraped Reddit posts with ModernFinBERT AI classifications from reddit_cleaned.<symbol>.
    """
    try:
        return get_sentiment_posts(symbol=symbol, limit=limit, offset=offset)
    except Exception as err:
        logger.error(f"Error in list_sentiment_posts endpoint: {err}")
        raise HTTPException(status_code=500, detail=str(err))
