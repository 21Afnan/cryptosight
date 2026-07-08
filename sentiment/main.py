import os
import re
import time
import yaml
import html
import emoji
import praw
import contractions
from pathlib import Path
from datetime import datetime, timezone
from cryptosight.utils.db import get_connection
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_environment as central_load_env
from cryptosight.sentiment.db import init_nlp_tables, insert_raw_post, fetch_unprocessed_posts, insert_sentiment_result

# Initialize the central logger for this module
logger = get_logger("NLP_MAIN")

# ------------------------------------------------------------------------------
# STEP 1: INITIAL SETUP & CONFIG LOADING
# ------------------------------------------------------------------------------
def load_app_config(config_path=None) -> dict:
    """
    Loads and parses the config.yaml file.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "config.yaml"
    
    with open(config_path, "r") as file:
        config = yaml.safe_load(file) or {}
        
    logger.info(f"Loaded configuration from: {config_path}")
    return config

def get_reddit_client():
    """
    Initializes the PRAW Reddit client using credentials loaded from the .env file.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "Scraping")
    
    # Safety Check: If keys are missing, raise an error immediately
    if not client_id or not client_secret:
        raise ValueError(
            "Reddit credentials missing! Please check that REDDIT_CLIENT_ID "
            "and REDDIT_CLIENT_SECRET are set in your .env file."
        )
        
    # Initialize PRAW
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    logger.info("Reddit API client initialized successfully!")
    return reddit


def fetch_posts_from_reddit(reddit_client, symbol: str, subreddit_name: str, limit: int, time_filter: str) -> list:
    """
    Searches a specific subreddit for posts mentioning the given symbol.
    Returns a list of PRAW Submission objects.
    """
    logger.info(f"Searching r/{subreddit_name} for posts mentioning '{symbol}'...")
    try:
        # 1. Connect to the specific subreddit
        subreddit = reddit_client.subreddit(subreddit_name)
        
        # 2. Search for the query (symbol) in that subreddit
        # We sort by 'new' to get the most recent posts.
        submissions = subreddit.search(query=symbol, limit=limit, sort="new", time_filter=time_filter)
        
        # 3. Convert the PRAW search generator into a standard list
        submissions_list = list(submissions)
        logger.info(f"Found {len(submissions_list)} posts.")
        return submissions_list
        
    except Exception as e:
        logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
        return []

# ------------------------------------------------------------------------------
# STEP 4: FETCH COMMENTS FOR A POST
# ------------------------------------------------------------------------------

def fetch_comments_from_post(submission, limit: int = 10) -> list:
    """
    Fetches the top comments under a specific Reddit post.
    """
    logger.info(f"Fetching comments for post ID {submission.id}...")
    try:
        # 1. replace_more(limit=0) removes the "load more comments" buttons.
        # This keeps the code fast and avoids sending extra network requests.
        submission.comments.replace_more(limit=0)
        
        comments_list = []
        # 2. Iterate through the top comments up to the limit
        for comment in submission.comments[:limit]:
            body = comment.body.strip() if comment.body else ""
            
            # Skip comments posted by automoderator bots to avoid generic wiki stickies
            author_name = comment.author.name if comment.author else ""
            if author_name.lower() == "automoderator":
                continue
            
            # 3. Filter out empty, deleted, or removed comments
            if body and body != "[deleted]" and body != "[removed]":
                comments_list.append(body)
                
        return comments_list
        
    except Exception as e:
        logger.error(f"Error fetching comments for post {submission.id}: {e}")
        return []

# ------------------------------------------------------------------------------
# STEP 5: SAVE MERGED DATA TO DATABASE
# ------------------------------------------------------------------------------

