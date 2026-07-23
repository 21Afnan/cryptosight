import json
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import get_connection, get_table_names, get_signals_table_names

logger = get_logger("MetadataManager")


def create_metadata_schema(conn):
    """Creates the 'metadata' schema in PostgreSQL if it does not already exist."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS metadata;")
            conn.commit()
            logger.info("Schema 'metadata' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating schema 'metadata': {error}")
        raise


def create_market_data(conn):
    """
    Creates the 'metadata.market_data' table with exact columns and stats tracking.
    """
    create_metadata_schema(conn)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS metadata.market_data (
        id SERIAL PRIMARY KEY,
        exchange VARCHAR(32) NOT NULL,
        symbol VARCHAR(32) NOT NULL,
        timeframe VARCHAR(16) NOT NULL,
        schema_name VARCHAR(64) NOT NULL,
        table_name VARCHAR(64) NOT NULL,
        start_time TIMESTAMP WITH TIME ZONE,
        end_time TIMESTAMP WITH TIME ZONE,
        row_count BIGINT DEFAULT 0,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_market_dataset UNIQUE (exchange, symbol, timeframe)
    );
    """
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_market_data_lookup 
    ON metadata.market_data (exchange, symbol, timeframe);
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            conn.commit()
            logger.info("Table 'metadata.market_data' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'metadata.market_data': {error}")
        raise


def upsert_market_data(conn, exchange: str, symbol: str, timeframe: str):
    """
    Updates or inserts the metadata record for a specific market dataset inside `metadata.market_data`.
    Auto-fetches the latest candle counts (`row_count`), `start_time`, and `end_time` from the data table.
    """
    create_market_data(conn)

    schema_name, table_name = get_table_names(exchange, symbol, timeframe)
    full_table = f"{schema_name}.{table_name}"

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s);", (schema_name, table_name))
            if not cursor.fetchone()[0]:
                logger.warning(f"Cannot update metadata: Table '{full_table}' does not exist yet.")
                return

            cursor.execute(f"SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM {full_table};")
            start_time, end_time, row_count = cursor.fetchone()

            upsert_sql = """
            INSERT INTO metadata.market_data (
                exchange, symbol, timeframe, schema_name, table_name,
                start_time, end_time, row_count, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (exchange, symbol, timeframe) DO UPDATE SET
                schema_name = EXCLUDED.schema_name,
                table_name = EXCLUDED.table_name,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                row_count = EXCLUDED.row_count,
                last_updated = CURRENT_TIMESTAMP;
            """
            cursor.execute(upsert_sql, (exchange.lower(), symbol.lower(), timeframe.lower(), schema_name, table_name, start_time, end_time, row_count))
            conn.commit()
            logger.info(f"Market metadata refreshed for '{exchange.upper()}' {symbol.upper()} [{timeframe}]: {row_count} candles ({start_time} to {end_time}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating market metadata for '{full_table}': {error}")
        raise


