"""
Strategy Selector Module for Cryptosight Execution Engine.
Selects the #1 best enabled strategy from PostgreSQL based on Net PnL.
"""

from cryptosight.utils.logger import get_logger

logger = get_logger("StrategySelector")


def get_best_strategy(conn) -> dict:
    """
    Returns the top enabled strategy dictionary from PostgreSQL based on net_pnl.
    Queries simulations.stats first, then falls back to metadata.strategy_data.
    """
    query_stats = """
    SELECT 
        d.strategy_id,
        d.strategy_name,
        d.exchange,
        d.symbol,
        d.timeframe,
        COALESCE(d.target_timeframe, d.timeframe),
        d.indicators_config,
        d.strategy_config,
        COALESCE(s.net_pnl, 0.0),
        COALESCE(s.win_rate, 0.0),
        COALESCE(s.total_trades, 0)
    FROM metadata.strategy_data d
    JOIN simulations.stats s ON d.strategy_id = s.strategy_id
    WHERE d.execution_enabled = TRUE AND COALESCE(s.total_trades, 0) > 0
    ORDER BY s.net_pnl DESC NULLS LAST
    LIMIT 1;
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
    LIMIT 1;
    """

    try:
        with conn.cursor() as cursor:
            # 1. Primary Selection: Query best strategy from simulations.stats by net_pnl
            cursor.execute(query_stats)
            row = cursor.fetchone()
            if row:
                strategy = {
                    "strategy_id": row[0],
                    "strategy_name": row[1],
                    "exchange": str(row[2]).lower(),
                    "symbol": str(row[3]).lower(),
                    "timeframe": row[4],
                    "target_timeframe": row[5],
                    "indicators_config": row[6],
                    "strategy_config": row[7],
                    "net_pnl": float(row[8]),
                    "win_rate": float(row[9]),
                    "total_trades": int(row[10]),
                }
                logger.info(
                    f"Selected #1 Best Enabled Strategy: '{strategy['strategy_name']}' "
                    f"[{strategy['exchange'].upper()} {strategy['symbol'].upper()} {strategy['timeframe']}] "
                    f"Net PnL=${strategy['net_pnl']:,.2f}, Win Rate={strategy['win_rate']:.1f}%."
                )
                return strategy

            # 2. Fallback Selection: Query first strategy where execution_enabled = TRUE
            cursor.execute(query_fallback)
            fb_row = cursor.fetchone()
            if fb_row:
                strategy = {
                    "strategy_id": fb_row[0],
                    "strategy_name": fb_row[1],
                    "exchange": str(fb_row[2]).lower(),
                    "symbol": str(fb_row[3]).lower(),
                    "timeframe": fb_row[4],
                    "target_timeframe": fb_row[5],
                    "indicators_config": fb_row[6],
                    "strategy_config": fb_row[7],
                    "net_pnl": 0.0,
                    "win_rate": 0.0,
                    "total_trades": 0,
                }
                logger.info(
                    f"Selected Fallback Enabled Strategy: '{strategy['strategy_name']}' "
                    f"[{strategy['exchange'].upper()} {strategy['symbol'].upper()} {strategy['timeframe']}]."
                )
                return strategy

            logger.warning("No strategy found in metadata.strategy_data with execution_enabled = TRUE.")

    except Exception as error:
        conn.rollback()
        logger.error(f"Error in strategy selector: {error}")

    return None
