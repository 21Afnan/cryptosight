"""
Master Execution Entry Point for Cryptosight Engine.
Executed periodically via Windows batch runner.
Contains a single function call to trigger the execution cycle.
"""

from cryptosight.execution.engine import run_execution_cycle


def main():
    """Triggers one complete execution cycle."""
    run_execution_cycle()


if __name__ == "__main__":
    main()
