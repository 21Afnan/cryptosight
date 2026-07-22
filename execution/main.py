import os
import sys
import json
from pathlib import Path
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import get_connection
from cryptosight.execution.executor import ExecutionEngine

logger = get_logger("ExecutionMain")


def run_executor(strategy_id: str = None, exchange: str = "bybit", order_type: str = "Market") -> dict:
    """
    Master entry point for running the Live Execution Engine pipeline 
    on top high-return Bybit strategies using a single shared DB connection.
    """
    conn = get_connection()
    try:
        engine = ExecutionEngine(conn=conn)
        return engine.run_pipeline(strategy_id=strategy_id, exchange=exchange, order_type=order_type)
    finally:
        try:
            conn.close()
            logger.info("Shared DB connection closed cleanly.")
        except Exception:
            pass


if __name__ == "__main__":
    logger.info("=== Executing Bybit High-Return Strategy Live Execution Pipeline ===")
    results = run_executor(exchange="bybit", order_type="Market")
    print(f"\nExecution Engine Summary:\n{json.dumps(results, indent=2, default=str)}\n")
