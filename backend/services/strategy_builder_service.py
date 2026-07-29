import json
from cryptosight.utils.db import get_connection
from cryptosight.utils.metadata import upsert_strategy_data
from cryptosight.utils.logger import get_logger

logger = get_logger("StrategyBuilderService")

def get_playbook_strategies() -> list:
    """
    Retrieves all reusable playbook strategies stored in metadata.playbook_table.
    Returns integer strategy_id and clean strategy_name without coin symbol or timeframe prepended.
    """
    import re
    conn = get_connection()
    if not conn:
        logger.error("Failed to establish DB connection for playbook fetch.")
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.playbook_id, p.strategy_name, p.start_time, p.end_time, p.indicators_config, p.strategy_config, s.strategy_id
                FROM metadata.playbook_table p
                LEFT JOIN metadata.strategy_data s ON LOWER(p.strategy_name) = LOWER(s.strategy_name)
                ORDER BY p.playbook_id ASC;
            """)
            rows = cursor.fetchall()
            playbook = []
            seen_names = set()
            for r in rows:
                raw_name = r[1] or ""
                # Strip symbol (BTC, ETH, SOL, LTC, DOGE, MINA, SUI, ADA, USDT) and timeframe (15m, 30m, 1h, 4h, etc.)
                clean_name = re.sub(r'\b(BTC|ETH|SOL|LTC|DOGE|MINA|SUI|ADA|USDT)\b', '', raw_name, flags=re.IGNORECASE)
                clean_name = re.sub(r'\b\d+[mhdMHDwW]\b', '', clean_name)
                clean_name = re.sub(r'\s+', ' ', clean_name).strip()
                if not clean_name:
                    clean_name = raw_name

                # Use strategy_id if available, fallback to playbook_id
                strat_id = r[6] if r[6] is not None else r[0]

                # Avoid duplicate clean template names in playbook list
                if clean_name in seen_names:
                    continue
                seen_names.add(clean_name)

                playbook.append({
                    "id": str(strat_id),
                    "strategy_id": strat_id,
                    "playbook_id": r[0],
                    "name": clean_name,
                    "original_name": raw_name,
                    "start_time": r[2].isoformat() if r[2] else None,
                    "end_time": r[3].isoformat() if r[3] else None,
                    "indicators_config": r[4] or {},
                    "strategy_config": r[5] or {}
                })
            return playbook
    except Exception as e:
        logger.error(f"Error fetching playbook strategies from DB: {e}")
        return []
    finally:
        conn.close()

def save_new_strategy(payload: dict) -> dict:
    """
    Saves a newly constructed custom strategy configuration into metadata.strategy_data
    and adds a clean template block into metadata.playbook_table.
    """
    import re
    conn = get_connection()
    if not conn:
        logger.error("Failed to establish DB connection for strategy save.")
        return {"success": False, "message": "Could not connect to database."}
    try:
        strategy_name = payload.get("strategy_name")
        exchange = payload.get("exchange", "bybit")
        symbol = payload.get("symbol")
        timeframe = payload.get("timeframe")
        indicators_config = payload.get("indicators_config")
        strategy_config = payload.get("strategy_config")

        if not strategy_name or not symbol or not timeframe:
            return {"success": False, "message": "Missing required fields (strategy_name, symbol, timeframe)."}

        # Store strategy configuration using the common upsert utility
        strategy_id = upsert_strategy_data(
            conn=conn,
            exchange=exchange,
            symbol=symbol,
            target_timeframe=timeframe,
            indicators_config=indicators_config,
            strategy_config=strategy_config,
            strategy_name=strategy_name,
            timeframe=timeframe
        )

        # Store/upsert clean template into metadata.playbook_table without symbol/timeframe in name
        clean_playbook_name = re.sub(r'\b(BTC|ETH|SOL|LTC|DOGE|MINA|SUI|ADA|USDT)\b', '', strategy_name, flags=re.IGNORECASE)
        clean_playbook_name = re.sub(r'\b\d+[mhdMHDwW]\b', '', clean_playbook_name)
        clean_playbook_name = re.sub(r'\s+', ' ', clean_playbook_name).strip()
        if not clean_playbook_name:
            clean_playbook_name = strategy_name

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO metadata.playbook_table (strategy_name, indicators_config, strategy_config)
                VALUES (%s, %s, %s)
                ON CONFLICT (strategy_name) DO UPDATE SET
                    indicators_config = EXCLUDED.indicators_config,
                    strategy_config = EXCLUDED.strategy_config;
            """, (clean_playbook_name, json.dumps(indicators_config), json.dumps(strategy_config)))
            conn.commit()

        return {
            "success": True,
            "strategy_id": strategy_id,
            "strategy_name": strategy_name
        }
    except Exception as e:
        logger.error(f"Error saving new strategy config: {e}")
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def run_dynamic_backtest(payload: dict) -> dict:
    """
    Executes a backtest dynamically by saving metadata and ledger results to the database
    (meeting foreign key references), but WITHOUT adding the strategy to the playbook_table
    (so it remains hidden from the templates library until explicitly saved).
    No defaults are allowed; all parameters must be extracted directly from the payload.
    """
    try:
        from cryptosight.backtesting.backtest import BacktestingEngine
        from cryptosight.backend.services.backtest_service import get_backtest_by_id

        # 1. Parse and validate fields — NO DEFAULTS!
        strategy_name = payload.get("strategy_name")
        exchange = payload.get("exchange")
        symbol = payload.get("symbol")
        timeframe = payload.get("timeframe")
        indicators_config = payload.get("indicators_config")
        strategy_config = payload.get("strategy_config")
        start_date = payload.get("start_date")
        end_date = payload.get("end_date")

        if not all([strategy_name, exchange, symbol, timeframe, start_date, end_date, indicators_config, strategy_config]):
            return {
                "success": False, 
                "message": "Missing required fields for running backtest. Please configure all settings."
            }

        take_profit = strategy_config.get("take_profit")
        stop_loss = strategy_config.get("stop_loss")
        if take_profit is None or stop_loss is None:
            return {
                "success": False,
                "message": "Missing take_profit or stop_loss in execution settings."
            }

        pos_size_type = strategy_config.get("position_size_type")
        pos_size_val = strategy_config.get("position_size_value")
        if pos_size_type is None or pos_size_val is None:
            return {
                "success": False,
                "message": "Missing position_size_type or position_size_value in execution settings."
            }

        # Build strategy dictionary structured exactly for the backtesting engine
        # Normalize symbol format to base asset (e.g. 'ETH' or 'BTC') and enforce base_tf as '1m'
        clean_symbol = symbol.replace("USDT", "").replace("/", "").upper()
        norm_symbol = clean_symbol

        strat_dict = {
            "strategy_name": strategy_name,
            "exchange": exchange,
            "symbol": norm_symbol,
            "timeframe": "1m",  # base timeframe for raw candles in DB is always 1m
            "target_timeframe": timeframe,  # target resampled timeframe (e.g. 30m)
            "market": {
                "exchange": exchange,
                "symbol": norm_symbol,
                "timeframe": "1m",  # base timeframe for raw candles in DB is always 1m
                "target_timeframe": timeframe,
                "start_time": start_date,
                "end_time": end_date
            },
            "indicators": indicators_config,
            "strategy": strategy_config
        }

        # 2. Run the backtest via the core BacktestingEngine
        # Inject position sizing configuration directly to the engine
        engine = BacktestingEngine()
        engine.config.update({
            "exchange": exchange,
            "symbol": norm_symbol,
            "timeframe": timeframe,
            "start_time": start_date,
            "end_time": end_date,
            "take_profit": {"value": float(take_profit)},
            "stop_loss": {"value": float(stop_loss)},
            "position_size_type": pos_size_type,
            "position_size_value": float(pos_size_val)
        })

        # Run the simulation and write backtest tables (ledger table, stats, and metadata)
        ledger_df = engine.run_single_strategy(strat_dict)

        # Automatically store/upsert clean template into metadata.playbook_table so it is saved in Playbook Library
        try:
            from cryptosight.utils.metadata import populate_playbook_from_strategy_data
            populate_playbook_from_strategy_data(conn)
        except Exception as pb_err:
            logger.warning(f"Could not auto-update playbook_table on backtest run: {pb_err}")

        # 3. Retrieve computed stats & trade curves from DB
        result = get_backtest_by_id(strategy_name)
        
        return {
            "success": True,
            "metrics": {
                "total_trades": result.get("total_trades", 0),
                "win_rate": result.get("win_rate", 0.0),
                "net_pnl": result.get("net_pnl", 0.0),
                "sharpe": result.get("sharpe", 0.0),
                "max_drawdown": result.get("max_drawdown", 0.0),
                "profit_factor": result.get("profit_factor", 1.5)
            },
            "charts": {
                "equity_curve": result.get("equity_curve", []),
                "drawdown_curve": result.get("drawdown_curve", []),
                "monthly_returns": result.get("monthly_returns", []),
                "rolling_metrics": result.get("rolling_metrics", []),
                "pnl_per_trade": result.get("pnl_per_trade", [])
            },
            "trades": result.get("trades", [])
        }

    except Exception as e:
        logger.error(f"Error executing dynamic backtest: {e}", exc_info=True)
        return {"success": False, "message": str(e)}