def parse_utc_timestamp(val) -> str:
    """
    Converts Reddit Unix float timestamp into clean UTC ISO timestamp for PostgreSQL.
    """
    if not val:
        return datetime.now(timezone.utc).isoformat()
    try:
        return datetime.fromtimestamp(float(val), tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def save_post_to_database(conn, symbol: str, submission, comment_texts: list):
    """
    Groups the PRAW submission details and comment texts together,
    and saves them in the database. Uses raw API IDs.
    """
    post_id = submission.id
    cleaned_title = clean_text(submission.title)
    cleaned_body = clean_text(submission.selftext)
    
    # Dropna check: if either cleaned title or body is empty, do not save to database
    if not cleaned_title or not cleaned_body:
        logger.warning(f"Dropped post {post_id} from saving (empty title or body).")
        return
        
    # Merge everything into a single post dictionary
    post_data = {
        "post_id": post_id,
        "created_utc": parse_utc_timestamp(submission.created_utc),
        "subreddit": submission.subreddit.display_name,
        "title": cleaned_title,
        "body": cleaned_body,
        "author": submission.author.name if submission.author else "[deleted]",
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "num_comments": submission.num_comments,
        "comments": comment_texts
    }
    
    try:
        # Call the imported SQL function to save to reddit_raw.<symbol> table
        insert_raw_post(conn, symbol, post_data)
        logger.info(f"Successfully saved post {post_id} to database.")
    except Exception as e:
        logger.error(f"Failed to save post {post_id} to database: {e}")

# ------------------------------------------------------------------------------
# STEP 6: INTELLIGENT TEXT CLEANING & AI SENTIMENT ANALYSIS
# ------------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Cleans raw Reddit text intelligently and dynamically:
    1. Unescapes HTML entity codes.
    2. Normalizes apostrophes and expands contractions (e.g. i've -> i have).
    3. Converts all emojis to text description using the 'emoji' library.
    4. Removes URLs, links, and HTML tags.
    5. Strips all numbers, punctuation, underscores, and special characters, keeping only letters and spaces.
    6. Condenses consecutive spaces and converts to lowercase.
    """
    if not text:
        return ""
        
    # 1. Unescape HTML entity codes (e.g. &#x1f393; -> emoji)
    text = html.unescape(text)
    
    # 2. Normalize curly apostrophes to standard straight ones
    text = text.replace("’", "'")
    
    # 3. Expand contractions dynamically using the contractions library
    text = contractions.fix(text)
        
    # 4. Convert all emojis to text (e.g., 🚀 becomes :rocket:)
    text = emoji.demojize(text)
    
    # 5. Convert ":rocket:" to " rocket " so it becomes a readable word
    text = re.sub(r':([a-zA-Z0-9_-]+):', r' \1 ', text)

    # 6. Remove URLs (e.g., http://... or www....)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # 7. Remove HTML tags (e.g., <p> or <br>)
    text = re.sub(r'<.*?>', '', text)
    
    # 8. Dynamically strip out numbers, punctuation, underscores, and all special characters
    # Keeping ONLY alphabetic letters and whitespace
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    
    # 9. Condense extra whitespaces to a single space, trim, and lowercase
    text = re.sub(r'\s+', ' ', text).strip().lower()
    
    return text


def load_sentiment_model(model_name: str):
    """
    Loads and returns the Hugging Face sentiment analysis pipeline.
    """
    logger.info(f"Loading AI Model '{model_name}' (this might take a moment)...")
    try:
        from transformers import pipeline
        pipe = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name)
        logger.info("AI Model loaded successfully!")
        return pipe
    except ImportError:
        logger.error("Error: 'transformers' or 'torch' is not installed in your Python environment.")
        logger.error("Please run: pip install transformers torch")
        raise


def analyze_text_sentiment(pipe, text: str) -> dict:
    """
    Classifies text sentiment as Bullish, Bearish, or Neutral.
    Always returns the sentiment with the highest score (no threshold filter).
    """
    if not text or not text.strip():
        return {"sentiment": "Neutral", "confidence": 1.0}
        
    chunk_size = 500
    overlap = 100
    step = chunk_size - overlap
    
    chunks = []
    for i in range(0, len(text), step):
        chunks.append(text[i : i + chunk_size])
        if i + chunk_size >= len(text):
            break
    
    results = []
    for chunk in chunks:
        try:
            prediction = pipe(chunk)[0]
            label = prediction["label"].lower()
            score = float(prediction["score"])
            results.append((label, score))
        except Exception as e:
            logger.error(f"Prediction error on text chunk: {e}")
            
    if not results:
        return {"sentiment": "Neutral", "confidence": 0.0}
        
    label_scores = {"bullish": [], "bearish": [], "neutral": []}
    for label, score in results:
        if "positive" in label or "bullish" in label:
            label_scores["bullish"].append(score)
        elif "negative" in label or "bearish" in label:
            label_scores["bearish"].append(score)
        else:
            label_scores["neutral"].append(score)
            
    sums = {k: sum(v) for k, v in label_scores.items()}
    winning_label = max(sums, key=sums.get)
    
    winning_scores = label_scores[winning_label]
    avg_confidence = sum(winning_scores) / len(winning_scores) if winning_scores else 0.0
    
    sentiment = winning_label.capitalize()
    
    return {"sentiment": sentiment, "confidence": round(avg_confidence, 4)}

# ------------------------------------------------------------------------------
# STEP 7: AI MODEL LOADING & PROCESSING UNPROCESSED POSTS WITH COMBINED TEXT
# ------------------------------------------------------------------------------

def run_sentiment_analysis_on_raw_data(conn, symbol: str, pipe, limit: int = 100):
    """
    Fetches raw unprocessed posts from reddit_raw.<symbol>, cleans title, body, and comments,
    combines them all into a single text block, analyzes the sentiment of the entire thread,
    and inserts the result into reddit_cleaned.<symbol>.
    """
    logger.info(f"Running sentiment analysis for: {symbol}...")
    
    # 1. Fetch unprocessed posts for this symbol up to the limit
    posts = fetch_unprocessed_posts(conn, symbol, limit=limit)
    if not posts:
        logger.info(f"No new unprocessed posts found for {symbol}.")
        return

    logger.info(f"Found {len(posts)} unprocessed posts to analyze.")
    
    for post in posts:
        # 2. Clean the raw title and body
        cleaned_title = clean_text(post.get("title", ""))
        cleaned_body = clean_text(post.get("body", ""))
        
        # 3. Drop check (dropna): skip post if either cleaned title or body is empty
        if not cleaned_title or not cleaned_body:
            logger.info(f"Skipping post {post['post_id']} - empty cleaned title or body.")
            continue
        
        # 4. Clean each comment in the comments array
        raw_comments = post.get("comments") or []
        cleaned_comments = [clean_text(c) for c in raw_comments if clean_text(c)]
        
        # 5. Merge all text parts with structural headers (Title, Body, Comments)
        text_parts = []
        if cleaned_title:
            text_parts.append(f"title: {cleaned_title}")
        if cleaned_body:
            text_parts.append(f"body: {cleaned_body}")
        if cleaned_comments:
            comments_str = ". ".join(cleaned_comments)
            text_parts.append(f"comments: {comments_str}")
            
        full_text = ". ".join(text_parts).strip()
            
        # 6. Run AI sentiment analysis on the combined text
        sentiment_res = analyze_text_sentiment(pipe, full_text)
        
        # 7. Package the cleaned record dictionary (including raw score, upvote_ratio, and num_comments)
        record = {
            "post_id": post["post_id"],
            "created_utc": post["created_utc"],
            "title": cleaned_title,
            "body": cleaned_body,
            "comments": cleaned_comments,
            "sentiment": sentiment_res["sentiment"],
            "confidence": sentiment_res["confidence"],
            "score": post.get("score"),
            "upvote_ratio": post.get("upvote_ratio"),
            "num_comments": post.get("num_comments")
        }
        
        # 8. Save results to database (reddit_cleaned.<symbol> table)
        insert_sentiment_result(conn, symbol, record)
        logger.info(f" Saved combined sentiment ({sentiment_res['sentiment']} - {sentiment_res['confidence']}) for post {post['post_id']}.")


def scrape_and_save_posts(conn, reddit_client, symbol: str, subreddits: list, posts_limit: int, fetch_comm: bool, comments_limit: int, time_filter: str = "year"):
    """
    Scrapes posts for a single cryptocurrency symbol across all target subreddits
    and saves them to the database.
    """
    logger.info(f"Processing symbol: {symbol}")
    
    # Split total posts limit evenly among all target subreddits
    limit_per_sub = max(1, posts_limit // len(subreddits)) if subreddits else posts_limit
    
    for sub in subreddits:
        # 1. Fetch matching posts
        posts = fetch_posts_from_reddit(reddit_client, symbol, sub, limit=limit_per_sub, time_filter=time_filter)
        
        # 2. Save each post along with comments
        for post in posts:
            comment_texts = []
            if fetch_comm and comments_limit > 0:
                comment_texts = fetch_comments_from_post(post, limit=comments_limit)
                time.sleep(1.0)  # Politeness delay to prevent API overloading
            
            # Merge and save raw post + comments to PostgreSQL
            save_post_to_database(conn, symbol, post, comment_texts)


def run_entire_nlp_pipeline(config_path: str = None):
    """
    Orchestrates the entire NLP workflow:
    1. Loads configurations.
    2. Connects to database and Reddit PRAW client.
    3. Scrapes Reddit and saves raw data.
    4. Runs AI model and saves cleaned sentiment analysis.
    """
    logger.info(" STARTING CRYPTOSIGHT NLP & SENTIMENT PIPELINE")
    
    # 1. SETUP & CONFIGURATION LOADING
    env_path = central_load_env()
    logger.info(f"Loaded environment variables from: {env_path}")
    logger.info(f"REDDIT_CLIENT_ID status: {'Loaded' if os.getenv('REDDIT_CLIENT_ID') else 'Missing!'}")
    config = load_app_config(config_path)
    
    # Extract config values
    symbols = config.get("symbols")
    subreddits = config.get("subreddits")
    
    scraping_cfg = config.get("scraping") or {}
    posts_limit = scraping_cfg.get("posts_per_symbol")
    time_filter = scraping_cfg.get("time_filter", "year")
    fetch_comm = scraping_cfg.get("fetch_comments")
    comments_limit = scraping_cfg.get("max_comments_per_post")
    
    model_cfg = config.get("model") or {}
    model_name = model_cfg.get("name")
    
    # 2. CONNECT TO DATABASE & REDDIT API
    logger.info(f"Connecting to database and initializing tables for: {symbols}...")
    try:
        conn = get_connection()
        init_nlp_tables(conn, symbols)
        logger.info("Database connection and tables initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
        
    reddit_client = get_reddit_client()
    
    try:
        # 3. PIPELINE STEP 1: SCRAPE REDDIT & SAVE RAW DATA
        logger.info("--- [STAGE 1/2] Scraping Raw Reddit Data ---")
        for symbol in symbols:
            scrape_and_save_posts(
                conn, reddit_client, symbol, subreddits, 
                posts_limit, fetch_comm, comments_limit, time_filter
            )
                    
        # 4. PIPELINE STEP 2: LOAD MODEL & RUN SENTIMENT ANALYSIS
        logger.info("--- [STAGE 2/2] Running AI Sentiment Analysis ---")
        
        # Load the Hugging Face Pipeline once (keeps memory clean and fast!)
        pipe = load_sentiment_model(model_name)
        
        for symbol in symbols:
            # Fetch unprocessed posts from DB, clean them, and analyze sentiment
            run_sentiment_analysis_on_raw_data(conn, symbol, pipe, limit=posts_limit)
            
        logger.info(" NLP SENTIMENT PIPELINE RUN COMPLETED")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise
        
    finally:
        # 5. Clean up the database connection when done
        conn.close()
        logger.info("Database connection closed. Good bye!")


if __name__ == "__main__":
    run_entire_nlp_pipeline()