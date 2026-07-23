import os
import re
import csv
import json
from io import StringIO
import psycopg2
from psycopg2.errors import UndefinedTable
from psycopg2.extras import execute_values
import pandas as pd
from pathlib import Path
from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_environment

logger = get_logger("DBManager")

load_environment()


def get_connection():
    """Reads database configurations from env and connects to PostgreSQL."""
    db_host     = os.getenv("DB_HOST")
    db_port     = os.getenv("DB_PORT")
    db_name     = os.getenv("DB_NAME")
    db_user     = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_host, db_name, db_user, db_password]):
        raise ValueError("Missing database configuration in .env")

    try:
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            options="-c timezone=UTC"
        )
        logger.info(f"Connected to database '{db_name}' (UTC).")
        return connection
    except Exception as error:
        logger.error(f"Failed to connect to database: {error}")
        raise


def get_table_names(exchange: str, symbol: str, timeframe: str):
    """Simple public helper to generate standardized schema and table names."""
    schema_name = f"{exchange.lower()}_data"
    table_name  = f"{symbol.lower()}_{timeframe.lower()}"
    return schema_name, table_name


def create_schema_and_table(conn, exchange: str, symbol: str, timeframe: str):
    """Creates PostgreSQL schema and table for a specific market if they don't exist."""
    schema_name, table_name = get_table_names(exchange, symbol, timeframe)

    create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
    create_table_sql  = f"""
    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
        timestamp TIMESTAMP PRIMARY KEY,
        open      NUMERIC NOT NULL,
        high      NUMERIC NOT NULL,
        low       NUMERIC NOT NULL,
        close     NUMERIC NOT NULL,
        volume    NUMERIC NOT NULL
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s",
                (schema_name, table_name)
            )
            table_exists = cursor.fetchone() is not None

            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()

            if table_exists:
                logger.info(f"Table '{schema_name}.{table_name}' verified.")
            else:
                logger.info(f"Table '{schema_name}.{table_name}' created.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating schema/table '{schema_name}.{table_name}': {error}")
        raise


def insert_ohlcv(conn, exchange: str, symbol: str, timeframe: str, ohlcv_data: list):
    """Inserts or updates OHLCV data records into the database using COPY + Temp Table."""
    if not ohlcv_data:
        return

    schema_name, table_name = get_table_names(exchange, symbol, timeframe)
    full_table = f"{schema_name}.{table_name}"
    temp_table = f"temp_{table_name}"

    # 1. Deduplicate incoming batch in Python keeping the last candle per timestamp
    unique_data = {row[0]: row for row in ohlcv_data}
    deduped_data = list(unique_data.values())

    # 2. Convert Python list of tuples into an in-memory TSV string buffer
    #    NaN/NaT -> '' so COPY loads them as real NULL, not the literal text "nan"
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter='\t')
    for row in deduped_data:
        writer.writerow(['' if v != v else v for v in row])  # v != v is True only for NaN
    buffer.seek(0)

    try:
        with conn.cursor() as cursor:
            # 3. Create a temporary staging table (session-local, auto-dropped on commit)
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table};")
            cursor.execute(f"""
                CREATE TEMP TABLE {temp_table} 
                (LIKE {full_table} INCLUDING DEFAULTS) ON COMMIT DROP;
            """)

            # 4. Stream data via COPY into the temp table — one round-trip, not N
            cursor.copy_from(buffer, temp_table, sep='\t', columns=('timestamp', 'open', 'high', 'low', 'close', 'volume'))

            # 5. Bulk upsert from temp table into the real table, handling ON CONFLICT
            cursor.execute(f"""
                INSERT INTO {full_table} (timestamp, open, high, low, close, volume)
                SELECT DISTINCT ON (timestamp) timestamp, open, high, low, close, volume FROM {temp_table}
                ORDER BY timestamp ASC
                ON CONFLICT (timestamp) DO UPDATE SET 
                    open   = EXCLUDED.open,
                    high   = EXCLUDED.high,
                    low    = EXCLUDED.low,
                    close  = EXCLUDED.close,
                    volume = EXCLUDED.volume;
            """)

            conn.commit()
            logger.info(f"Saved {len(ohlcv_data)} records to '{full_table}' via COPY.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting via COPY into '{full_table}': {error}")
        raise


def get_latest_timestamp(conn, exchange: str, symbol: str, timeframe: str):
    """Gets the latest timestamp available for the given market table."""
    schema_name, table_name = get_table_names(exchange, symbol, timeframe)

    table_exists_query = "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s);"
    try:
        with conn.cursor() as cursor:
            cursor.execute(table_exists_query, (schema_name, table_name))
            if not cursor.fetchone()[0]:
                return None

            cursor.execute(f"SELECT MAX(timestamp) FROM {schema_name}.{table_name};")
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as error:
        logger.error(f"Error getting latest timestamp from '{schema_name}.{table_name}': {error}")
        return None


def fetch_ohlcv(conn, exchange: str, symbol: str, timeframe: str, start_time: str, end_time: str) -> pd.DataFrame:
    """
    Ultra-fast vectorized fetch of OHLCV data from PostgreSQL using COPY TO STDOUT.
    Streams C-speed CSV directly into pandas with pre-declared dtypes (skips inference).
    """
    schema_name, table_name = get_table_names(exchange, symbol, timeframe)
    full_table = f"{schema_name}.{table_name}"

    dtype_map = {
        "open": "float64",
        "high": "float64",
        "low": "float64",
        "close": "float64",
        "volume": "float64",
    }

    try:
        with conn.cursor() as cursor:
            subquery = cursor.mogrify(
                f"SELECT timestamp, open, high, low, close, volume FROM {full_table} "
                f"WHERE timestamp >= %s AND timestamp <= %s ORDER BY timestamp ASC",
                (start_time, end_time)
            ).decode("utf-8")
            
            copy_query = f"COPY ({subquery}) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)"
            buffer = StringIO()
            cursor.copy_expert(copy_query, buffer)
            buffer.seek(0)

            df = pd.read_csv(
                buffer,
                dtype=dtype_map,
                parse_dates=["timestamp"],
                index_col="timestamp",
            )

            if not df.empty:
                if df.index.tz is None:
                    df.index = df.index.tz_localize("UTC")
                logger.info(f"Fetched {len(df)} candles from '{full_table}' via fast COPY.")
            return df

    except UndefinedTable:
        logger.warning(f"Table '{full_table}' does not exist.")
        return pd.DataFrame()
    except Exception as error:
        logger.error(f"Error fetching data via COPY from '{full_table}': {error}")
        return pd.DataFrame()


# ── SIGNALS ──────────────────────────────────────────────────────────────────

def get_signals_table_names(exchange: str, symbol: str, target_timeframe: str):
    """Returns standardized schema and table names for the signals schema."""
    schema_name = "signals"
    table_name  = f"{exchange.lower()}_{symbol.lower()}_{target_timeframe.lower()}"
    return schema_name, table_name


def create_signals_schema_and_table(conn, exchange: str, symbol: str, target_timeframe: str):
    """Creates the 'signals' schema and a market-specific signal table if they don't exist."""
    schema_name, table_name = get_signals_table_names(exchange, symbol, target_timeframe)

    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS signals;"
    create_table_sql  = f"""
    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
        timestamp    TIMESTAMP WITH TIME ZONE PRIMARY KEY,
        signal       SMALLINT     NOT NULL DEFAULT 0
    );
    """
    create_index_sql = f"""
    CREATE INDEX IF NOT EXISTS idx_{table_name}_signal
    ON {schema_name}.{table_name} (signal)
    WHERE signal != 0;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s",
                (schema_name, table_name)
            )
            table_exists = cursor.fetchone() is not None

            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            conn.commit()

            if table_exists:
                logger.info(f"Table '{schema_name}.{table_name}' verified.")
            else:
                logger.info(f"Table '{schema_name}.{table_name}' created.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating signals table '{schema_name}.{table_name}': {error}")
        raise


def insert_signals(conn, exchange: str, symbol: str, target_timeframe: str, df: pd.DataFrame):
    """
    Upserts all rows from the signals pipeline DataFrame into signals.{exchange}_{symbol}_{target_timeframe}.
    Automatically packs columns prefixed with 'ind_' into the indicators JSONB column
    and columns prefixed with 'long_cond_' / 'short_cond_' into the conditions JSONB column.
    Uses execute_values for clean handling of JSONB types.
    """
    if df is None or df.empty:
        return

    schema_name, table_name = get_signals_table_names(exchange, symbol, target_timeframe)
    full_table = f"{schema_name}.{table_name}"

    rows = []
    for ts, row in df.iterrows():
        sig = int(row["signal"]) if "signal" in df.columns else 0
        rows.append((
            ts,
            sig,
        ))

    upsert_sql = f"""
        INSERT INTO {full_table} (timestamp, signal)
        VALUES %s
        ON CONFLICT (timestamp) DO UPDATE SET
            signal       = EXCLUDED.signal;
    """
    try:
        with conn.cursor() as cursor:
            execute_values(cursor, upsert_sql, rows, page_size=500)
        conn.commit()
        active = sum(1 for r in rows if r[-1] != 0)
        logger.info(f"Saved {len(rows)} signal rows ({active} active) to '{full_table}'.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting signals into '{full_table}': {error}")
        raise


# ── BACKTESTS ─────────────────────────────────────────────────────────────────

def get_backtest_table_names(exchange: str, symbol: str, timeframe: str, strategy_id: str = None):
    """Returns standardized schema and table names for the backtests schema."""
    schema_name = "backtests"
    if strategy_id:
        table_name = strategy_id.lower()
    else:
        table_name = f"{exchange.lower()}_{symbol.lower()}_{timeframe.lower()}"
    return schema_name, table_name


def create_backtest_schema_and_table(conn, exchange: str, symbol: str, timeframe: str, strategy_id: str = None):
    """Creates the 'backtests' schema and a market/strategy-specific ledger table if they don't exist."""
    schema_name, table_name = get_backtest_table_names(exchange, symbol, timeframe, strategy_id=strategy_id)

    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS backtests;"
    create_table_sql  = f"""
    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
        entry_time     TIMESTAMP WITH TIME ZONE PRIMARY KEY,
        direction      VARCHAR(8)    NOT NULL,
        signal         SMALLINT      NOT NULL,
        entry_price    NUMERIC(18,8) NOT NULL,
        quantity       NUMERIC(18,8) NOT NULL,
        take_profit    NUMERIC(18,8) NOT NULL,
        stop_loss      NUMERIC(18,8) NOT NULL,
        exit_price     NUMERIC(18,8) NOT NULL,
        exit_time      TIMESTAMP WITH TIME ZONE NOT NULL,
        exit_reason    VARCHAR(32)   NOT NULL,
        status         VARCHAR(16)   NOT NULL,
        net_pnl        NUMERIC(18,8) NOT NULL,
        perc_pnl       NUMERIC(10,6) NOT NULL,
        cumulative_pnl NUMERIC(18,8) NOT NULL,
        balance        NUMERIC(18,8) NOT NULL
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s",
                (schema_name, table_name)
            )
            table_exists = cursor.fetchone() is not None

            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()

            if table_exists:
                logger.info(f"Table '{schema_name}.{table_name}' verified.")
            else:
                logger.info(f"Table '{schema_name}.{table_name}' created.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating backtests table '{schema_name}.{table_name}': {error}")
        raise


def insert_backtest_ledger(conn, exchange: str, symbol: str, timeframe: str, ledger_df: pd.DataFrame, strategy_id: str = None):
    """
    Upserts all trade rows from the backtest ledger DataFrame into backtests.{strategy_id or exchange_symbol_timeframe}.
    entry_time (the DataFrame index from run_pipeline) is used as the PRIMARY KEY.
    Uses the same COPY + temp table approach as insert_ohlcv for maximum speed.
    """
    if ledger_df is None or ledger_df.empty:
        return

    schema_name, table_name = get_backtest_table_names(exchange, symbol, timeframe, strategy_id=strategy_id)
    full_table = f"{schema_name}.{table_name}"
    temp_table = f"temp_{table_name}"

    ledger_cols = (
        "entry_time", "direction", "signal", "entry_price", "quantity",
        "take_profit", "stop_loss", "exit_price", "exit_time", "exit_reason",
        "status", "net_pnl", "perc_pnl", "cumulative_pnl", "balance"
    )

    # Build tab-separated buffer — same approach as insert_ohlcv
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    for entry_time, row in ledger_df.iterrows():
        writer.writerow([
            entry_time,
            row["direction"],
            int(row["signal"]),
            row["entry_price"],
            row["quantity"],
            row["take_profit"],
            row["stop_loss"],
            row["exit_price"],
            row["exit_time"],
            row["exit_reason"],
            row["status"],
            row["net_pnl"],
            row["perc_pnl"],
            row["cumulative_pnl"],
            row["balance"],
        ])
    buffer.seek(0)

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table};")
            cursor.execute(f"""
                CREATE TEMP TABLE {temp_table}
                (LIKE {full_table} INCLUDING DEFAULTS) ON COMMIT DROP;
            """)
            cursor.copy_from(buffer, temp_table, sep="\t", columns=ledger_cols)
            cursor.execute(f"""
                INSERT INTO {full_table} ({', '.join(ledger_cols)})
                SELECT DISTINCT ON (entry_time) {', '.join(ledger_cols)} FROM {temp_table}
                ORDER BY entry_time ASC
                ON CONFLICT (entry_time) DO UPDATE SET
                    direction      = EXCLUDED.direction,
                    signal         = EXCLUDED.signal,
                    entry_price    = EXCLUDED.entry_price,
                    quantity       = EXCLUDED.quantity,
                    take_profit    = EXCLUDED.take_profit,
                    stop_loss      = EXCLUDED.stop_loss,
                    exit_price     = EXCLUDED.exit_price,
                    exit_time      = EXCLUDED.exit_time,
                    exit_reason    = EXCLUDED.exit_reason,
                    status         = EXCLUDED.status,
                    net_pnl        = EXCLUDED.net_pnl,
                    perc_pnl       = EXCLUDED.perc_pnl,
                    cumulative_pnl = EXCLUDED.cumulative_pnl,
                    balance        = EXCLUDED.balance;
            """)
        conn.commit()
        logger.info(f"Saved {len(ledger_df)} trade rows to '{full_table}' via COPY.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting backtest ledger into '{full_table}': {error}")
        raise


# ── SIMULATIONS ───────────────────────────────────────────────────────────────

def fetch_signals_from_db(conn, exchange: str, symbol: str, target_timeframe: str) -> pd.DataFrame:
    """
    Fetches pre-computed signals directly from signals.{exchange}_{symbol}_{target_timeframe}.
    Returns a DataFrame indexed by timestamp with a 'signal' column.
    """
    schema_name, table_name = get_signals_table_names(exchange, symbol, target_timeframe)
    full_table = f"{schema_name}.{table_name}"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s);", (schema_name, table_name))
            if not cursor.fetchone()[0]:
                logger.info(f"Signals table '{full_table}' does not exist yet.")
                return pd.DataFrame()

            cursor.execute(f"SELECT timestamp, signal FROM {full_table} ORDER BY timestamp ASC;")
            rows = cursor.fetchall()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["timestamp", "signal"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        logger.info(f"Fetched {len(df)} signal rows from '{full_table}'.")
        return df
    except Exception as error:
        logger.warning(f"Could not fetch signals from '{full_table}': {error}")
        return pd.DataFrame()


def get_sim_table_name(strategy_identifier) -> str:
    """
    Helper to convert strategy_name or strategy_id to a clean PostgreSQL table name under 'simulations' schema.
    Example: 'BTC 1h RSI Mean Reversion' -> 'btc_1h_rsi_mean_reversion'
             1 / '1' -> 'strategy_1'
    """
    s_str = str(strategy_identifier).strip().lower()
    clean_name = re.sub(r'[^a-z0-9_]', '_', s_str)
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    
    if clean_name.isdigit():
        return f"strategy_{clean_name}"
    return clean_name


def create_simulations_schema_and_tables(conn, strategy_id: str):
    """
    Creates the 'simulations' schema, shared positions & stats tables, and strategy-specific ledger table under 'simulation_ledger' schema.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS simulations;"

    create_positions_sql = """
    CREATE TABLE IF NOT EXISTS simulations.positions (
        strategy_id    VARCHAR(128) PRIMARY KEY,
        direction      VARCHAR(8)   NOT NULL,
        entry_time     TIMESTAMP WITH TIME ZONE NOT NULL,
        entry_price    NUMERIC(18,8) NOT NULL,
        quantity       NUMERIC(18,8) NOT NULL,
        take_profit    NUMERIC(18,8) NOT NULL,
        stop_loss      NUMERIC(18,8) NOT NULL,
        current_price  NUMERIC(18,8) NOT NULL,
        unrealized_pnl NUMERIC(18,8) NOT NULL,
        status         VARCHAR(16)   NOT NULL DEFAULT 'Open',
        exit_price     NUMERIC(18,8),
        exit_time      TIMESTAMP WITH TIME ZONE,
        exit_reason    VARCHAR(32),
        last_updated   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_stats_sql = """
    CREATE TABLE IF NOT EXISTS simulations.stats (
        strategy_id     VARCHAR(128) PRIMARY KEY,
        metrics         JSONB,
        initial_balance NUMERIC(18,8) NOT NULL,
        final_balance   NUMERIC(18,8) NOT NULL,
        total_pnl       NUMERIC(18,8) NOT NULL,
        total_trades    INT NOT NULL,
        winning_trades  INT NOT NULL,
        losing_trades   INT NOT NULL,
        win_rate        NUMERIC(5,2) NOT NULL,
        last_updated    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """

    strat_table_name = get_sim_table_name(strategy_id)
    create_ledger_sql = f"""
    CREATE SCHEMA IF NOT EXISTS simulation_ledger;

    CREATE TABLE IF NOT EXISTS simulation_ledger.{strat_table_name} (
        id             SERIAL PRIMARY KEY,
        direction      VARCHAR(8)  NOT NULL,
        entry_time     TIMESTAMP WITH TIME ZONE UNIQUE NOT NULL,
        exit_time      TIMESTAMP WITH TIME ZONE NOT NULL,
        entry_price    NUMERIC(18,8) NOT NULL,
        exit_price     NUMERIC(18,8) NOT NULL,
        quantity       NUMERIC(18,8) NOT NULL,
        gross_pnl      NUMERIC(18,8) NOT NULL,
        commission     NUMERIC(18,8) NOT NULL,
        slippage       NUMERIC(18,8) NOT NULL,
        net_pnl        NUMERIC(18,8) NOT NULL,
        perc_pnl       NUMERIC(10,6) NOT NULL,
        exit_reason    VARCHAR(32)   NOT NULL,
        balance_after  NUMERIC(18,8) NOT NULL
    );
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute("CREATE SCHEMA IF NOT EXISTS simulation_ledger;")
            cursor.execute(create_positions_sql)
            cursor.execute(create_stats_sql)
            cursor.execute(create_ledger_sql)
            conn.commit()
            
            # Clean up orphaned non-numeric strategy_id entries in simulations.positions
            try:
                cursor.execute("DELETE FROM simulations.positions WHERE strategy_id ~ '[^0-9]';")
                conn.commit()
            except Exception:
                conn.rollback()

            # Deduplicate and add unique constraint to existing table if not present
            try:
                cursor.execute(f"""
                    DELETE FROM simulation_ledger.{strat_table_name} a
                    USING simulation_ledger.{strat_table_name} b
                    WHERE a.id > b.id AND a.entry_time = b.entry_time;
                """)
                cursor.execute(f"""
                    ALTER TABLE simulation_ledger.{strat_table_name}
                    ADD CONSTRAINT {strat_table_name}_entry_time_uq UNIQUE (entry_time);
                """)
                conn.commit()
            except Exception:
                conn.rollback()

            logger.info(f"Schema 'simulations' and table 'simulation_ledger.{strat_table_name}' verified/created.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating simulations tables for strategy '{strategy_id}': {error}")
        raise

def clear_simulation_data(conn, strategy_id: str):
    """
    Clears old ledger records and open positions for this strategy so that rerunning the simulator doesn't create duplicate trades.
    """
    strat_table_name = get_sim_table_name(strategy_id)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE simulation_ledger.{strat_table_name};")
            cursor.execute("DELETE FROM simulations.positions WHERE strategy_id = %s;", (str(strategy_id),))
            conn.commit()
            logger.info(f"Cleared old simulation data for '{strategy_id}'.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error clearing old simulation data: {error}")


def save_simulation_position(conn, strategy_id: str, position: dict):
    """
    Saves or updates active open position for a strategy in simulations.positions with status = 'Open'.
    """
    upsert_sql = """
    INSERT INTO simulations.positions (
        strategy_id, direction, entry_time, entry_price, quantity,
        take_profit, stop_loss, current_price, unrealized_pnl, status, last_updated
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Open', CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        direction      = EXCLUDED.direction,
        entry_time     = EXCLUDED.entry_time,
        entry_price    = EXCLUDED.entry_price,
        quantity       = EXCLUDED.quantity,
        take_profit    = EXCLUDED.take_profit,
        stop_loss      = EXCLUDED.stop_loss,
        current_price  = EXCLUDED.current_price,
        unrealized_pnl = EXCLUDED.unrealized_pnl,
        status         = 'Open',
        exit_price     = NULL,
        exit_time      = NULL,
        exit_reason    = NULL,
        last_updated   = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                str(strategy_id),
                position["direction"],
                position["entry_time"],
                position["entry_price"],
                position["quantity"],
                position["take_profit"],
                position["stop_loss"],
                position["current_price"],
                position["unrealized_pnl"],
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error saving position for strategy '{strategy_id}': {error}")


def close_simulation_position(conn, strategy_id: str, exit_data: dict = None):
    """
    Deletes position row from simulations.positions when closed, since completed trades
    are permanently saved in strategy ledger tables. Keeps simulations.positions clean with only ACTIVE open positions.
    """
    delete_sql = "DELETE FROM simulations.positions WHERE strategy_id = %s;"
    try:
        with conn.cursor() as cursor:
            cursor.execute(delete_sql, (str(strategy_id),))
            conn.commit()
            logger.info(f"Position for strategy '{strategy_id}' closed and removed from simulations.positions (saved in ledger).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error removing closed position for strategy '{strategy_id}': {error}")


def insert_simulation_ledger(conn, strategy_id: str, trade: dict):
    """
    Appends a completed trade to strategy-specific table: simulation_ledger.<strategy_id>.
    """
    safe_strat_id = get_sim_table_name(strategy_id)
    strat_table_name = f"simulation_ledger.{safe_strat_id}"
    insert_sql = f"""
    INSERT INTO {strat_table_name} (
        direction, entry_time, exit_time, entry_price, exit_price,
        quantity, gross_pnl, commission, slippage, net_pnl, perc_pnl, exit_reason, balance_after
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (entry_time) DO UPDATE SET
        direction      = EXCLUDED.direction,
        exit_time      = EXCLUDED.exit_time,
        entry_price    = EXCLUDED.entry_price,
        exit_price     = EXCLUDED.exit_price,
        quantity       = EXCLUDED.quantity,
        gross_pnl      = EXCLUDED.gross_pnl,
        commission     = EXCLUDED.commission,
        slippage       = EXCLUDED.slippage,
        net_pnl        = EXCLUDED.net_pnl,
        perc_pnl       = EXCLUDED.perc_pnl,
        exit_reason    = EXCLUDED.exit_reason,
        balance_after  = EXCLUDED.balance_after;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(insert_sql, (
                trade["direction"],
                trade["entry_time"],
                trade["exit_time"],
                trade["entry_price"],
                trade["exit_price"],
                trade["quantity"],
                trade["gross_pnl"],
                trade["commission"],
                trade["slippage"],
                trade["net_pnl"],
                trade["perc_pnl"],
                trade["exit_reason"],
                trade.get("balance_after", trade.get("balance", 0.0)),
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting trade into '{strat_table_name}': {error}")


def upsert_simulation_stats(conn, strategy_id: str, stats_summary: dict, metrics_json: dict = None):
    """
    Upserts overall strategy performance metrics and timestamp into simulations.stats.
    """
    upsert_sql = """
    INSERT INTO simulations.stats (
        strategy_id, metrics, initial_balance, final_balance, total_pnl,
        total_trades, winning_trades, losing_trades, win_rate, last_updated
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        metrics         = EXCLUDED.metrics,
        initial_balance = EXCLUDED.initial_balance,
        final_balance   = EXCLUDED.final_balance,
        total_pnl       = EXCLUDED.total_pnl,
        total_trades    = EXCLUDED.total_trades,
        winning_trades  = EXCLUDED.winning_trades,
        losing_trades   = EXCLUDED.losing_trades,
        win_rate        = EXCLUDED.win_rate,
        last_updated    = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                strategy_id,
                json.dumps(metrics_json) if metrics_json else None,
                stats_summary["initial_balance"],
                stats_summary["final_balance"],
                stats_summary["total_pnl"],
                stats_summary["total_trades"],
                stats_summary["winning_trades"],
                stats_summary["losing_trades"],
                stats_summary["win_rate"],
            ))
            conn.commit()
            logger.info(f"Simulations stats saved to DB for '{strategy_id}'.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error saving simulation stats for strategy '{strategy_id}': {error}")


# ── EXECUTION SCHEMA & TABLES ────────────────────────────────────────────────

def create_execution_schema_and_tables(conn, strategy_id: str, strategy_name: str = None):
    """Creates the 'execution' schema, positions table, strategy ledger table under 'execution_ledger' schema, and stats table."""
    identifier = strategy_name or strategy_id
    strat_table_name = get_sim_table_name(identifier)
    sql = f"""
    CREATE SCHEMA IF NOT EXISTS execution;
    CREATE SCHEMA IF NOT EXISTS execution_ledger;

    CREATE TABLE IF NOT EXISTS execution.positions (
        strategy_id VARCHAR(128) PRIMARY KEY,
        trade_id VARCHAR(64) NOT NULL,
        symbol VARCHAR(32) NOT NULL,
        direction VARCHAR(16) NOT NULL,
        entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
        entry_price NUMERIC NOT NULL,
        quantity NUMERIC NOT NULL,
        take_profit NUMERIC NOT NULL,
        stop_loss NUMERIC NOT NULL,
        current_price NUMERIC NOT NULL,
        unrealized_pnl NUMERIC NOT NULL,
        status VARCHAR(16) DEFAULT 'Open',
        exit_price NUMERIC,
        exit_time TIMESTAMP WITH TIME ZONE,
        exit_reason VARCHAR(32),
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS execution_ledger.{strat_table_name} (
        trade_id VARCHAR(64) PRIMARY KEY,
        entry_time TIMESTAMP WITH TIME ZONE UNIQUE NOT NULL,
        exit_time TIMESTAMP WITH TIME ZONE NOT NULL,
        direction VARCHAR(16) NOT NULL,
        entry_price NUMERIC NOT NULL,
        exit_price NUMERIC NOT NULL,
        quantity NUMERIC NOT NULL,
        gross_pnl NUMERIC NOT NULL,
        commission NUMERIC NOT NULL,
        slippage NUMERIC NOT NULL,
        net_pnl NUMERIC NOT NULL,
        perc_pnl NUMERIC NOT NULL,
        exit_reason VARCHAR(32) NOT NULL,
        balance NUMERIC NOT NULL,
        recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS execution.stats (
        strategy_id VARCHAR(128) PRIMARY KEY,
        initial_balance NUMERIC NOT NULL,
        final_balance NUMERIC NOT NULL,
        total_pnl NUMERIC NOT NULL,
        win_rate NUMERIC NOT NULL,
        total_trades INT NOT NULL,
        winning_trades INT NOT NULL,
        losing_trades INT NOT NULL,
        max_drawdown NUMERIC NOT NULL,
        metrics JSONB NOT NULL,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            
            # Deduplicate and add unique constraint to existing table if not present
            try:
                cur.execute(f"""
                    DELETE FROM execution_ledger.{strat_table_name} a
                    USING execution_ledger.{strat_table_name} b
                    WHERE a.ctid > b.ctid AND a.entry_time = b.entry_time;
                """)
                cur.execute(f"""
                    ALTER TABLE execution_ledger.{strat_table_name}
                    ADD CONSTRAINT {strat_table_name}_entry_time_uq UNIQUE (entry_time);
                """)
                conn.commit()
            except Exception:
                conn.rollback()

            logger.info(f"Execution schema & tables verified/created for '{strategy_id}' (table: execution_ledger.{strat_table_name}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating execution tables for strategy '{strategy_id}': {error}")
        raise


def save_execution_position(conn, strategy_id: str, symbol: str, position: dict):
    """Saves or updates active open position in execution.positions."""
    upsert_sql = """
    INSERT INTO execution.positions (
        strategy_id, trade_id, symbol, direction, entry_time, entry_price, quantity,
        take_profit, stop_loss, current_price, unrealized_pnl, status, last_updated
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        trade_id       = EXCLUDED.trade_id,
        symbol         = EXCLUDED.symbol,
        direction      = EXCLUDED.direction,
        entry_time     = EXCLUDED.entry_time,
        entry_price    = EXCLUDED.entry_price,
        quantity       = EXCLUDED.quantity,
        take_profit    = EXCLUDED.take_profit,
        stop_loss      = EXCLUDED.stop_loss,
        current_price  = EXCLUDED.current_price,
        unrealized_pnl = EXCLUDED.unrealized_pnl,
        status         = EXCLUDED.status,
        exit_price     = NULL,
        exit_time      = NULL,
        exit_reason    = NULL,
        last_updated   = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(upsert_sql, (
                strategy_id,
                position["trade_id"],
                symbol,
                position["direction"],
                position["entry_time"],
                position["entry_price"],
                position["quantity"],
                position["take_profit"],
                position["stop_loss"],
                position["current_price"],
                position["unrealized_pnl"],
                position.get("status", "Open"),
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error saving execution position for '{strategy_id}': {error}")


def close_execution_position(conn, strategy_id: str, exit_data: dict):
    """Updates position status to 'Closed' in execution.positions."""
    update_sql = """
    UPDATE execution.positions SET
        status         = 'Closed',
        current_price  = %s,
        unrealized_pnl = 0.0,
        exit_price     = %s,
        exit_time      = %s,
        exit_reason    = %s,
        last_updated   = CURRENT_TIMESTAMP
    WHERE strategy_id = %s;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(update_sql, (
                exit_data.get("exit_price"),
                exit_data.get("exit_price"),
                exit_data.get("exit_time"),
                exit_data.get("exit_reason"),
                strategy_id,
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error closing execution position for '{strategy_id}': {error}")


def insert_execution_ledger(conn, strategy_id: str, completed_trade: dict, strategy_name: str = None):
    """Inserts completed trade into execution_ledger.<strategy_name> table."""
    identifier = strategy_name or strategy_id
    strat_table_name = get_sim_table_name(identifier)
    insert_sql = f"""
    INSERT INTO execution_ledger.{strat_table_name} (
        trade_id, entry_time, exit_time, direction, entry_price, exit_price,
        quantity, gross_pnl, commission, slippage, net_pnl, perc_pnl, exit_reason, balance
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (entry_time) DO UPDATE SET
        trade_id     = EXCLUDED.trade_id,
        exit_time    = EXCLUDED.exit_time,
        direction    = EXCLUDED.direction,
        entry_price  = EXCLUDED.entry_price,
        exit_price   = EXCLUDED.exit_price,
        quantity     = EXCLUDED.quantity,
        gross_pnl    = EXCLUDED.gross_pnl,
        commission   = EXCLUDED.commission,
        slippage     = EXCLUDED.slippage,
        net_pnl      = EXCLUDED.net_pnl,
        perc_pnl     = EXCLUDED.perc_pnl,
        exit_reason  = EXCLUDED.exit_reason,
        balance      = EXCLUDED.balance,
        recorded_at  = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(insert_sql, (
                completed_trade["trade_id"],
                completed_trade["entry_time"],
                completed_trade["exit_time"],
                completed_trade["direction"],
                completed_trade["entry_price"],
                completed_trade["exit_price"],
                completed_trade["quantity"],
                completed_trade["gross_pnl"],
                completed_trade["commission"],
                completed_trade["slippage"],
                completed_trade["net_pnl"],
                completed_trade["perc_pnl"],
                completed_trade["exit_reason"],
                completed_trade["balance"],
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting execution ledger for '{strategy_id}': {error}")


def upsert_execution_stats(conn, strategy_id: str, initial_balance: float, final_balance: float, completed_trades: list, metrics_dict: dict):
    """Calculates & upserts execution stats into execution.stats."""
    if not completed_trades:
        return

    df_trades = pd.DataFrame(completed_trades)
    total_trades = len(completed_trades)
    winning_trades = len(df_trades[df_trades["net_pnl"] > 0])
    losing_trades = len(df_trades[df_trades["net_pnl"] < 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
    total_pnl = float(df_trades["net_pnl"].sum())
    max_dd = float(metrics_dict.get("max_drawdown", 0.0) or 0.0)

    upsert_sql = """
    INSERT INTO execution.stats (
        strategy_id, initial_balance, final_balance, total_pnl, win_rate,
        total_trades, winning_trades, losing_trades, max_drawdown, metrics, last_updated
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        initial_balance = EXCLUDED.initial_balance,
        final_balance   = EXCLUDED.final_balance,
        total_pnl       = EXCLUDED.total_pnl,
        win_rate        = EXCLUDED.win_rate,
        total_trades    = EXCLUDED.total_trades,
        winning_trades  = EXCLUDED.winning_trades,
        losing_trades   = EXCLUDED.losing_trades,
        max_drawdown    = EXCLUDED.max_drawdown,
        metrics         = EXCLUDED.metrics,
        last_updated    = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(upsert_sql, (
                strategy_id,
                initial_balance,
                final_balance,
                total_pnl,
                win_rate,
                total_trades,
                winning_trades,
                losing_trades,
                max_dd,
                json.dumps(metrics_dict),
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting execution stats for '{strategy_id}': {error}")


def insert_account_history(conn, strategy_id: str, symbol: str, completed_trade: dict):
    """Inserts completed live trade into account.history table."""
    insert_sql = """
    INSERT INTO account.history (
        trade_id, strategy_id, symbol, direction, entry_price, exit_price,
        quantity, gross_pnl, commission, slippage, net_pnl, perc_pnl, exit_reason, balance, entry_time, exit_time
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (strategy_id, entry_time) DO UPDATE SET
        trade_id     = EXCLUDED.trade_id,
        symbol       = EXCLUDED.symbol,
        direction    = EXCLUDED.direction,
        entry_price  = EXCLUDED.entry_price,
        exit_price   = EXCLUDED.exit_price,
        quantity     = EXCLUDED.quantity,
        gross_pnl    = EXCLUDED.gross_pnl,
        commission   = EXCLUDED.commission,
        slippage     = EXCLUDED.slippage,
        net_pnl      = EXCLUDED.net_pnl,
        perc_pnl     = EXCLUDED.perc_pnl,
        exit_reason  = EXCLUDED.exit_reason,
        balance      = EXCLUDED.balance,
        exit_time    = EXCLUDED.exit_time,
        recorded_at  = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(insert_sql, (
                completed_trade["trade_id"],
                strategy_id,
                symbol,
                completed_trade["direction"],
                completed_trade["entry_price"],
                completed_trade["exit_price"],
                completed_trade["quantity"],
                completed_trade["gross_pnl"],
                completed_trade["commission"],
                completed_trade["slippage"],
                completed_trade["net_pnl"],
                completed_trade["perc_pnl"],
                completed_trade["exit_reason"],
                completed_trade["balance"],
                completed_trade["entry_time"],
                completed_trade["exit_time"],
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting into account.history for symbol '{symbol}': {error}")


def upsert_account_stats(conn, coin_symbol: str, initial_balance: float, current_balance: float, completed_trades: list, metrics_dict: dict):
    """Upserts live account performance stats for a coin into account.stats table."""
    total_trades = len(completed_trades)
    if total_trades == 0:
        return

    df_trades = pd.DataFrame(completed_trades)
    winning_trades = len(df_trades[df_trades["net_pnl"] > 0])
    losing_trades = len(df_trades[df_trades["net_pnl"] < 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
    total_pnl = float(df_trades["net_pnl"].sum())
    max_dd = float(metrics_dict.get("max_drawdown", 0.0) or 0.0)

    upsert_sql = """
    INSERT INTO account.stats (
        coin_symbol, initial_balance, current_balance, no_of_trades,
        winning_trades, losing_trades, total_pnl, win_rate, max_drawdown, last_updated
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (coin_symbol) DO UPDATE SET
        initial_balance = EXCLUDED.initial_balance,
        current_balance = EXCLUDED.current_balance,
        no_of_trades    = EXCLUDED.no_of_trades,
        winning_trades  = EXCLUDED.winning_trades,
        losing_trades   = EXCLUDED.losing_trades,
        total_pnl       = EXCLUDED.total_pnl,
        win_rate        = EXCLUDED.win_rate,
        max_drawdown    = EXCLUDED.max_drawdown,
        last_updated    = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(upsert_sql, (
                coin_symbol.upper(),
                initial_balance,
                current_balance,
                total_trades,
                winning_trades,
                losing_trades,
                total_pnl,
                win_rate,
                max_dd,
            ))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting account.stats for symbol '{coin_symbol}': {error}")

