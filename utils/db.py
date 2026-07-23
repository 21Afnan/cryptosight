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
            # Build WHERE clause only for non-None time bounds
            conditions = []
            params = []
            if start_time is not None:
                conditions.append("timestamp >= %s")
                params.append(start_time)
            if end_time is not None:
                conditions.append("timestamp <= %s")
                params.append(end_time)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            raw_sql = f"SELECT timestamp, open, high, low, close, volume FROM {full_table} {where_clause} ORDER BY timestamp ASC"

            subquery = cursor.mogrify(raw_sql, params).decode("utf-8")
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
        conn.rollback()
        logger.warning(f"Table '{full_table}' does not exist.")
        return pd.DataFrame()
    except Exception as error:
        conn.rollback()
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


def create_active_positions_table(conn):
    """
    Creates the 'simulations' schema and 'simulations.active_positions' table.
    Uses `strategy_id` as PRIMARY KEY to guarantee zero duplicacy (max 1 active position per strategy).
    Stores market context (exchange, symbol, timeframe, strategy_name) with every open trade.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS simulations;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS simulations.active_positions (
        strategy_id     BIGINT PRIMARY KEY REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
        strategy_name   VARCHAR(150) NOT NULL,
        exchange        VARCHAR(20)  NOT NULL,
        symbol          VARCHAR(20)  NOT NULL,
        timeframe       VARCHAR(10)  NOT NULL,
        trade_id        VARCHAR(50)  NOT NULL,
        direction       VARCHAR(8)   NOT NULL,
        entry_time      TIMESTAMP WITH TIME ZONE NOT NULL,
        entry_price     NUMERIC(18,8) NOT NULL,
        quantity        NUMERIC(18,8) NOT NULL,
        take_profit     NUMERIC(18,8) NOT NULL,
        stop_loss       NUMERIC(18,8) NOT NULL,
        current_price   NUMERIC(18,8) NOT NULL,
        unrealized_pnl  NUMERIC(18,8) NOT NULL,
        status          VARCHAR(20)  NOT NULL,
        updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Table 'simulations.active_positions' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating 'simulations.active_positions': {error}")
        raise


def upsert_active_position(
    conn,
    strategy_id: int,
    strategy_name: str,
    exchange: str,
    symbol: str,
    timeframe: str,
    trade_id: str,
    direction: str,
    entry_time,
    entry_price: float,
    quantity: float,
    take_profit: float,
    stop_loss: float,
    current_price: float,
    unrealized_pnl: float,
    status: str,
):
    """
    Inserts or updates the single open trade for a strategy in simulations.active_positions.
    """
    upsert_sql = """
    INSERT INTO simulations.active_positions (
        strategy_id, strategy_name, exchange, symbol, timeframe,
        trade_id, direction, entry_time, entry_price, quantity,
        take_profit, stop_loss, current_price, unrealized_pnl, status, updated_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        trade_id       = EXCLUDED.trade_id,
        direction      = EXCLUDED.direction,
        entry_time     = EXCLUDED.entry_time,
        entry_price    = EXCLUDED.entry_price,
        quantity       = EXCLUDED.quantity,
        take_profit    = EXCLUDED.take_profit,
        stop_loss      = EXCLUDED.stop_loss,
        current_price  = EXCLUDED.current_price,
        unrealized_pnl = EXCLUDED.unrealized_pnl,
        status         = EXCLUDED.status,
        updated_at     = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                strategy_id, strategy_name, exchange, symbol, timeframe,
                trade_id, direction, entry_time, entry_price, quantity,
                take_profit, stop_loss, current_price, unrealized_pnl, status
            ))
            conn.commit()
            logger.debug(f"Active position updated for strategy '{strategy_name}' (ID #{strategy_id}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting active position for strategy #{strategy_id}: {error}")
        raise


