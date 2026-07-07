# ==============================================================================
# CRYPTOSIGHT Reddit Data Collector (collector.py)
# ==============================================================================

import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from cryptosight.utils.db import get_connection
from cryptosight.utils.config import load_config
from cryptosight.utils.logger import get_logger
from cryptosight.nlp_.db import init_nlp_tables, insert_raw_post

logger = get_logger("NLP_COLLECTOR")

POSTS_API_URL = "https://api.pullpush.io/reddit/search/submission/"
COMMENTS_API_URL = "https://api.pullpush.io/reddit/search/comment/"


def parse_utc_timestamp(val) -> str:
    """
    Converts Reddit Unix timestamp into clean UTC ISO timestamp.
    """
    if not val:
        return datetime.now(timezone.utc).isoformat()
    try:
        return datetime.fromtimestamp(float(val), tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def fetch_posts(symbol: str, subreddit: str, limit: int = 50) -> list:
    """
    Fetches Reddit posts mentioning the symbol from a specific subreddit.
    """
    params = {
        "q": symbol,
        "subreddit": subreddit,
        "size": limit
    }
    try:
        logger.info(f"Fetching posts for [{symbol}] in r/{subreddit}...")
        response = requests.get(POSTS_API_URL, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        elif response.status_code == 429:
            logger.warning("Rate limit hit. Waiting 5s...")
            time.sleep(5.0)
        return []
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        return []


def fetch_comments(post_id: str, limit: int = 10) -> list:
    """
    Fetches top comments under a specific Reddit post.
    """
    link_id = post_id if post_id.startswith("t3_") else f"t3_{post_id}"
    params = {
        "link_id": link_id,
        "size": limit
    }
    try:
        response = requests.get(COMMENTS_API_URL, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            raw_comments = data.get("data", [])
            return [c.get("body", "").strip() for c in raw_comments if c.get("body") and c.get("body") != "[deleted]"]
        return []
    except Exception as e:
        logger.error(f"Error fetching comments for post {post_id}: {e}")
        return []


def collect_reddit_data(config_path: str | Path = None):
    """
    Collects Reddit posts and comments and saves them in the database.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    config = load_config(config_path)
    symbols = config.get("symbols", ["BTC", "ADA"])
    subreddits = config.get("subreddits", ["Bitcoin", "cardano"])
    
    scraping_cfg = config.get("scraping", {})
    posts_limit = scraping_cfg.get("posts_per_symbol", 50)
    fetch_comm = scraping_cfg.get("fetch_comments", True)
    comments_limit = scraping_cfg.get("max_comments_per_post", 10)

    logger.info(f"Starting collection for: {symbols}")
    
    conn = get_connection()
    init_nlp_tables(conn, symbols)

    try:
        for symbol in symbols:
            limit_per_sub = max(1, posts_limit // len(subreddits)) if subreddits else posts_limit
            
            for sub in subreddits:
                posts = fetch_posts(symbol, sub, limit=limit_per_sub)
                for p in posts:
                    raw_id = p.get("id")
                    if not raw_id:
                        continue
                    
                    post_id = raw_id if raw_id.startswith("t3_") else f"t3_{raw_id}"
                    comment_texts = []
                    
                    if fetch_comm and comments_limit > 0:
                        comment_texts = fetch_comments(post_id, limit=comments_limit)
                        time.sleep(1.5)  # Avoid rate limiting
                    
                    post_data = {
                        "post_id": post_id,
                        "created_utc": parse_utc_timestamp(p.get("created_utc")),
                        "subreddit": p.get("subreddit", sub),
                        "title": p.get("title", ""),
                        "body": p.get("selftext", "") or p.get("body", ""),
                        "author": p.get("author", ""),
                        "score": p.get("score"),
                        "upvote_ratio": p.get("upvote_ratio"),
                        "num_comments": p.get("num_comments"),
                        "comments": comment_texts
                    }
                    
                    insert_raw_post(conn, symbol, post_data)
                    
        logger.info("Reddit data collection completed successfully!")
    except Exception as e:
        logger.error(f"Error during collection: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    collect_reddit_data()
