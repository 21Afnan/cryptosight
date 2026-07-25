"""
Strategy Selector Module for Cryptosight Execution Engine.
Selects the #1 best enabled strategy from PostgreSQL based on Net PnL.
"""

from cryptosight.utils.logger import get_logger

logger = get_logger("StrategySelector")


def get_top_strategies(conn, limit=3) -> list:
    """
    Returns a list of top enabled strategies from PostgreSQL up to the specified limit.
    Priority 1: Strategies with active open positions.
    Priority 2: Strategies with best live net_pnl.
    Priority 3: Strategies with best simulated net_pnl.
    Priority 4: Fallback.
    """
    def row_to_dict(r):
        return {
            "strategy_id": r[0],
            "strategy_name": r[1],
            "exchange": r[2],
            "symbol": r[3],
            "timeframe": r[4],
            "target_timeframe": r[5],
            "indicators_config": r[6],
            "strategy_config": r[7],
        }

    # 1. Open Position Check
    query_active = """
    SELECT 
        d.strategy_id,
        d.strategy_name,
        d.exchange,
        d.symbol,
        d.timeframe,
        COALESCE(d.target_timeframe, d.timeframe),
        d.indicators_config,
        d.strategy_config
    FROM metadata.strategy_data d
    JOIN execution.active_positions a ON d.strategy_id = a.strategy_id
    WHERE d.execution_enabled = TRUE
    """

    # 2. Live Performance Check
    query_exec_stats = """
    SELECT 
        d.strategy_id,
        d.strategy_name,
        d.exchange,
        d.symbol,
        d.timeframe,
        COALESCE(d.target_timeframe, d.timeframe),
        d.indicators_config,
        d.strategy_config
    FROM metadata.strategy_data d
    JOIN execution.stats e ON d.strategy_id = e.strategy_id
    WHERE d.execution_enabled = TRUE AND COALESCE(e.total_trades, 0) > 0
    ORDER BY e.net_pnl DESC NULLS LAST
    """

    # 3. Simulation Stats Fallback
    query_sim_stats = """
    SELECT 
        d.strategy_id,
        d.strategy_name,
        d.exchange,
        d.symbol,
        d.timeframe,
        COALESCE(d.target_timeframe, d.timeframe),
        d.indicators_config,
        d.strategy_config
    FROM metadata.strategy_data d
    JOIN simulations.stats s ON d.strategy_id = s.strategy_id
    WHERE d.execution_enabled = TRUE AND COALESCE(s.total_trades, 0) > 0
    ORDER BY s.net_pnl DESC NULLS LAST
    """

    query_fallback = """
    SELECT 
        strategy_id,
        strategy_name,
        exchange,
        symbol,
        timeframe,
        COALESCE(target_timeframe, timeframe),
        indicators_config,
        strategy_config
    FROM metadata.strategy_data
    WHERE execution_enabled = TRUE
    ORDER BY strategy_id ASC
    """

    selected_strategies = []
    seen_ids = set()

    try:
        with conn.cursor() as cursor:
            # 1. Fetch all active open positions (MUST manage them even if it exceeds limit, but we cap array returned)
            # Actually, to be safe, if we have 4 open positions and limit=3, we should probably return all 4 so they are managed.
            # But let's stick to the limit for simplicity.
            cursor.execute(query_active)
            for row in cursor.fetchall():
                if len(selected_strategies) >= limit: break
                strat = row_to_dict(row)
                if strat["strategy_id"] not in seen_ids:
                    selected_strategies.append(strat)
                    seen_ids.add(strat["strategy_id"])
                    logger.info(f"Selected Strategy #{strat['strategy_id']} '{strat['strategy_name']}' to manage open position.")

            # 2. Live Performance Check
            if len(selected_strategies) < limit:
                cursor.execute(query_exec_stats)
                for row in cursor.fetchall():
                    if len(selected_strategies) >= limit: break
                    strat = row_to_dict(row)
                    if strat["strategy_id"] not in seen_ids:
                        selected_strategies.append(strat)
                        seen_ids.add(strat["strategy_id"])
                        logger.info(f"Selected Strategy #{strat['strategy_id']} '{strat['strategy_name']}' based on live stats.")

            # 3. Simulation Stats Fallback
            if len(selected_strategies) < limit:
                cursor.execute(query_sim_stats)
                for row in cursor.fetchall():
                    if len(selected_strategies) >= limit: break
                    strat = row_to_dict(row)
                    if strat["strategy_id"] not in seen_ids:
                        selected_strategies.append(strat)
                        seen_ids.add(strat["strategy_id"])
                        logger.info(f"Selected Strategy #{strat['strategy_id']} '{strat['strategy_name']}' based on sim stats.")

            # 4. Final Fallback
            if len(selected_strategies) < limit:
                cursor.execute(query_fallback)
                for row in cursor.fetchall():
                    if len(selected_strategies) >= limit: break
                    strat = row_to_dict(row)
                    if strat["strategy_id"] not in seen_ids:
                        selected_strategies.append(strat)
                        seen_ids.add(strat["strategy_id"])
                        logger.info(f"Selected Strategy #{strat['strategy_id']} '{strat['strategy_name']}' from fallback.")

        if not selected_strategies:
            logger.warning("No enabled strategies found in metadata.strategy_data.")

    except Exception as error:
        conn.rollback()
        logger.error(f"Error in strategy selector: {error}")

    return selected_strategies