def delete_active_position(conn, strategy_id: int):
    """Deletes the active position row from simulations.active_positions when a trade closes."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM simulations.active_positions WHERE strategy_id = %s;", (strategy_id,))
            conn.commit()
            logger.info(f"Active position removed for strategy ID #{strategy_id}.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error deleting active position for strategy #{strategy_id}: {error}")
        raise


def fetch_active_position(conn, strategy_id: int) -> dict:
    """Fetches any existing open position for strategy_id from simulations.active_positions."""
    query = """
    SELECT trade_id, direction, entry_time, entry_price, quantity, take_profit, stop_loss, current_price, unrealized_pnl, status
    FROM simulations.active_positions
    WHERE strategy_id = %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (strategy_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "trade_id": str(row[0]),
                    "direction": str(row[1]),
                    "entry_time": row[2],
                    "entry_price": float(row[3]),
                    "quantity": float(row[4]),
                    "take_profit": float(row[5]),
                    "stop_loss": float(row[6]),
                    "current_price": float(row[7]),
                    "unrealized_pnl": float(row[8]),
                    "status": str(row[9]),
                }
    except Exception as error:
        conn.rollback()
        logger.error(f"Error fetching active position for strategy #{strategy_id}: {error}")
    return None


def get_simulation_ledger_table_names(exchange: str, symbol: str, timeframe: str, strategy_name: str = None):
    """Returns standardized schema and table names for simulation_ledgers schema using strategy_name."""
    import re
    schema_name = "simulation_ledgers"
    if strategy_name:
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', str(strategy_name)).lower()
        table_name = re.sub(r'_+', '_', clean_name).strip('_')
    else:
        table_name = f"{exchange.lower()}_{symbol.lower()}_{timeframe.lower()}"
    return schema_name, table_name