def create_sentiment_data(conn):
    """
    Creates the 'metadata.sentiment_data' table to track Reddit raw & cleaned sentiment tables.
    """
    create_metadata_schema(conn)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS metadata.sentiment_data (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(32) NOT NULL UNIQUE,
        raw_schema VARCHAR(64) NOT NULL DEFAULT 'reddit_raw',
        raw_table VARCHAR(64) NOT NULL,
        cleaned_schema VARCHAR(64) NOT NULL DEFAULT 'reddit_cleaned',
        cleaned_table VARCHAR(64) NOT NULL,
        total_posts BIGINT DEFAULT 0,
        bullish_count BIGINT DEFAULT 0,
        bearish_count BIGINT DEFAULT 0,
        neutral_count BIGINT DEFAULT 0,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_sentiment_data_lookup 
    ON metadata.sentiment_data (symbol);
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            conn.commit()
            logger.info("Table 'metadata.sentiment_data' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'metadata.sentiment_data': {error}")
        raise


def upsert_sentiment_data(conn, symbol: str):
    """
    Updates or inserts the metadata record for a coin's sentiment data inside `metadata.sentiment_data`.
    Auto-fetches total posts, bullish, bearish, and neutral counts right from `reddit_cleaned.<symbol>`.
    """
    create_sentiment_data(conn)

    sym = symbol.lower()
    raw_table = sym
    cleaned_table = sym
    full_cleaned_table = f"reddit_cleaned.{sym}"

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'reddit_cleaned' AND tablename = %s);", (sym,))
            if not cursor.fetchone()[0]:
                logger.warning(f"Cannot update sentiment metadata: Table '{full_cleaned_table}' does not exist yet.")
                return

            cursor.execute(f"""
                SELECT 
                    COUNT(*),
                    COUNT(*) FILTER (WHERE sentiment = 'Bullish'),
                    COUNT(*) FILTER (WHERE sentiment = 'Bearish'),
                    COUNT(*) FILTER (WHERE sentiment = 'Neutral')
                FROM {full_cleaned_table};
            """)
            total_posts, bullish_count, bearish_count, neutral_count = cursor.fetchone()

            upsert_sql = """
            INSERT INTO metadata.sentiment_data (
                symbol, raw_schema, raw_table, cleaned_schema, cleaned_table,
                total_posts, bullish_count, bearish_count, neutral_count, last_updated
            )
            VALUES (%s, 'reddit_raw', %s, 'reddit_cleaned', %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (symbol) DO UPDATE SET
                total_posts = EXCLUDED.total_posts,
                bullish_count = EXCLUDED.bullish_count,
                bearish_count = EXCLUDED.bearish_count,
                neutral_count = EXCLUDED.neutral_count,
                last_updated = CURRENT_TIMESTAMP;
            """
            cursor.execute(upsert_sql, (sym, raw_table, cleaned_table, total_posts, bullish_count, bearish_count, neutral_count))
            conn.commit()
            logger.info(f"Sentiment metadata refreshed for '{sym.upper()}': {total_posts} posts ({bullish_count} Bullish, {bearish_count} Bearish).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating sentiment metadata for '{full_cleaned_table}': {error}")
        raise


# ── STRATEGY DATA ────────────────────────────────────────────────────────────

def generate_strategy_id(exchange: str, symbol: str, target_timeframe: str, indicators_config: dict = None, strategy_config: dict = None, sim_params: dict = None) -> str:
    """
    Generates a deterministic, human-readable strategy_id based on exchange, symbol (coin),
    target_timeframe, indicators, and strategy exit settings (TP/SL).
    Example: 'binance_btc_1h_rsi_14_tp5_sl2'
    """
    ind_parts = []
    if indicators_config and isinstance(indicators_config, dict):
        for ind_name, configs in sorted(indicators_config.items()):
            if isinstance(configs, list):
                for cfg in configs:
                    if isinstance(cfg, dict):
                        params = cfg.get("parameters", {})
                        param_vals = [str(v) for k, v in sorted(params.items()) if isinstance(v, (int, float))]
                        if param_vals:
                            ind_parts.append(f"{ind_name.lower()}_{'_'.join(param_vals)}")
                        else:
                            ind_parts.append(ind_name.lower())
            else:
                ind_parts.append(str(ind_name).lower())
    
    ind_str = f"_{'_'.join(sorted(set(ind_parts)))}" if ind_parts else ""

    # Add TP and SL to the strategy ID to make them unique
    strat_parts = []
    if strategy_config and isinstance(strategy_config, dict):
        tp = strategy_config.get('take_profit')
        sl = strategy_config.get('stop_loss')
        if tp is not None:
            # TP/SL are now direct percentages (e.g., 5). 
            # Replace decimals with underscore just in case someone uses 2.5% (e.g., tp2_5)
            tp_str = str(tp).replace('.', '_')
            strat_parts.append(f"tp{tp_str}")
        if sl is not None:
            sl_str = str(sl).replace('.', '_')
            strat_parts.append(f"sl{sl_str}")
            
    if sim_params and isinstance(sim_params, dict):
        import hashlib
        # Hash the sim_params to avoid excessively long table names
        sim_str = "_".join(f"{k}{v}" for k, v in sorted(sim_params.items()))
        sim_hash = hashlib.md5(sim_str.encode()).hexdigest()[:6]
        strat_parts.append(f"sim{sim_hash}")
            
    strat_str = f"_{'_'.join(strat_parts)}" if strat_parts else ""
    
    return f"{exchange.lower()}_{symbol.lower()}_{target_timeframe.lower()}{ind_str}{strat_str}"



