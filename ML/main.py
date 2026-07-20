import sys
from pathlib import Path

from cryptosight.ml.pipeline import QuantMLPipeline
def orchestrate_ml_pipeline(config_path: str | Path = None):
    """Backward-compatible wrapper."""
    return QuantMLPipeline(config_path).run_pipeline()


if __name__ == "__main__":
    orchestrate_ml_pipeline()
