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

def generate_strategy_id(exchange: str, symbol: str, target_timeframe: str, indicators_config: dict = None) -> str:
    """
    Generates a deterministic, human-readable strategy_id based on exchange, symbol (coin),
    target_timeframe, and all configured indicators plus their timeperiods.
    Example: 'binance_btc_1h_rsi_14' or 'binance_btc_1h_ema_20_ema_50_rsi_14'
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
    return f"{exchange.lower()}_{symbol.lower()}_{target_timeframe.lower()}{ind_str}"


def create_strategy_data(conn):
    """
    Creates the 'metadata.strategy_data' table to track signal pipeline strategy configurations.
    Uses `strategy_id` (derived from exchange, symbol, target_timeframe, and indicators+periods) as PRIMARY KEY.
    """
    create_metadata_schema(conn)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS metadata.strategy_data (
        strategy_id       VARCHAR(128) PRIMARY KEY,
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
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            conn.commit()
            logger.info("Table 'metadata.strategy_data' verified/created successfully.")
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
):
    """
    Updates or inserts the metadata record for a strategy inside `metadata.strategy_data`.
    Auto-fetches total_rows, long_signals, short_signals, and last_signal_time live
    from the signals table. Uses `strategy_id` as the primary key.
    """
    create_strategy_data(conn)

    strategy_id = generate_strategy_id(exchange, symbol, target_timeframe, indicators_config)
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
                return

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
                strategy_id, exchange, symbol, target_timeframe,
                indicators_config, strategy_config,
                total_rows, long_signals, short_signals,
                last_signal_time, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (strategy_id) DO UPDATE SET
                exchange          = EXCLUDED.exchange,
                symbol            = EXCLUDED.symbol,
                target_timeframe  = EXCLUDED.target_timeframe,
                indicators_config = EXCLUDED.indicators_config,
                strategy_config   = EXCLUDED.strategy_config,
                total_rows        = EXCLUDED.total_rows,
                long_signals      = EXCLUDED.long_signals,
                short_signals     = EXCLUDED.short_signals,
                last_signal_time  = EXCLUDED.last_signal_time,
                last_updated      = CURRENT_TIMESTAMP;
            """
            cursor.execute(upsert_sql, (
                strategy_id, exchange.lower(), symbol.lower(), target_timeframe.lower(),
                json.dumps(indicators_config) if indicators_config else None,
                json.dumps(strategy_config)   if strategy_config   else None,
                total_rows, long_signals, short_signals,
                last_signal_time,
            ))
            conn.commit()
            logger.info(
                f"Strategy metadata refreshed for '{strategy_id}': {total_rows} rows, "
                f"{long_signals} Long / {short_signals} Short signals."
            )
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
