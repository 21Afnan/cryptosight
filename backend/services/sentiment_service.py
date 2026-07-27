"""
sentiment_service.py
Service layer for Sentiment & NLP pipeline endpoints (/api/v1/sentiment).
Queries live PostgreSQL tables strictly: metadata.sentiment_data and reddit_cleaned.<symbol>.
ZERO fake fallback numbers or default counts.
"""

import json
from typing import Dict, Any, List, Optional
from cryptosight.utils.db import get_connection
from cryptosight.utils.logger import get_logger

logger = get_logger("SentimentService")


def get_sentiment_summary() -> Dict[str, Any]:
    """
    Returns high-level market sentiment summary and per-symbol breakdowns directly from metadata.sentiment_data.
    Zero fake fallback numbers or default values.
    """
    conn = get_connection()
    if not conn:
        logger.error("Failed to connect to PostgreSQL database.")
        return {
            "market_summary": {
                "overall_score": 0,
                "overall_label": "N/A",
                "total_posts_analyzed": 0,
                "total_bullish_pct": 0.0,
                "total_bearish_pct": 0.0,
                "total_neutral_pct": 0.0,
                "last_updated": None,
                "top_bullish_symbol": "N/A",
                "top_bearish_symbol": "N/A",
                "active_model": "tabularisai/ModernFinBERT",
            },
            "per_symbol": [],
            "distribution": [],
        }

    per_symbol: List[Dict[str, Any]] = []
    total_posts_sum = 0
    bullish_sum = 0
    bearish_sum = 0
    neutral_sum = 0
    top_bullish_sym = "N/A"
    top_bearish_sym = "N/A"
    max_bullish_cnt = -1
    max_bearish_cnt = -1
    last_updated = None

    try:
        with conn.cursor() as cursor:
            query = """
                SELECT symbol, total_posts, bullish_count, bearish_count, neutral_count, last_updated
                FROM metadata.sentiment_data
                ORDER BY total_posts DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]

            for row in rows:
                rec = dict(zip(col_names, row))
                sym = str(rec["symbol"]).upper()
                t_posts = int(rec.get("total_posts") or 0)
                bull_c = int(rec.get("bullish_count") or 0)
                bear_c = int(rec.get("bearish_count") or 0)
                neut_c = int(rec.get("neutral_count") or 0)
                l_updated = rec.get("last_updated")

                total_posts_sum += t_posts
                bullish_sum += bull_c
                bearish_sum += bear_c
                neutral_sum += neut_c

                if t_posts > 0:
                    if bull_c > max_bullish_cnt:
                        max_bullish_cnt = bull_c
                        top_bullish_sym = sym

                    if bear_c > max_bearish_cnt:
                        max_bearish_cnt = bear_c
                        top_bearish_sym = sym

                    if l_updated and not last_updated:
                        last_updated = l_updated.isoformat() if hasattr(l_updated, "isoformat") else str(l_updated)

                    subreddit = "r/Bitcoin" if sym == "BTC" else "r/cardano" if sym == "ADA" else f"r/{sym.lower()}"

                    per_symbol.append({
                        "symbol": sym,
                        "total_posts": t_posts,
                        "bullish_count": bull_c,
                        "bearish_count": bear_c,
                        "neutral_count": neut_c,
                        "last_updated": last_updated,
                        "subreddit": subreddit,
                    })

    except Exception as err:
        logger.error(f"Error querying metadata.sentiment_data: {err}")
    finally:
        conn.close()

    # Calculate overall market metrics dynamically from DB
    if total_posts_sum > 0:
        bull_pct = round((bullish_sum / total_posts_sum) * 100, 1)
        bear_pct = round((bearish_sum / total_posts_sum) * 100, 1)
        neut_pct = round((neutral_sum / total_posts_sum) * 100, 1)
        overall_label = "Bullish" if bull_pct >= 50 else "Bearish" if bear_pct > bull_pct else "Neutral"
        overall_score = int(bull_pct)
    else:
        bull_pct, bear_pct, neut_pct = 0.0, 0.0, 0.0
        overall_label = "N/A"
        overall_score = 0

    distribution = [
        {"name": "Bullish", "value": bull_pct, "color": "#22C55E"},
        {"name": "Bearish", "value": bear_pct, "color": "#EE5D5D"},
        {"name": "Neutral", "value": neut_pct, "color": "#F0B90B"},
    ]

    market_summary = {
        "overall_score": overall_score,
        "overall_label": overall_label,
        "total_posts_analyzed": total_posts_sum,
        "total_bullish_pct": bull_pct,
        "total_bearish_pct": bear_pct,
        "total_neutral_pct": neut_pct,
        "last_updated": last_updated,
        "top_bullish_symbol": top_bullish_sym if max_bullish_cnt > 0 else "N/A",
        "top_bearish_symbol": top_bearish_sym if max_bearish_cnt > 0 else "N/A",
        "active_model": "tabularisai/ModernFinBERT",
    }

    return {
        "market_summary": market_summary,
        "per_symbol": per_symbol,
        "distribution": distribution,
    }


def get_sentiment_posts(symbol: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Queries cleaned Reddit posts from reddit_cleaned.<symbol> tables directly from PostgreSQL.
    Zero fake defaults.
    """
    conn = get_connection()
    if not conn:
        logger.error("Failed to connect to PostgreSQL database.")
        return {"total": 0, "posts": []}

    target_symbols = ["btc", "ada"]
    if symbol and symbol.strip().lower() not in ("all", ""):
        clean_sym = symbol.strip().lower()
        if clean_sym in target_symbols:
            target_symbols = [clean_sym]

    posts: List[Dict[str, Any]] = []

    try:
        with conn.cursor() as cursor:
            for sym in target_symbols:
                table_name = f"reddit_cleaned.{sym}"
                cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'reddit_cleaned' AND tablename = %s);", (sym,))
                if not cursor.fetchone()[0]:
                    continue

                sql = f"""
                    SELECT post_id, created_utc, title, body, comments, sentiment, confidence, score, upvote_ratio, num_comments
                    FROM {table_name}
                    ORDER BY created_utc DESC
                    LIMIT %s OFFSET %s;
                """
                cursor.execute(sql, (limit, offset))
                rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]

                sub_name = "r/Bitcoin" if sym == "btc" else "r/cardano"

                for r in rows:
                    rec = dict(zip(col_names, r))
                    created_utc = rec.get("created_utc")
                    if created_utc:
                        if hasattr(created_utc, "strftime"):
                            rec["created_utc"] = created_utc.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            s = str(created_utc).replace("T", " ")
                            if "+00:00" in s:
                                s = s.replace("+00:00", "")
                            rec["created_utc"] = s.strip()
                    rec["symbol"] = sym.upper()
                    rec["subreddit"] = sub_name
                    rec["confidence"] = float(rec.get("confidence") or 0.0)
                    rec["score"] = int(rec.get("score") or 0)
                    rec["upvote_ratio"] = float(rec.get("upvote_ratio") or 0.0)
                    posts.append(rec)

    except Exception as err:
        logger.error(f"Error querying sentiment posts: {err}")
    finally:
        conn.close()

    posts.sort(key=lambda p: str(p.get("created_utc")), reverse=True)

    return {
        "total": len(posts),
        "posts": posts[offset : offset + limit],
    }
