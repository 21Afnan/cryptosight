import json
from cryptosight.execution.engine import ExecutionEngine
from cryptosight.utils.logger import get_logger

logger = get_logger("ExecutionMain")


def run_execution(strategy_id: str = None) -> dict:
    """Entry point caller function for the Bybit Live Execution Engine."""
    logger.info("=== Executing Bybit Live Execution Engine Pipeline ===")
    engine = ExecutionEngine()
    results = engine.run_pipeline(strategy_id=strategy_id)
    logger.info("Execution Pipeline Summary:\n" + json.dumps(results, indent=2, default=str))
    return results


if __name__ == "__main__":
    run_execution()
