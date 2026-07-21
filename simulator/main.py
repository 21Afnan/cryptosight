from cryptosight.utils.logger import get_logger
from cryptosight.simulator.simulation import run_all_simulations

logger = get_logger("Main")

def main():
    logger.info("CRYPTOSIGHT QUANT SIMULATOR ORCHESTRATOR")
    try:
        # Run sequential paper trading simulation for all DB strategies
        run_all_simulations()
    except Exception as e:
        logger.error(f"Simulation run failed: {e}")

if __name__ == "__main__":
    main()