def create_simulation_ledger_table(conn, exchange: str, symbol: str, timeframe: str, strategy_name: str = None):
    """Creates the 'simulation_ledgers' schema and strategy-specific ledger table if they don't exist."""
    schema_name, table_name = get_simulation_ledger_table_names(exchange, symbol, timeframe, strategy_name=strategy_name)

    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS simulation_ledgers;"
    create_table_sql  = f"""
    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
        trade_id       VARCHAR(50)   PRIMARY KEY,
        direction      VARCHAR(8)    NOT NULL,
        entry_time     TIMESTAMP WITH TIME ZONE NOT NULL,
        exit_time      TIMESTAMP WITH TIME ZONE NOT NULL,
        entry_price    NUMERIC(18,8) NOT NULL,
        exit_price     NUMERIC(18,8) NOT NULL,
        quantity       NUMERIC(18,8) NOT NULL,
        gross_pnl      NUMERIC(18,8) NOT NULL,
        commission     NUMERIC(18,8) NOT NULL,
        slippage       NUMERIC(18,8) NOT NULL,
        net_pnl        NUMERIC(18,8) NOT NULL,
        perc_pnl       NUMERIC(10,6) NOT NULL,
        exit_reason    VARCHAR(50)   NOT NULL,
        final_balance  NUMERIC(18,8) NOT NULL
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info(f"Table '{schema_name}.{table_name}' verified/created.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating simulation ledger table '{schema_name}.{table_name}': {error}")
        raise


def insert_simulation_ledger(conn, exchange: str, symbol: str, timeframe: str, ledger_df: pd.DataFrame, strategy_name: str = None):
    """
    Inserts completed simulation trades into simulation_ledgers.{strategy_name}.
    Uses COPY + temp table for high performance.
    """
    if ledger_df is None or ledger_df.empty:
        return

    schema_name, table_name = get_simulation_ledger_table_names(exchange, symbol, timeframe, strategy_name=strategy_name)
    create_simulation_ledger_table(conn, exchange, symbol, timeframe, strategy_name=strategy_name)

    full_table = f"{schema_name}.{table_name}"
    temp_table = f"temp_sim_{table_name}"

    ledger_cols = (
        "trade_id", "direction", "entry_time", "exit_time", "entry_price",
        "exit_price", "quantity", "gross_pnl", "commission", "slippage",
        "net_pnl", "perc_pnl", "exit_reason", "final_balance"
    )

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    for idx, row in ledger_df.iterrows():
        writer.writerow([
            row["trade_id"],
            row["direction"],
            row["entry_time"],
            row["exit_time"],
            row["entry_price"],
            row["exit_price"],
            row["quantity"],
            row["gross_pnl"],
            row["commission"],
            row["slippage"],
            row["net_pnl"],
            row["perc_pnl"],
            row["exit_reason"],
            row["final_balance"],
        ])
    buffer.seek(0)

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table};")
            cursor.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {full_table} INCLUDING DEFAULTS) ON COMMIT DROP;")
            cursor.copy_from(buffer, temp_table, sep="\t", columns=ledger_cols)
            cursor.execute(f"""
                INSERT INTO {full_table} ({', '.join(ledger_cols)})
                SELECT DISTINCT ON (trade_id) {', '.join(ledger_cols)} FROM {temp_table}
                ORDER BY trade_id ASC
                ON CONFLICT (trade_id) DO UPDATE SET
                    direction      = EXCLUDED.direction,
                    entry_time     = EXCLUDED.entry_time,
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
                    final_balance  = EXCLUDED.final_balance;
            """)
        conn.commit()
        logger.info(f"Saved {len(ledger_df)} trade rows to simulation ledger '{full_table}'.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting simulation ledger into '{full_table}': {error}")
        raise


def create_simulation_stats_table(conn):
    """
    Creates the 'simulations' schema and 'simulations.stats' table if they do not exist.
    Uses `strategy_id` as PRIMARY KEY to guarantee zero duplicacy per strategy.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS simulations;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS simulations.stats (
        strategy_id     BIGINT PRIMARY KEY REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
        strategy_name   VARCHAR(150) NOT NULL,
        exchange        VARCHAR(20)  NOT NULL,
        symbol          VARCHAR(20)  NOT NULL,
        timeframe       VARCHAR(10)  NOT NULL,
        total_trades    INT,
        winning_trades  INT,
        losing_trades   INT,
        win_rate        NUMERIC(18,8),
        net_pnl         NUMERIC(18,8),
        final_balance   NUMERIC(18,8),
        updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Table 'simulations.stats' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating 'simulations.stats': {error}")
        raise


def upsert_simulation_stats(
    conn,
    strategy_id: int,
    strategy_name: str,
    exchange: str,
    symbol: str,
    timeframe: str,
    initial_balance: float,
    ledger_df: pd.DataFrame = None,
):
    """
    Inserts or updates per-strategy simulation performance statistics and dynamic tabular metrics in `simulations.stats`.
    Dynamically creates PostgreSQL columns for all QuantStats performance metrics.
    """
    import re
    create_simulation_stats_table(conn)

    has_trades = ledger_df is not None and not ledger_df.empty
    total_trades = len(ledger_df) if has_trades else 0
    winning_trades = int((ledger_df["net_pnl"] > 0).sum()) if has_trades else 0
    losing_trades = int((ledger_df["net_pnl"] < 0).sum()) if has_trades else 0
    win_rate = float(winning_trades / total_trades * 100.0) if has_trades and total_trades > 0 else 0.0
    net_pnl = float(ledger_df["net_pnl"].sum()) if has_trades else 0.0
    final_balance = float(ledger_df["final_balance"].iloc[-1]) if has_trades and "final_balance" in ledger_df.columns else initial_balance

    data_map = {
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "exchange": exchange.lower(),
        "symbol": symbol.lower(),
        "timeframe": timeframe.lower(),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "net_pnl": net_pnl,
        "final_balance": final_balance,
    }

    if has_trades:
        # Dynamically compute all QuantStats metrics
        try:
            from cryptosight.stats.metrices import compute_all_metrics, to_json_safe
            if "perc_pnl" in ledger_df.columns and not ledger_df["perc_pnl"].empty:
                raw_metrics = compute_all_metrics(ledger_df["perc_pnl"], is_percentage=False)
                clean_metrics = to_json_safe(raw_metrics)
                for metric_name, val in clean_metrics.items():
                    if isinstance(val, (dict, list)):
                        continue
                    col_key = re.sub(r'[^a-zA-Z0-9_]', '_', metric_name.lower())
                    data_map[col_key] = val
        except Exception as e:
            logger.warning(f"Could not compute tabular stats metrics for strategy '{strategy_name}': {e}")

    try:
        with conn.cursor() as cursor:
            # Dynamically alter table to add any missing metric columns
            for col, val in data_map.items():
                if col in ("strategy_id", "strategy_name", "exchange", "symbol", "timeframe"):
                    continue
                col_type = "NUMERIC(18,8)" if isinstance(val, (int, float)) or val is None else "VARCHAR(255)"
                cursor.execute(f"ALTER TABLE simulations.stats ADD COLUMN IF NOT EXISTS {col} {col_type};")

            columns = list(data_map.keys())
            values = [data_map[col] for col in columns]

            col_names_str = ", ".join(columns)
            placeholders_str = ", ".join(["%s"] * len(columns))
            update_assignments = [f"{col} = EXCLUDED.{col}" for col in columns if col != "strategy_id"]
            update_str = ", ".join(update_assignments)

            upsert_sql = f"""
            INSERT INTO simulations.stats ({col_names_str}, updated_at)
            VALUES ({placeholders_str}, CURRENT_TIMESTAMP)
            ON CONFLICT (strategy_id) DO UPDATE SET
                {update_str},
                updated_at = CURRENT_TIMESTAMP;
            """
            cursor.execute(upsert_sql, tuple(values))
            conn.commit()
            logger.info(f"Simulation stats saved in 'simulations.stats' for strategy '{strategy_name}' (ID #{strategy_id}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating 'simulations.stats' for strategy #{strategy_id}: {error}")
        raise


def create_account_api_table(conn):
    """
    Creates the 'account' schema and 'account.api' table if they do not exist.
    Uses `exchange` as PRIMARY KEY for simple single-account lookup per exchange.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS account;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS account.api (
        exchange    VARCHAR(32) PRIMARY KEY,
        api_key     TEXT NOT NULL,
        api_secret  TEXT NOT NULL,
        demo        BOOLEAN DEFAULT TRUE,
        updated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Table 'account.api' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'account.api': {error}")
        raise


def upsert_account_api(
    conn,
    exchange: str,
    api_key: str,
    api_secret: str,
    demo: bool = True,
):
    """
    Inserts or updates exchange API credentials in `account.api`.
    """
    create_account_api_table(conn)

    upsert_sql = """
    INSERT INTO account.api (
        exchange, api_key, api_secret, demo, updated_at
    )
    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (exchange) DO UPDATE SET
        api_key    = EXCLUDED.api_key,
        api_secret = EXCLUDED.api_secret,
        demo       = EXCLUDED.demo,
        updated_at = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                exchange.lower().strip(),
                api_key.strip(),
                api_secret.strip(),
                demo,
            ))
            conn.commit()
            logger.info(f"API credentials saved to 'account.api' for exchange '{exchange}' (demo={demo}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting API credentials for exchange '{exchange}': {error}")
        raise


def get_account_api(conn, exchange: str) -> dict:
    """
    Fetches API credentials for an exchange from `account.api`.
    """
    create_account_api_table(conn)
    query = """
    SELECT exchange, api_key, api_secret, demo
    FROM account.api
    WHERE exchange = %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (exchange.lower().strip(),))
            row = cursor.fetchone()
            if row:
                return {
                    "exchange": row[0],
                    "api_key": row[1],
                    "api_secret": row[2],
                    "demo": bool(row[3]),
                }
    except Exception as error:
        conn.rollback()
        logger.error(f"Error fetching API credentials for exchange '{exchange}': {error}")
    return None
