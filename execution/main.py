import os
import sys
import json
from pathlib import Path
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import get_connection
from cryptosight.execution.executor import ExecutionEngine

logger = get_logger("ExecutionMain")


def run_executor(strategy_id: str = None, exchange: str = None, top_n: int = None) -> dict:
    """
    Master entry point for running the Live Execution Engine pipeline 
    on top high-return strategies using a single shared DB connection.
    Reads top_n dynamically from metadata.execution_settings table if top_n is None.
    """
    conn = get_connection()
    try:
        engine = ExecutionEngine(conn=conn)
        return engine.run_pipeline(strategy_id=strategy_id, exchange=exchange, top_n=top_n)
    finally:
        try:
            conn.close()
            logger.info("Shared DB connection closed cleanly.")
        except Exception:
            pass


if __name__ == "__main__":
    logger.info("=== Executing High-Return Strategy Live Execution Pipeline ===")
    results = run_executor()
    print(f"\nExecution Engine Summary:\n{json.dumps(results, indent=2, default=str)}\n")