def create_strategy_data(conn):
    """
    Creates the 'metadata.strategy_data' table to track signal pipeline strategy configurations.
    Col 1: strategy_id (BIGSERIAL PRIMARY KEY, 1, 2, 3...)
    Col 2: strategy_name (VARCHAR(128) UNIQUE NOT NULL)
    """
    create_metadata_schema(conn)

    try:
        with conn.cursor() as cursor:
            # Migration check: if strategy_id is VARCHAR, drop old tables to recreate with BIGSERIAL (1, 2, 3...)
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'metadata' 
                  AND table_name = 'strategy_data' 
                  AND column_name = 'strategy_id';
            """)
            col_type = cursor.fetchone()
            if col_type and col_type[0].lower() in ('character varying', 'text', 'varchar'):
                logger.info("Migrating metadata schema: dropping old VARCHAR strategy_id tables to create BIGSERIAL sequence (1, 2, 3...).")
                cursor.execute("DROP TABLE IF EXISTS metadata.simulator_config CASCADE;")
                cursor.execute("DROP TABLE IF EXISTS metadata.backtest_data CASCADE;")
                cursor.execute("DROP TABLE IF EXISTS metadata.strategy_data CASCADE;")
                conn.commit()

            create_table_sql = """
            CREATE TABLE IF NOT EXISTS metadata.strategy_data (
                strategy_id       BIGSERIAL PRIMARY KEY,
                strategy_name     VARCHAR(128) UNIQUE NOT NULL,
                exchange          VARCHAR(32)  NOT NULL,
                symbol            VARCHAR(32)  NOT NULL,
                target_timeframe  VARCHAR(16)  NOT NULL,

                indicators_config JSONB,
                strategy_config   JSONB,

                total_rows        BIGINT DEFAULT 0,
                long_signals      BIGINT DEFAULT 0,
                short_signals     BIGINT DEFAULT 0,
                last_signal_time  TIMESTAMP WITH TIME ZONE,

                last_updated      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            create_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_strategy_data_lookup
            ON metadata.strategy_data (exchange, symbol, target_timeframe);
            """
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            conn.commit()
            logger.info("Table 'metadata.strategy_data' verified/created with serial strategy_id and strategy_name.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'metadata.strategy_data': {error}")
        raise


def upsert_strategy_data(
    conn,
    exchange: str,
    symbol: str,
    target_timeframe: str,
    indicators_config: dict,
    strategy_config: dict,
    strategy_name: str = None,
):
    """
    Updates or inserts strategy definition into `metadata.strategy_data`.
    Uses `strategy_name` as UNIQUE key to preserve serial integer `strategy_id` (1, 2, 3...).
    Returns the integer `strategy_id`.
    """
    create_strategy_data(conn)

    if not strategy_name:
        strategy_name = generate_strategy_id(exchange, symbol, target_timeframe, indicators_config, strategy_config)

    schema_name, table_name = get_signals_table_names(exchange, symbol, target_timeframe)
    full_signals_table = f"{schema_name}.{table_name}"

    try:
        with conn.cursor() as cursor:
            # Guard: signals table must already exist
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s);",
                (schema_name, table_name)
            )
            if not cursor.fetchone()[0]:
                logger.warning(
                    f"Cannot update strategy metadata: Signals table '{full_signals_table}' does not exist yet."
                )
                return None

            # Auto-fetch live stats from the signals table
            cursor.execute(f"""
                SELECT
                    COUNT(*),
                    COUNT(*) FILTER (WHERE signal = 1),
                    COUNT(*) FILTER (WHERE signal = -1),
                    MAX(timestamp)
                FROM {full_signals_table};
            """)
            total_rows, long_signals, short_signals, last_signal_time = cursor.fetchone()

            upsert_sql = """
            INSERT INTO metadata.strategy_data (
                strategy_name, exchange, symbol, target_timeframe,
                indicators_config, strategy_config,
                total_rows, long_signals, short_signals,
                last_signal_time, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (strategy_name) DO UPDATE SET
                exchange          = EXCLUDED.exchange,
                symbol            = EXCLUDED.symbol,
                target_timeframe  = EXCLUDED.target_timeframe,
                indicators_config = EXCLUDED.indicators_config,
                strategy_config   = EXCLUDED.strategy_config,
                total_rows        = EXCLUDED.total_rows,
                long_signals      = EXCLUDED.long_signals,
                short_signals     = EXCLUDED.short_signals,
                last_signal_time  = EXCLUDED.last_signal_time,
                last_updated      = CURRENT_TIMESTAMP
            RETURNING strategy_id;
            """
            cursor.execute(upsert_sql, (
                strategy_name, exchange.lower(), symbol.lower(), target_timeframe.lower(),
                json.dumps(indicators_config) if indicators_config else None,
                json.dumps(strategy_config)   if strategy_config   else None,
                total_rows, long_signals, short_signals,
                last_signal_time,
            ))
            strategy_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                f"Strategy metadata saved for ID #{strategy_id} ('{strategy_name}'): {total_rows} rows, "
                f"{long_signals} Long / {short_signals} Short signals."
            )

            # Auto-initialize simulator_config with default settings for strategy_id
            create_simulator_config(conn)
            sim_upsert_sql = """
            INSERT INTO metadata.simulator_config (
                strategy_id, enabled, initial_balance, position_size_type, position_size_value,
                commission, slippage, allow_long, allow_short
            ) VALUES (%s, True, 10000.00, 'fixed_percentage', 10.00, 0.0005, 0.0002, True, True)
            ON CONFLICT (strategy_id) DO NOTHING;
            """
            cursor.execute(sim_upsert_sql, (strategy_id,))
            conn.commit()
            return strategy_id

    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating strategy metadata for '{full_signals_table}': {error}")
        raise


def create_backtest_data(conn):
    """
    Creates the 'metadata.backtest_data' table to track backtest configurations and key metrics.
    Relates to `metadata.strategy_data` via a foreign key on `strategy_id`.
    """
    create_metadata_schema(conn)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS metadata.backtest_data (
        strategy_id       VARCHAR(128) PRIMARY KEY REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
        backtest_config   JSONB NOT NULL,
        total_trades      INT DEFAULT 0,
        win_rate          NUMERIC(5,2) DEFAULT 0.00,
        net_pnl           NUMERIC(18,8) DEFAULT 0.00,
        final_balance     NUMERIC(18,8) DEFAULT 0.00,
        last_updated      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Table 'metadata.backtest_data' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'metadata.backtest_data': {error}")
        raise


def upsert_backtest_data(conn, strategy_id: str, backtest_config: dict, ledger_df):
    """
    Inserts or updates the summary data of a backtest run in `metadata.backtest_data`.
    Calculates summary stats (total_trades, win_rate, net_pnl, final_balance) on the fly.
    """
    create_backtest_data(conn)

    total_trades = len(ledger_df)
    if total_trades > 0:
        net_pnl = float(ledger_df["net_pnl"].sum())
        win_rate = float((ledger_df["net_pnl"] > 0).sum() / total_trades * 100)
        final_balance = float(ledger_df["balance"].iloc[-1])
    else:
        net_pnl = 0.0
        win_rate = 0.0
        final_balance = float(backtest_config.get("initial_balance", 10000.0))

    try:
        with conn.cursor() as cursor:
            upsert_sql = """
            INSERT INTO metadata.backtest_data (
                strategy_id, backtest_config, total_trades,
                win_rate, net_pnl, final_balance, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (strategy_id) DO UPDATE SET
                backtest_config = EXCLUDED.backtest_config,
                total_trades    = EXCLUDED.total_trades,
                win_rate        = EXCLUDED.win_rate,
                net_pnl         = EXCLUDED.net_pnl,
                final_balance   = EXCLUDED.final_balance,
                last_updated    = CURRENT_TIMESTAMP;
            """
            cursor.execute(upsert_sql, (
                strategy_id,
                json.dumps(backtest_config),
                total_trades,
                win_rate,
                net_pnl,
                final_balance,
            ))
            conn.commit()
            logger.info(f"Backtest metadata refreshed for '{strategy_id}': PnL = {net_pnl:.2f}, Win Rate = {win_rate:.2f}%.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating backtest metadata for '{strategy_id}': {error}")
        raise


def fetch_strategy_from_db(conn, strategy_id: str) -> dict:
    """
    Fetches a strategy record from metadata.strategy_data by strategy_id.
    Returns dict: strategy_id, exchange, symbol, target_timeframe, indicators_config, strategy_config.
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT strategy_id, exchange, symbol, target_timeframe, indicators_config, strategy_config "
                "FROM metadata.strategy_data WHERE strategy_id = %s;",
                (strategy_id,)
            )
            row = cursor.fetchone()
            if not row:
                logger.error(f"Strategy '{strategy_id}' not found in metadata.strategy_data.")
                return {}

            ind_cfg = row[4] if isinstance(row[4], dict) else (json.loads(row[4]) if row[4] else {})
            strat_cfg = row[5] if isinstance(row[5], dict) else (json.loads(row[5]) if row[5] else {})

            return {
                "strategy_id": row[0],
                "exchange": row[1],
                "symbol": row[2],
                "target_timeframe": row[3],
                "indicators_config": ind_cfg,
                "strategy_config": strat_cfg,
            }
    except Exception as error:
        logger.error(f"Error fetching strategy '{strategy_id}' from DB: {error}")
        return {}


def list_all_strategies(conn) -> list:
    """Returns a list of all strategy_ids available in metadata.strategy_data."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT strategy_id FROM metadata.strategy_data ORDER BY strategy_id ASC;")
            rows = cursor.fetchall()
            return [r[0] for r in rows]
    except Exception as error:
        logger.error(f"Error listing strategies from DB: {error}")
        return []


def fetch_best_strategy_from_db(conn) -> tuple[str, dict]:
    """Queries simulations.stats for strategy with highest total_pnl and returns its metadata."""
    query = """
    SELECT strategy_id, total_pnl 
    FROM simulations.stats 
    ORDER BY total_pnl DESC 
    LIMIT 1;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()

        if not row:
            raise RuntimeError("No simulation stats found in simulations.stats! Run simulation first.")

        best_id = row[0]
        strat_info = fetch_strategy_from_db(conn, best_id)
        if not strat_info:
            raise RuntimeError(f"Best strategy '{best_id}' metadata not found in metadata.strategy_data!")

        logger.info(f"Top Strategy selected from DB: [{best_id}] | PnL: ${float(row[1]):+,.2f}")
        return best_id, strat_info
    except Exception as error:
        logger.error(f"Error fetching best strategy from DB: {error}")
        raise


# ── SIMULATOR CONFIG DATA ───────────────────────────────────────────────────

def create_simulator_config(conn):
    """Creates metadata.simulator_config table with tabular relational columns referencing serial strategy_id."""
    create_metadata_schema(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'metadata' 
                  AND table_name = 'simulator_config' 
                  AND column_name = 'strategy_id';
            """)
            col_type = cur.fetchone()
            if col_type and col_type[0].lower() in ('character varying', 'text', 'varchar'):
                logger.info("Migrating simulator_config schema: dropping old VARCHAR strategy_id table.")
                cur.execute("DROP TABLE IF EXISTS metadata.simulator_config CASCADE;")
                conn.commit()

            sql = """
            CREATE TABLE IF NOT EXISTS metadata.simulator_config (
                strategy_id         BIGINT PRIMARY KEY,
                enabled             BOOLEAN NOT NULL DEFAULT TRUE,
                initial_balance     NUMERIC(18,8) NOT NULL DEFAULT 10000.0,
                position_size_type  VARCHAR(32) NOT NULL DEFAULT 'fixed_percentage',
                position_size_value NUMERIC(18,8) NOT NULL DEFAULT 10.0,
                commission          NUMERIC(10,6) NOT NULL DEFAULT 0.0005,
                slippage            NUMERIC(10,6) NOT NULL DEFAULT 0.0002,
                allow_long          BOOLEAN NOT NULL DEFAULT TRUE,
                allow_short         BOOLEAN NOT NULL DEFAULT TRUE,
                last_updated        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            cur.execute(sql)
            conn.commit()

            # Auto-populate missing simulator_config rows for all strategies in strategy_data
            cur.execute("""
                INSERT INTO metadata.simulator_config (
                    strategy_id, enabled, initial_balance, position_size_type, position_size_value,
                    commission, slippage, allow_long, allow_short
                )
                SELECT strategy_id, True, 10000.00, 'fixed_percentage', 10.00, 0.0005, 0.0002, True, True
                FROM metadata.strategy_data
                ON CONFLICT (strategy_id) DO NOTHING;
            """)
            conn.commit()
    except Exception as err:
        conn.rollback()
        logger.error(f"Error creating metadata.simulator_config table: {err}")


def upsert_simulator_config(conn, strategy_id: str, config_dict: dict):
    """Upserts tabular simulation configuration for a strategy into metadata.simulator_config."""
    create_simulator_config(conn)
    
    enabled = config_dict.get("enabled", True)
    initial_balance = config_dict.get("initial_balance", 10000.0)
    pos_size = config_dict.get("position_size") or {}
    if isinstance(pos_size, dict):
        position_size_type = pos_size.get("type", config_dict.get("position_size_type", "fixed_percentage"))
        position_size_value = pos_size.get("value", config_dict.get("position_size_value", 10.0))
    else:
        position_size_type = config_dict.get("position_size_type", "fixed_percentage")
        position_size_value = config_dict.get("position_size_value", 10.0)
        
    commission = config_dict.get("commission", config_dict.get("commission_rate", 0.0005))
    slippage = config_dict.get("slippage", config_dict.get("slippage_rate", 0.0002))
    allow_long = config_dict.get("allow_long", True)
    allow_short = config_dict.get("allow_short", True)

    upsert_sql = """
    INSERT INTO metadata.simulator_config (
        strategy_id, enabled, initial_balance, position_size_type, position_size_value,
        commission, slippage, allow_long, allow_short, last_updated
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        enabled             = EXCLUDED.enabled,
        initial_balance     = EXCLUDED.initial_balance,
        position_size_type  = EXCLUDED.position_size_type,
        position_size_value = EXCLUDED.position_size_value,
        commission          = EXCLUDED.commission,
        slippage            = EXCLUDED.slippage,
        allow_long          = EXCLUDED.allow_long,
        allow_short         = EXCLUDED.allow_short,
        last_updated        = CURRENT_TIMESTAMP;
    """
    with conn.cursor() as cur:
        cur.execute(upsert_sql, (
            strategy_id, enabled, initial_balance, position_size_type, position_size_value,
            commission, slippage, allow_long, allow_short
        ))
        conn.commit()
    logger.info(f"Tabular simulator configuration upserted for strategy '{strategy_id}'.")


def fetch_simulator_config(conn, strategy_id: str = None) -> dict:
    """Fetches tabular configuration dictionary from metadata.simulator_config DB table for a strategy."""
    create_simulator_config(conn)
    try:
        with conn.cursor() as cur:
            if strategy_id:
                cur.execute("""
                    SELECT strategy_id, enabled, initial_balance, position_size_type, position_size_value,
                           commission, slippage, allow_long, allow_short
                    FROM metadata.simulator_config WHERE strategy_id = %s;
                """, (strategy_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "strategy_id": row[0],
                        "enabled": row[1],
                        "initial_balance": float(row[2]),
                        "position_size": {"type": row[3], "value": float(row[4])},
                        "commission": float(row[5]),
                        "slippage": float(row[6]),
                        "allow_long": row[7],
                        "allow_short": row[8]
                    }
                # Default fallback config if strategy not found yet in simulator_config
                return {
                    "strategy_id": strategy_id,
                    "enabled": True,
                    "initial_balance": 10000.0,
                    "position_size": {"type": "fixed_percentage", "value": 10.0},
                    "commission": 0.0005,
                    "slippage": 0.0002,
                    "allow_long": True,
                    "allow_short": True
                }
            else:
                cur.execute("""
                    SELECT strategy_id, enabled, initial_balance, position_size_type, position_size_value,
                           commission, slippage, allow_long, allow_short
                    FROM metadata.simulator_config;
                """)
                rows = cur.fetchall()
                result = {}
                for r in rows:
                    result[r[0]] = {
                        "strategy_id": r[0],
                        "enabled": r[1],
                        "initial_balance": float(r[2]),
                        "position_size": {"type": r[3], "value": float(r[4])},
                        "commission": float(r[5]),
                        "slippage": float(r[6]),
                        "allow_long": r[7],
                        "allow_short": r[8]
                    }
                return result
    except Exception as e:
        logger.error(f"Error fetching simulator config from DB: {e}")
        return {}


def create_account_schema_and_tables(conn):
    """Creates the 'account' schema and account.api_creds, account.history, and account.stats tables."""
    sql = """
    CREATE SCHEMA IF NOT EXISTS account;

    CREATE TABLE IF NOT EXISTS account.api_creds (
        exchange        VARCHAR(64) PRIMARY KEY,
        api_key         TEXT NOT NULL,
        api_secret      TEXT NOT NULL,
        demo            BOOLEAN NOT NULL DEFAULT FALSE,
        last_updated    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS account.history (
        id              SERIAL PRIMARY KEY,
        trade_id        VARCHAR(64) NOT NULL,
        strategy_id     VARCHAR(128) NOT NULL,
        symbol          VARCHAR(32) NOT NULL,
        direction       VARCHAR(16) NOT NULL,
        entry_price     NUMERIC NOT NULL,
        exit_price      NUMERIC NOT NULL,
        quantity        NUMERIC NOT NULL,
        gross_pnl       NUMERIC NOT NULL,
        commission      NUMERIC NOT NULL,
        slippage        NUMERIC NOT NULL,
        net_pnl         NUMERIC NOT NULL,
        perc_pnl        NUMERIC NOT NULL,
        exit_reason     VARCHAR(32) NOT NULL,
        balance         NUMERIC NOT NULL,
        entry_time      TIMESTAMP WITH TIME ZONE NOT NULL,
        exit_time       TIMESTAMP WITH TIME ZONE NOT NULL,
        recorded_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_account_history_strat_entry UNIQUE (strategy_id, entry_time)
    );

    CREATE TABLE IF NOT EXISTS account.stats (
        id              SERIAL PRIMARY KEY,
        coin_symbol     VARCHAR(32) NOT NULL UNIQUE,
        initial_balance NUMERIC NOT NULL,
        current_balance NUMERIC NOT NULL,
        no_of_trades    INT NOT NULL DEFAULT 0,
        winning_trades  INT NOT NULL DEFAULT 0,
        losing_trades   INT NOT NULL DEFAULT 0,
        total_pnl       NUMERIC NOT NULL DEFAULT 0.0,
        win_rate        NUMERIC NOT NULL DEFAULT 0.0,
        max_drawdown    NUMERIC DEFAULT 0.0,
        last_updated    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            logger.info("Schema 'account' and tables (api_creds, history, stats) verified/created successfully.")
            
            # Deduplicate existing account.history table and apply constraint
            try:
                cur.execute("""
                    DELETE FROM account.history a
                    USING account.history b
                    WHERE a.ctid > b.ctid 
                      AND a.strategy_id = b.strategy_id 
                      AND a.entry_time = b.entry_time;
                """)
                cur.execute("""
                    ALTER TABLE account.history
                    ADD CONSTRAINT uq_account_history_strat_entry UNIQUE (strategy_id, entry_time);
                """)
                conn.commit()
            except Exception:
                conn.rollback()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating account schema & tables: {e}")
        raise


def upsert_account_api_creds(conn, exchange: str, api_key: str, api_secret: str, demo: bool = False):
    """Upserts API key credentials for an exchange into account.api_creds."""
    create_account_schema_and_tables(conn)
    sql = """
    INSERT INTO account.api_creds (exchange, api_key, api_secret, demo, last_updated)
    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (exchange) DO UPDATE SET
        api_key = EXCLUDED.api_key,
        api_secret = EXCLUDED.api_secret,
        demo = EXCLUDED.demo,
        last_updated = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (exchange.lower().strip(), api_key.strip(), api_secret.strip(), demo))
            conn.commit()
            logger.info(f"API credentials upserted into account.api_creds for exchange '{exchange}'.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting account.api_creds for '{exchange}': {e}")
        raise


def get_exchange_credentials(conn, exchange: str) -> dict:
    """
    Retrieves API key credentials for an exchange strictly from account.api_creds table.
    """
    create_account_schema_and_tables(conn)
    sql_account = "SELECT api_key, api_secret, demo FROM account.api_creds WHERE LOWER(exchange) = %s;"
    try:
        with conn.cursor() as cur:
            cur.execute(sql_account, (exchange.lower().strip(),))
            row = cur.fetchone()
            if row and row[0] and row[1]:
                return {
                    "api_key": row[0].strip(),
                    "api_secret": row[1].strip(),
                    "demo": bool(row[2]) if len(row) > 2 and row[2] is not None else False
                }
    except Exception as e:
        logger.warning(f"Could not query account.api_creds for '{exchange}': {e}")

    return {}




if __name__ == "__main__":
    logger.info("--- Testing All Metadata Schema & Tables ---")
    connection = get_connection()
    try:
        create_metadata_schema(connection)
        create_market_data(connection)
        create_sentiment_data(connection)

        logger.info("--- Manually Upserting All Symbols for Market Data & Sentiment ---")
        symbols = ["btc", "eth", "sol", "ltc", "doge", "mina", "sui", "ada"]
        for sym in symbols:
            upsert_market_data(connection, exchange="binance", symbol=sym, timeframe="1m")
            upsert_market_data(connection, exchange="bybit", symbol=sym, timeframe="1m")
            upsert_sentiment_data(connection, symbol=sym)

        logger.info("--- All Symbols Manually Upserted & Verified Successfully ---")
    finally:
        connection.close()
