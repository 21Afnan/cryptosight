import sys
from cryptosight.utils.db import get_connection
from cryptosight.simulator.simulation import SimulatorEngine
from cryptosight.utils.logger import get_logger

logger = get_logger("SimulatorMain")


def main() -> tuple:
    """
    Main function to run the simulation engine pipeline.
    Opens database connection, initializes SimulatorEngine, and runs all simulations.
    Returns tuple of (results_dict, exec_config_dict).
    """
    conn = get_connection()
    try:
        engine = SimulatorEngine(conn=conn)
        results = engine.run_all_simulations()
        return results, engine.exec_config
    finally:
        conn.close()


if __name__ == "__main__":
    
    print("      RUNNING SEQUENTIAL EVENT-DRIVEN SIMULATION ENGINE")

    results, exec_config = main()

    print("\n" + "=" * 65)
    print("                 SIMULATION RESULTS SHOWCASE")
    
    print(f"Total Strategies Simulated: {len(results)}")
    print(f"Initial Account Balance:   ${exec_config['initial_balance']:,.2f}\n")

    for s_name, ledger in results.items():
        if ledger is not None and not ledger.empty:
            final_bal = ledger["final_balance"].iloc[-1]
            net_pnl = final_bal - exec_config['initial_balance']
            win_count = (ledger["net_pnl"] > 0).sum()
            win_rate = (win_count / len(ledger) * 100.0) if len(ledger) > 0 else 0.0
            print(f" • Strategy: '{s_name}'")
            print(f"   - Simulated Trades: {len(ledger)}")
            print(f"   - Win Rate:         {win_rate:.2f}%")
            print(f"   - Net PnL:          ${net_pnl:+,.2f}")
            print(f"   - Final Balance:    ${final_bal:,.2f}")
            print("-" * 55)
        else:
            print(f" • Strategy: '{s_name}' -> 0 trades executed or insufficient candle data.")
         
    print("=" * 65)
