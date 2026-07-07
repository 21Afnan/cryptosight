
from pathlib import Path
from cryptosight.utils.logger import get_logger
from cryptosight.nlp_.collector import collect_reddit_data
from cryptosight.nlp_.analyzer import run_analyzer_pipeline

logger = get_logger("NLP_MAIN")


def run_entire_nlp_pipeline(config_path: str = None):
    """
    Orchestrates the entire NLP workflow.
    """
    logger.info("STARTING NLP INGESTION & SENTIMENT PIPELINE")    
    # Resolve config path if not provided
    if config_path is None:
        config_path = str(Path(__file__).parent / "config.yaml")
        
    try:
        # Step 1: Collect raw Reddit data (posts + comments)
        logger.info("Step 1/2: Scraping raw Reddit data...")
        collect_reddit_data(config_path=config_path)
        
        # Step 2: Clean, chunk, and classify sentiment via ModernFinBERT
        logger.info("Step 2/2: Cleaning and running AI sentiment analyzer...")
        run_analyzer_pipeline(config_path=config_path)
        
        logger.info("NLP PIPELINE COMPLETED SUCCESSFULLY!")
        
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


if __name__ == "__main__":
    run_entire_nlp_pipeline()
