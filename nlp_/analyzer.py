import re
from pathlib import Path
from cryptosight.utils.db import get_connection
from cryptosight.utils.config import load_config
from cryptosight.utils.logger import get_logger
from cryptosight.nlp_.db import fetch_unprocessed_posts, insert_sentiment_result

logger = get_logger("NLP_ANALYZER")

from transformers import pipeline


def clean_text(text: str) -> str:
    """
    Cleans text by removing URLs, HTML tags, and extra spaces.
    """
    if not text:
        return ""
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # Remove URLs
    text = re.sub(r'<.*?>', '', text)                  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text).strip()           # Remove extra whitespace
    return text


class SentimentAnalyzer:
    """
    Loads ModernFinBERT model and analyzes text sentiment.
    """
    def __init__(self, model_name: str, confidence_threshold: float):
        self.threshold = confidence_threshold
        logger.info(f"Loading AI Model: {model_name}...")
        self.pipe = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name)
        logger.info("AI Model loaded successfully!")
        
    def analyze(self, text: str) -> dict:
        """
        Classifies sentiment as Bullish, Bearish, or Neutral by dividing long text
        into 500-character chunks, analyzing each, and aggregating results.
        """
        if not text or not text.strip():
            return {"sentiment": "Neutral", "confidence": 1.0}
            
        # Split text into chunks of 500 characters
        chunk_size = 500
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        results = []
        for chunk in chunks:
            try:
                prediction = self.pipe(chunk)[0]
                label = prediction["label"].lower()
                score = float(prediction["score"])
                results.append((label, score))
            except Exception as e:
                logger.error(f"Prediction error on chunk: {e}")
                
        if not results:
            return {"sentiment": "Neutral", "confidence": 0.0}
            
        # Aggregate scores by mapping labels
        label_scores = {"bullish": [], "bearish": [], "neutral": []}
        for label, score in results:
            if "positive" in label or "bullish" in label:
                label_scores["bullish"].append(score)
            elif "negative" in label or "bearish" in label:
                label_scores["bearish"].append(score)
            else:
                label_scores["neutral"].append(score)
                
        # Find winning label with highest total confidence sum
        sums = {k: sum(v) for k, v in label_scores.items()}
        winning_label = max(sums, key=sums.get)
        
        # Calculate average confidence score of the winning label
        winning_scores = label_scores[winning_label]
        avg_confidence = sum(winning_scores) / len(winning_scores) if winning_scores else 0.0
        
        sentiment = winning_label.capitalize()
        
        # Apply confidence threshold
        if avg_confidence < self.threshold:
            return {"sentiment": "Neutral", "confidence": round(avg_confidence, 4)}
            
        return {"sentiment": sentiment, "confidence": round(avg_confidence, 4)}


def run_analyzer_pipeline(config_path: str | Path = None):
    """
    Main pipeline:
    1. Loads symbols and model settings from config.
    2. Fetches raw unprocessed posts.
    3. Cleans text, runs AI sentiment analysis, and saves results.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
        
    config = load_config(config_path)
    symbols = config.get("symbols", ["BTC", "ADA"])
    
    model_cfg = config.get("model", {})
    model_name = model_cfg.get("name", "tabularisai/ModernFinBERT")
    threshold = model_cfg.get("confidence_threshold", 0.60)
    
    analyzer = SentimentAnalyzer(model_name, threshold)
    conn = get_connection()
    
    try:
        for symbol in symbols:
            logger.info(f"Processing sentiment for symbol: {symbol}")
            
            # Fetch up to 100 unprocessed posts for this symbol
            posts = fetch_unprocessed_posts(conn, symbol, limit=100)
            if not posts:
                logger.info(f"No new posts to analyze for {symbol}.")
                continue
                
            for post in posts:
                cleaned_title = clean_text(post.get("title", ""))
                cleaned_body = clean_text(post.get("body", ""))
                
                # Clean each comment in the array
                raw_comments = post.get("comments") or []
                cleaned_comments = [clean_text(c) for c in raw_comments if clean_text(c)]
                
                # Combine title and body for the main sentiment evaluation
                full_text = f"{cleaned_title}. {cleaned_body}".strip()
                result = analyzer.analyze(full_text)
                
                record = {
                    "post_id": post["post_id"],
                    "created_utc": post["created_utc"],
                    "cleaned_title": cleaned_title,
                    "cleaned_body": cleaned_body,
                    "cleaned_comments": cleaned_comments,
                    "sentiment": result["sentiment"],
                    "confidence": result["confidence"]
                }
                
                # Save results to database (reddit_cleaned.<symbol>)
                insert_sentiment_result(conn, symbol, record)
                
        logger.info("Analyzer pipeline executed successfully!")
    except Exception as e:
        logger.error(f"Analyzer error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_analyzer_pipeline()
