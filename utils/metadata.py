import json
import re
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

def generate_strategy_id(exchange: str, symbol: str, target_timeframe: str, indicators_config: dict = None, strategy_config: dict = None) -> str:
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
                timeframe         VARCHAR(16),
                start_time        TIMESTAMP WITH TIME ZONE,
                end_time          TIMESTAMP WITH TIME ZONE,
                max_retries       INT,
                retry_delay       INT,
                execution_enabled BOOLEAN DEFAULT TRUE,

                indicators_config JSONB,
                strategy_config   JSONB,

                total_rows        BIGINT DEFAULT 0,
                long_signals      BIGINT DEFAULT 0,
                short_signals     BIGINT DEFAULT 0,
                last_signal_time  TIMESTAMP WITH TIME ZONE,

                last_updated      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            alter_sqls = [
                "ALTER TABLE metadata.strategy_data ADD COLUMN IF NOT EXISTS timeframe    VARCHAR(16);",
                "ALTER TABLE metadata.strategy_data ADD COLUMN IF NOT EXISTS start_time   TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE metadata.strategy_data ADD COLUMN IF NOT EXISTS end_time     TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE metadata.strategy_data ADD COLUMN IF NOT EXISTS max_retries  INT;",
                "ALTER TABLE metadata.strategy_data ADD COLUMN IF NOT EXISTS retry_delay  INT;",
                "ALTER TABLE metadata.strategy_data ADD COLUMN IF NOT EXISTS execution_enabled BOOLEAN DEFAULT TRUE;",
            ]
            create_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_strategy_data_lookup
            ON metadata.strategy_data (exchange, symbol, target_timeframe);
            """
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            for alter_sql in alter_sqls:
                cursor.execute(alter_sql)
            conn.commit()

            # Clean up legacy exchange prefixes from strategy_name in metadata.strategy_data
            try:
                cursor.execute("""
                    UPDATE metadata.strategy_data 
                    SET strategy_name = REGEXP_REPLACE(strategy_name, '^(bybit_|binance_)', '', 'i')
                    WHERE strategy_name ~* '^(bybit_|binance_)';
                """)
                conn.commit()
            except Exception as e:
                logger.warning(f"Error cleaning up legacy exchange prefixes from strategy_name: {e}")
                conn.rollback()

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
    timeframe: str = None,
    start_time: str = None,
    end_time: str = None,
    max_retries: int = None,
    retry_delay: int = None,
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
                strategy_name, exchange, symbol, target_timeframe, timeframe, start_time, end_time, max_retries, retry_delay,
                indicators_config, strategy_config,
                total_rows, long_signals, short_signals,
                last_signal_time, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (strategy_name) DO UPDATE SET
                exchange          = EXCLUDED.exchange,
                symbol            = EXCLUDED.symbol,
                target_timeframe  = EXCLUDED.target_timeframe,
                timeframe         = COALESCE(EXCLUDED.timeframe,    metadata.strategy_data.timeframe),
                start_time        = COALESCE(EXCLUDED.start_time,   metadata.strategy_data.start_time),
                end_time          = COALESCE(EXCLUDED.end_time,     metadata.strategy_data.end_time),
                max_retries       = COALESCE(EXCLUDED.max_retries,  metadata.strategy_data.max_retries),
                retry_delay       = COALESCE(EXCLUDED.retry_delay,  metadata.strategy_data.retry_delay),
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
                timeframe.lower() if timeframe else None,
                start_time, end_time,
                max_retries, retry_delay,
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
        strategy_id       BIGINT PRIMARY KEY REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
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


def upsert_backtest_data(conn, strategy_id: int, backtest_config: dict, ledger_df):
    """
    Inserts or updates the summary data of a backtest run in `metadata.backtest_data`.
    Calculates summary stats (total_trades, win_rate, net_pnl, final_balance) on the fly.
    """
    create_backtest_data(conn)

    try:
        total_trades = len(ledger_df)
        if total_trades > 0:
            net_pnl = float(ledger_df["net_pnl"].sum())
            win_rate = float((ledger_df["net_pnl"] > 0).sum() / total_trades * 100)
            final_balance = float(ledger_df["balance"].iloc[-1])
        else:
            net_pnl = 0.0
            win_rate = 0.0
            final_balance = float(backtest_config.get("initial_balance", 10000.0))

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


def create_simulator_config(conn):
    """
    Creates the `metadata.simulator_config` table if it does not exist.
    Stores a single global simulator configuration row in tabular column format.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS metadata;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS metadata.simulator_config (
        config_id            INT PRIMARY KEY DEFAULT 1 CHECK (config_id = 1),
        initial_balance      NUMERIC(18,2) NOT NULL,
        position_size_type   VARCHAR(50) NOT NULL,
        position_size_value  NUMERIC(10,4) NOT NULL,
        commission           NUMERIC(10,6) NOT NULL,
        slippage             NUMERIC(10,6) NOT NULL,
        created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Table 'metadata.simulator_config' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'metadata.simulator_config': {error}")
        raise


def upsert_simulator_config(
    conn,
    initial_balance: float,
    position_size_type: str,
    position_size_value: float,
    commission: float,
    slippage: float,
) -> int:
    """
    Inserts or updates the single global simulator configuration in `metadata.simulator_config`.
    Returns the integer config_id (1).
    """
    create_simulator_config(conn)

    upsert_sql = """
    INSERT INTO metadata.simulator_config (
        config_id, initial_balance, position_size_type,
        position_size_value, commission, slippage, updated_at
    )
    VALUES (1, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (config_id) DO UPDATE SET
        initial_balance     = EXCLUDED.initial_balance,
        position_size_type  = EXCLUDED.position_size_type,
        position_size_value = EXCLUDED.position_size_value,
        commission          = EXCLUDED.commission,
        slippage            = EXCLUDED.slippage,
        updated_at          = CURRENT_TIMESTAMP
    RETURNING config_id;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                initial_balance,
                position_size_type,
                position_size_value,
                commission,
                slippage,
            ))
            config_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Simulator config saved to 'metadata.simulator_config' (ID #{config_id}).")
            return config_id
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting simulator config: {error}")
        raise


def fetch_simulator_config(conn) -> dict:
    """
    Fetches the single global simulator configuration row from `metadata.simulator_config`.
    Returns dict with keys: initial_balance, position_size_type, position_size_value, commission, slippage.
    """
    create_simulator_config(conn)
    query_sql = """
    SELECT initial_balance, position_size_type, position_size_value, commission, slippage
    FROM metadata.simulator_config
    WHERE config_id = 1;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query_sql)
            row = cursor.fetchone()
            if row:
                return {
                    "initial_balance": float(row[0]),
                    "position_size_type": str(row[1]),
                    "position_size_value": float(row[2]),
                    "commission": float(row[3]),
                    "slippage": float(row[4]),
                }
    except Exception as error:
        conn.rollback()
        logger.error(f"Error fetching simulator config: {error}")

    raise RuntimeError("metadata.simulator_config could not be fetched and no config exists — cannot proceed without real config")


