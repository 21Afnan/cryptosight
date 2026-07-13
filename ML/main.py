from pathlib import Path
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config
from cryptosight.ml.features import MLFeatureBuilder
logger = get_logger("MLMain")

def get_ml_dataset(config_path: str | Path = None) -> dict[str, pd.DataFrame]:
    """
    ONE unified entry point returning clean, fully engineered and target-labeled DataFrames.
    Loads `ml_config.yaml` once from disk and passes the loaded dictionary `config` to `MLFeatureBuilder`.
    """
    logger.info("Starting Cryptosight Quant ML Data Pipeline ")
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "ml_config.yaml"
    
    # Load config once from disk (`Single Source of Truth`)
    config = load_config(config_path)

    # Pass pure dictionary to MLFeatureBuilder (in-memory quant engine)
    builder = MLFeatureBuilder(config=config)
    datasets = builder.build_dataset()
    logger.info(" ML Data Pipeline Execution Complete ")
    return datasets


if __name__ == "__main__":
    get_ml_dataset()
