from cryptosight.utils.logger import get_logger
from cryptosight.simulator.simulation import SimulatorEngine

logger = get_logger("Main")

def main():
    logger.info("CRYPTOSIGHT QUANT SIMULATOR ORCHESTRATOR")
    try:
        # Initialize simulation engine
        engine = SimulatorEngine()    
        # Run sequential paper trading simulation
        engine.run_simulation()
    except Exception as e:
        logger.error(f"Simulation run failed: {e}")

if __name__ == "__main__":
    main()