def create_simulation_data(conn):
    """
    Creates the `metadata.simulation_data` table if it does not exist.
    Stores simulation configuration parameters per strategy in tabular format.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS metadata;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS metadata.simulation_data (
        strategy_id          BIGINT PRIMARY KEY REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
        strategy_name        VARCHAR(150) NOT NULL,
        exchange             VARCHAR(20)  NOT NULL,
        symbol               VARCHAR(20)  NOT NULL,
        timeframe            VARCHAR(10)  NOT NULL,
        initial_balance      NUMERIC(18,2) NOT NULL,
        position_size_type   VARCHAR(50)  NOT NULL,
        position_size_value  NUMERIC(10,4) NOT NULL,
        commission           NUMERIC(10,6) NOT NULL,
        slippage             NUMERIC(10,6) NOT NULL,
        last_updated         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Table 'metadata.simulation_data' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'metadata.simulation_data': {error}")
        raise


def upsert_simulation_data(
    conn,
    strategy_id: int,
    strategy_name: str,
    exchange: str,
    symbol: str,
    timeframe: str,
    initial_balance: float,
    position_size_type: str,
    position_size_value: float,
    commission: float,
    slippage: float,
):
    """
    Inserts or updates simulation configuration settings per strategy in `metadata.simulation_data`.
    """
    create_simulation_data(conn)

    upsert_sql = """
    INSERT INTO metadata.simulation_data (
        strategy_id, strategy_name, exchange, symbol, timeframe,
        initial_balance, position_size_type, position_size_value,
        commission, slippage, last_updated
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        strategy_name       = EXCLUDED.strategy_name,
        exchange            = EXCLUDED.exchange,
        symbol              = EXCLUDED.symbol,
        timeframe           = EXCLUDED.timeframe,
        initial_balance     = EXCLUDED.initial_balance,
        position_size_type  = EXCLUDED.position_size_type,
        position_size_value = EXCLUDED.position_size_value,
        commission          = EXCLUDED.commission,
        slippage            = EXCLUDED.slippage,
        last_updated        = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                strategy_id, strategy_name, exchange, symbol, timeframe,
                initial_balance, position_size_type, position_size_value,
                commission, slippage
            ))
            conn.commit()
            logger.info(f"Simulation metadata config updated for strategy '{strategy_name}' (ID #{strategy_id}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating simulation metadata for strategy #{strategy_id}: {error}")
        raise


