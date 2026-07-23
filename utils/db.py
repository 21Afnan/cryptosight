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
        signal       SMALLINT     NOT NULL DEFAULT 0,
        indicators   JSONB,
        conditions   JSONB
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

    ind_cols = [c for c in df.columns if c.startswith("ind_")]
    cond_cols = [c for c in df.columns if c.startswith("long_cond_") or c.startswith("short_cond_")]

    rows = []
    for ts, row in df.iterrows():
        sig = int(row["signal"]) if "signal" in df.columns else 0

        indicators_payload = None
        if ind_cols:
            ind_dict = {}
            for col in ind_cols:
                val = row[col]
                if pd.notna(val):
                    ind_dict[col] = bool(val) if isinstance(val, (bool, pd.BooleanDtype)) else (val.item() if hasattr(val, 'item') else val)
            indicators_payload = json.dumps(ind_dict) if ind_dict else None

        conditions_payload = None
        if cond_cols:
            cond_dict = {}
            for col in cond_cols:
                val = row[col]
                if pd.notna(val):
                    cond_dict[col] = bool(val) if isinstance(val, (bool, pd.BooleanDtype)) else (val.item() if hasattr(val, 'item') else val)
            conditions_payload = json.dumps(cond_dict) if cond_dict else None

        rows.append((
            ts,
            sig,
            indicators_payload,
            conditions_payload,
        ))

    upsert_sql = f"""
        INSERT INTO {full_table} (timestamp, signal, indicators, conditions)
        VALUES %s
        ON CONFLICT (timestamp) DO UPDATE SET
            signal       = EXCLUDED.signal,
            indicators   = EXCLUDED.indicators,
            conditions   = EXCLUDED.conditions;
    """
    try:
        with conn.cursor() as cursor:
            execute_values(cursor, upsert_sql, rows, page_size=500)
        conn.commit()
        active = sum(1 for r in rows if r[1] != 0)
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



