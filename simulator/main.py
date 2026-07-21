import json
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import get_connection
from cryptosight.simulator.simulator import SimulatorEngine

logger = get_logger("SimulatorMain")


def run_simulator(strategy_id: str = None) -> dict:
    """Master entry point for executing the quantitative simulation pipeline."""
    conn = get_connection()
    try:
        engine = SimulatorEngine(conn=conn)
        return engine.run_pipeline(strategy_id=strategy_id)
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("=== Executing Simulator Pipeline ===")
    results = run_simulator()
    logger.info(f"Simulator Execution Summary:\n{json.dumps(results, indent=2, default=str)}")