def create_execution_config(conn):
    """
    Creates the `metadata.execution_config` table if it does not exist.
    Stores live/demo execution settings (category='linear'/'spot', order_type='Market'/'Limit').
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS metadata;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS metadata.execution_config (
        config_id         INT PRIMARY KEY DEFAULT 1,
        category          VARCHAR(32) NOT NULL DEFAULT 'linear',
        order_type        VARCHAR(32) NOT NULL DEFAULT 'Market',
        position_size_type VARCHAR(50) NOT NULL,
        position_size_value NUMERIC(10,4) NOT NULL,
        reference_balance NUMERIC(18,2) NOT NULL,
        updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            # Add columns for existing tables
            cursor.execute("ALTER TABLE metadata.execution_config ADD COLUMN IF NOT EXISTS position_size_type VARCHAR(50);")
            cursor.execute("ALTER TABLE metadata.execution_config ADD COLUMN IF NOT EXISTS position_size_value NUMERIC(10,4);")
            cursor.execute("ALTER TABLE metadata.execution_config ADD COLUMN IF NOT EXISTS reference_balance NUMERIC(18,2);")
            conn.commit()
            logger.info("Table 'metadata.execution_config' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'metadata.execution_config': {error}")
        raise


def upsert_execution_config(
    conn,
    position_size_type: str,
    position_size_value: float,
    reference_balance: float,
    category: str = "linear",
    order_type: str = "Market",
) -> dict:
    """
    Inserts or updates execution configuration in `metadata.execution_config`.
    Supports switching category ('linear', 'spot') and order_type ('Market', 'Limit').
    """
    create_execution_config(conn)

    upsert_sql = """
    INSERT INTO metadata.execution_config (
        config_id, category, order_type, position_size_type, position_size_value, reference_balance, updated_at
    )
    VALUES (1, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (config_id) DO UPDATE SET
        category   = EXCLUDED.category,
        order_type = EXCLUDED.order_type,
        position_size_type = EXCLUDED.position_size_type,
        position_size_value = EXCLUDED.position_size_value,
        reference_balance = EXCLUDED.reference_balance,
        updated_at = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                category.lower().strip(), 
                order_type.strip(),
                position_size_type.strip(),
                float(position_size_value),
                float(reference_balance)
            ))
            conn.commit()
            logger.info(f"Execution config saved to 'metadata.execution_config' (category='{category}', order_type='{order_type}').")
            return {
                "category": category, 
                "order_type": order_type,
                "position_size_type": position_size_type,
                "position_size_value": position_size_value,
                "reference_balance": reference_balance
            }
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting execution config: {error}")
        raise


def fetch_execution_config(conn) -> dict:
    """
    Fetches execution settings from `metadata.execution_config`.
    """
    create_execution_config(conn)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT category, order_type, position_size_type, position_size_value, reference_balance FROM metadata.execution_config LIMIT 1;")
            row = cursor.fetchone()
            if row:
                if row[2] is None or row[3] is None or row[4] is None:
                    raise RuntimeError("metadata.execution_config has missing required fields (position_size_type, position_size_value, reference_balance) — cannot proceed without real config")
                return {
                    "category": str(row[0]), 
                    "order_type": str(row[1]),
                    "position_size_type": str(row[2]),
                    "position_size_value": float(row[3]),
                    "reference_balance": float(row[4])
                }
    except Exception as error:
        conn.rollback()
        logger.error(f"Error fetching metadata.execution_config: {error}")
        raise RuntimeError(f"metadata.execution_config could not be fetched and no config exists — cannot proceed without real config: {error}")
    
    raise RuntimeError("metadata.execution_config could not be fetched and no config exists — cannot proceed without real config")




