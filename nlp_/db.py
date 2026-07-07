
import psycopg2
from psycopg2.extras import DictCursor
from cryptosight.utils.db import get_connection
from cryptosight.utils.logger import get_logger

logger = get_logger("NLP_DB")


def init_nlp_tables(conn, symbols: list):
    """
    Creates schemas (reddit_raw and reddit_cleaned) and tables for each symbol.
    Each symbol is stored in its own table with post_id as the primary key.
    """
    with conn.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS reddit_raw;")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS reddit_cleaned;")
        
        for symbol in symbols:
            table_name = symbol.lower()
            
            # Raw data table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS reddit_raw.{table_name} (
                    post_id VARCHAR(100) PRIMARY KEY,
                    created_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                    subreddit VARCHAR(100) NOT NULL,
                    title TEXT,
                    body TEXT,
                    author VARCHAR(100),
                    score BIGINT,
                    upvote_ratio NUMERIC(5, 2),
                    num_comments BIGINT,
                    comments TEXT[],
                    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Cleaned sentiment results table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS reddit_cleaned.{table_name} (
                    post_id VARCHAR(100) PRIMARY KEY,
                    created_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                    symbol VARCHAR(20) NOT NULL DEFAULT '{symbol.upper()}',
                    cleaned_title TEXT,
                    cleaned_body TEXT,
                    cleaned_comments TEXT[],
                    sentiment VARCHAR(20) NOT NULL,
                    confidence NUMERIC(5, 4) NOT NULL,
                    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Dynamic migration: Add missing columns to existing tables if they don't exist
            cursor.execute(f"ALTER TABLE reddit_raw.{table_name} ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
            cursor.execute(f"ALTER TABLE reddit_cleaned.{table_name} ADD COLUMN IF NOT EXISTS symbol VARCHAR(20) NOT NULL DEFAULT '{symbol.upper()}';")
            cursor.execute(f"ALTER TABLE reddit_cleaned.{table_name} ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
            
    conn.commit()
    logger.info(f"Initialized schemas and tables for symbols: {[s.upper() for s in symbols]}")


def insert_raw_post(conn, symbol: str, post: dict):
    """
    Inserts or updates a single raw Reddit post into reddit_raw.<symbol>.
    """
    table_name = symbol.lower()
    sql = f"""
        INSERT INTO reddit_raw.{table_name} 
            (post_id, created_utc, subreddit, title, body, author, score, upvote_ratio, num_comments, comments)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (post_id) DO UPDATE SET
            score = EXCLUDED.score,
            upvote_ratio = EXCLUDED.upvote_ratio,
            num_comments = EXCLUDED.num_comments,
            comments = EXCLUDED.comments,
            ingested_at = CURRENT_TIMESTAMP;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (
            post["post_id"],
            post["created_utc"],
            post["subreddit"],
            post.get("title", ""),
            post.get("body", ""),
            post.get("author", ""),
            post.get("score"),
            post.get("upvote_ratio"),
            post.get("num_comments"),
            post.get("comments", [])
        ))
    conn.commit()


def insert_sentiment_result(conn, symbol: str, result: dict):
    """
    Inserts or updates the cleaned text and AI sentiment result into reddit_cleaned.<symbol>.
    """
    table_name = symbol.lower()
    sql = f"""
        INSERT INTO reddit_cleaned.{table_name} 
            (post_id, created_utc, symbol, cleaned_title, cleaned_body, cleaned_comments, sentiment, confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (post_id) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            cleaned_title = EXCLUDED.cleaned_title,
            cleaned_body = EXCLUDED.cleaned_body,
            cleaned_comments = EXCLUDED.cleaned_comments,
            sentiment = EXCLUDED.sentiment,
            confidence = EXCLUDED.confidence,
            processed_at = CURRENT_TIMESTAMP;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (
            result["post_id"],
            result["created_utc"],
            symbol.upper(),
            result.get("cleaned_title", ""),
            result.get("cleaned_body", ""),
            result.get("cleaned_comments", []),
            result["sentiment"],
            result["confidence"]
        ))
    conn.commit()


def fetch_unprocessed_posts(conn, symbol: str, limit: int) -> list:
    """
    Fetches raw posts from reddit_raw.<symbol> that do not exist in reddit_cleaned.<symbol> yet.
    """
    table_name = symbol.lower()
    sql = f"""
        SELECT r.post_id, r.created_utc, r.title, r.body, r.comments 
        FROM reddit_raw.{table_name} r
        LEFT JOIN reddit_cleaned.{table_name} c ON r.post_id = c.post_id
        WHERE c.post_id IS NULL
        ORDER BY r.created_utc DESC
        LIMIT %s;
    """
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
