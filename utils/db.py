import os
import re
import csv
import json
import datetime
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


def create_ml_backtest_schema_and_table(conn, model_id: str):
    """
    Creates the dedicated 'ml_backtests' schema and model-specific table if they don't exist.
    """
    clean_table_name = str(model_id).lower().replace("-", "_").replace(" ", "_")
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS ml_backtests;"
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS ml_backtests.{clean_table_name} (
        entry_time     TIMESTAMP WITH TIME ZONE PRIMARY KEY,
        direction      VARCHAR(8)    NOT NULL,
        signal         NUMERIC(10,4) NOT NULL,
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
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info(f"Table 'ml_backtests.{clean_table_name}' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating ML backtest table 'ml_backtests.{clean_table_name}': {error}")
        raise


def insert_ml_backtest_ledger(conn, model_id: str, ledger_df: pd.DataFrame):
    """
    Inserts all trade rows from an ML backtest ledger DataFrame into ml_backtests.{model_id}.
    Uses fast tab-separated COPY buffer for maximum performance.
    """
    if ledger_df is None or ledger_df.empty:
        return

    clean_table_name = str(model_id).lower().replace("-", "_").replace(" ", "_")
    create_ml_backtest_schema_and_table(conn, model_id)

    full_table = f"ml_backtests.{clean_table_name}"
    temp_table = f"temp_ml_{clean_table_name}"

    ledger_cols = (
        "entry_time", "direction", "signal", "entry_price", "quantity",
        "take_profit", "stop_loss", "exit_price", "exit_time", "exit_reason",
        "status", "net_pnl", "perc_pnl", "cumulative_pnl", "balance"
    )

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    for idx_val, row in ledger_df.iterrows():
        if "entry_time" in row and pd.notna(row["entry_time"]) and str(row["entry_time"]).strip() not in ("0", ""):
            entry_time = str(row["entry_time"])
        elif "exit_time" in row and pd.notna(row["exit_time"]):
            entry_time = str(row["exit_time"])
        elif isinstance(idx_val, (pd.Timestamp, datetime.datetime)):
            entry_time = idx_val.isoformat()
        else:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            entry_time = (now_utc - datetime.timedelta(minutes=15 * (len(ledger_df) - int(idx_val)))).isoformat()

        exit_time = str(row["exit_time"]) if "exit_time" in row and pd.notna(row["exit_time"]) else entry_time

        writer.writerow([
            entry_time,
            row.get("direction", "LONG"),
            float(row.get("signal", 0.0)) if pd.notna(row.get("signal")) else 0.0,
            row.get("entry_price", 0.0),
            row.get("quantity", 0.0),
            row.get("take_profit", 0.0) if pd.notna(row.get("take_profit")) else 0.0,
            row.get("stop_loss", 0.0) if pd.notna(row.get("stop_loss")) else 0.0,
            row.get("exit_price", 0.0),
            exit_time,
            row.get("exit_reason", "MARKET_EXIT"),
            row.get("status", "CLOSED"),
            row.get("net_pnl", 0.0),
            row.get("perc_pnl", 0.0),
            row.get("cumulative_pnl", 0.0),
            row.get("balance", 0.0),
        ])
    buffer.seek(0)

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table};")
            cursor.execute(f"""
                CREATE TEMP TABLE {temp_table}
                (LIKE {full_table} INCLUDING DEFAULTS) ON COMMIT DROP;
            """)
            copy_sql = f"COPY {temp_table} ({', '.join(ledger_cols)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')"
            cursor.copy_expert(copy_sql, buffer)
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
        logger.info(f"Saved {len(ledger_df)} trade rows to dedicated table '{full_table}' via copy_expert.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting ML backtest ledger into '{full_table}': {error}")
        raise


# ── BACKTEST STATS ────────────────────────────────────────────────────────────

def create_backtest_stats_table(conn):
    """
    Creates the 'backtests.stats' table to store computed performance metrics
    and chart data for each strategy's backtest run.

    Uses 2 dynamic JSONB columns so no schema migration is ever needed:
      - metrics: entire compute_all_metrics() output dict (sharpe, sortino, cagr, ...)
      - charts:  entire all_charts.json from plots.py (equity_curve, drawdown, monthly, ...)

    Status values: 'pending' | 'running' | 'completed' | 'failed'
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS backtests;"
    create_table_sql  = """
    CREATE TABLE IF NOT EXISTS backtests.stats (
        strategy_id   BIGINT PRIMARY KEY
                      REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
        status        VARCHAR(16)               NOT NULL DEFAULT 'pending',
        metrics       JSONB,
        charts        JSONB,
        last_updated  TIMESTAMP WITH TIME ZONE  DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
        conn.commit()
        logger.info("Table 'backtests.stats' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'backtests.stats': {error}")
        raise


def upsert_backtest_stats(conn, strategy_id: int, status: str, metrics: dict = None, charts: dict = None):
    """
    Inserts or updates a row in backtests.stats for a given strategy_id.

    Args:
        strategy_id : int   — FK to metadata.strategy_data
        status      : str   — 'pending' | 'running' | 'completed' | 'failed'
        metrics     : dict  — full output of compute_all_metrics()  (can be None)
        charts      : dict  — full all_charts.json from plots.py    (can be None)

    The JSONB columns store everything dynamically — new metrics/charts from
    future module updates are automatically persisted without any ALTER TABLE.
    """
    create_backtest_stats_table(conn)

    import json as _json

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO backtests.stats (strategy_id, status, metrics, charts, last_updated)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (strategy_id) DO UPDATE SET
                    status       = EXCLUDED.status,
                    metrics      = COALESCE(EXCLUDED.metrics, backtests.stats.metrics),
                    charts       = COALESCE(EXCLUDED.charts,  backtests.stats.charts),
                    last_updated = CURRENT_TIMESTAMP;
            """, (
                strategy_id,
                status,
                _json.dumps(metrics) if metrics else None,
                _json.dumps(charts)  if charts  else None,
            ))
        conn.commit()
        logger.info(f"backtests.stats upserted for strategy_id={strategy_id} → status={status}")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting backtests.stats for strategy_id={strategy_id}: {error}")
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
        charts          JSONB,
        updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            # Defensive alter table to add the charts column if the table already existed
            cursor.execute("ALTER TABLE simulations.stats ADD COLUMN IF NOT EXISTS charts JSONB;")
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
        "charts": None,
    }

    if has_trades:
        # Dynamically compute all QuantStats metrics
        import json
        try:
            from cryptosight.stats.metrices import compute_all_metrics, to_json_safe
            if "perc_pnl" in ledger_df.columns and not ledger_df["perc_pnl"].empty:
                # QuantStats explicitly requires a DatetimeIndex to calculate metrics and plots!
                returns_series = ledger_df.set_index("exit_time")["perc_pnl"]
                returns_series.index = pd.to_datetime(returns_series.index)
                
                raw_metrics = compute_all_metrics(returns_series, is_percentage=False)
                clean_metrics = to_json_safe(raw_metrics)
                for metric_name, val in clean_metrics.items():
                    if isinstance(val, (dict, list)):
                        continue
                    col_key = re.sub(r'[^a-zA-Z0-9_]', '_', metric_name.lower())
                    data_map[col_key] = val
                
                # Generate Charts!
                try:
                    from cryptosight.stats.plots import generate_all_plots
                    plots, master_json_data = generate_all_plots(returns_series, is_percentage=False)
                    data_map["charts"] = json.dumps(master_json_data)
                except Exception as chart_err:
                    logger.warning(f"Could not compute chart plots for strategy '{strategy_name}': {chart_err}")
        except Exception as e:
            logger.warning(f"Could not compute tabular stats metrics for strategy '{strategy_name}': {e}")

    try:
        with conn.cursor() as cursor:
            # Dynamically alter table to add any missing metric columns
            for col, val in data_map.items():
                if col in ("strategy_id", "strategy_name", "exchange", "symbol", "timeframe", "charts"):
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
        try:
            import psycopg2
            is_type_mismatch = isinstance(error, getattr(psycopg2.errors, 'DatatypeMismatch', Exception)) or "datatype" in str(error).lower() or "type mismatch" in str(error).lower()
        except Exception:
            is_type_mismatch = "datatype" in str(error).lower() or "type mismatch" in str(error).lower()

        if is_type_mismatch:
            for col, val in data_map.items():
                logger.error(f"Column '{col}' expected type mismatch: got value {val} of type {type(val)}")
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


def create_execution_active_positions_table(conn):
    """
    Creates the 'execution' schema and 'execution.active_positions' table if they do not exist.
    Tracks live Bybit demo open positions using `strategy_id PRIMARY KEY` to enforce single-position limits.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS execution;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS execution.active_positions (
        strategy_id      BIGINT PRIMARY KEY REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
        strategy_name    VARCHAR(128) NOT NULL,
        exchange         VARCHAR(32) NOT NULL,
        symbol           VARCHAR(32) NOT NULL,
        timeframe        VARCHAR(16) NOT NULL,
        order_id         VARCHAR(128) UNIQUE,
        direction        VARCHAR(16) NOT NULL,
        entry_time       TIMESTAMP WITH TIME ZONE NOT NULL,
        entry_price      NUMERIC(18,8) NOT NULL,
        quantity         NUMERIC(18,8) NOT NULL,
        order_value      NUMERIC(18,8),
        mark_price       NUMERIC(18,8),
        liq_price        NUMERIC(18,8),
        take_profit      NUMERIC(18,8),
        stop_loss        NUMERIC(18,8),
        unrealized_pnl   NUMERIC(18,8),
        status           VARCHAR(32),
        updated_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            cursor.execute("DELETE FROM execution.active_positions WHERE order_id IS NULL OR order_id = '';")
            conn.commit()
            logger.info("Table 'execution.active_positions' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'execution.active_positions': {error}")
        raise


def upsert_execution_active_position(
    conn,
    strategy_id: int,
    strategy_name: str,
    exchange: str,
    symbol: str,
    timeframe: str,
    order_id: str,
    direction: str,
    entry_time,
    entry_price: float,
    quantity: float,
    take_profit: float = None,
    stop_loss: float = None,
    mark_price: float = None,
    liq_price: float = None,
    unrealized_pnl: float = 0.0,
    status: str="OPEN"
):
    """
    Inserts or updates an active open position row in `execution.active_positions`.
    """
    create_execution_active_positions_table(conn)

    order_value = float(entry_price) * float(quantity)
    upsert_sql = """
    INSERT INTO execution.active_positions (
        strategy_id, strategy_name, exchange, symbol, timeframe,
        order_id, direction, entry_time, entry_price, quantity,
        order_value, take_profit, stop_loss, mark_price, liq_price, unrealized_pnl, status, updated_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (strategy_id) DO UPDATE SET
        strategy_name  = EXCLUDED.strategy_name,
        exchange       = EXCLUDED.exchange,
        symbol         = EXCLUDED.symbol,
        timeframe      = EXCLUDED.timeframe,
        order_id       = EXCLUDED.order_id,
        direction      = EXCLUDED.direction,
        entry_time     = EXCLUDED.entry_time,
        entry_price    = EXCLUDED.entry_price,
        quantity       = EXCLUDED.quantity,
        order_value    = EXCLUDED.order_value,
        take_profit    = EXCLUDED.take_profit,
        stop_loss      = EXCLUDED.stop_loss,
        mark_price     = EXCLUDED.mark_price,
        liq_price      = EXCLUDED.liq_price,
        unrealized_pnl = EXCLUDED.unrealized_pnl,
        status         = EXCLUDED.status,
        updated_at     = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(upsert_sql, (
                strategy_id, strategy_name, exchange, symbol, timeframe,
                order_id, direction, entry_time, entry_price, quantity,
                order_value, take_profit, stop_loss, mark_price, liq_price, unrealized_pnl, status
            ))
            conn.commit()
            logger.debug(f"Execution active position updated for strategy '{strategy_name}' (ID #{strategy_id}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error upserting execution active position for strategy #{strategy_id}: {error}")
        raise


def delete_execution_active_position(conn, strategy_id: int):
    """
    Deletes the active position row from `execution.active_positions` when a trade closes.
    """
    create_execution_active_positions_table(conn)
    query = "DELETE FROM execution.active_positions WHERE strategy_id = %s;"
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (strategy_id,))
            conn.commit()
            logger.info(f"Execution active position deleted for strategy #{strategy_id}.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error deleting execution active position for strategy #{strategy_id}: {error}")
        raise


def create_execution_stats_table(conn):
    """
    Creates the 'execution' schema and 'execution.stats' table if they do not exist.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS execution;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS execution.stats (
        strategy_id     BIGINT PRIMARY KEY REFERENCES metadata.strategy_data(strategy_id) ON DELETE CASCADE,
        strategy_name   VARCHAR(128) NOT NULL,
        exchange        VARCHAR(32) NOT NULL,
        symbol          VARCHAR(32) NOT NULL,
        timeframe       VARCHAR(16) NOT NULL,
        total_trades    INTEGER DEFAULT 0,
        winning_trades  INTEGER DEFAULT 0,
        losing_trades   INTEGER DEFAULT 0,
        win_rate        NUMERIC(5,2) DEFAULT 0.0,
        net_pnl         NUMERIC(18,8) DEFAULT 0.0,
        final_balance   NUMERIC(18,8) NOT NULL,
        metrics         JSONB,
        charts          JSONB,
        updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            
            # Defensive alter table to add columns in case the table already existed before the JSONB update
            cursor.execute("ALTER TABLE execution.stats ADD COLUMN IF NOT EXISTS metrics JSONB;")
            cursor.execute("ALTER TABLE execution.stats ADD COLUMN IF NOT EXISTS charts JSONB;")
            
            conn.commit()
            logger.info("Table 'execution.stats' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating table 'execution.stats': {error}")
        raise


def insert_execution_ledger(
    conn,
    strategy_name: str,
    entry_order_id: str,
    exit_order_id: str,
    entry_time,
    exit_time,
    direction: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    gross_pnl: float,
    commission: float,
    net_pnl: float,
    return_pct: float,
    exit_reason: str,
    balance_after: float
):
    """
    Inserts a completed trade record into `execution_ledgers.<strategy_name>`.
    STEP 5 FIX: Stores both entry_order_id and exit_order_id separately.
    Includes post-trade balance (balance_after).
    """
    import re
    clean_strat = re.sub(r'[^a-zA-Z0-9_]+', '_', strategy_name.lower().strip())
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS execution_ledgers;"
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS execution_ledgers.{clean_strat} (
        trade_id        BIGSERIAL PRIMARY KEY,
        entry_order_id  VARCHAR(128),
        exit_order_id   VARCHAR(128) UNIQUE,
        entry_time      TIMESTAMP WITH TIME ZONE NOT NULL,
        exit_time       TIMESTAMP WITH TIME ZONE NOT NULL,
        direction       VARCHAR(16) NOT NULL,
        entry_price     NUMERIC(18,8) NOT NULL,
        exit_price      NUMERIC(18,8) NOT NULL,
        quantity        NUMERIC(18,8) NOT NULL,
        gross_pnl       NUMERIC(18,8) NOT NULL,
        commission      NUMERIC(18,8) DEFAULT 0.0,
        net_pnl         NUMERIC(18,8) NOT NULL,
        return_pct      NUMERIC(18,8) NOT NULL,
        exit_reason     VARCHAR(32) NOT NULL,
        balance_after   NUMERIC(18,8) NOT NULL,
        created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    insert_sql = f"""
    INSERT INTO execution_ledgers.{clean_strat} (
        entry_order_id, exit_order_id, entry_time, exit_time, direction, entry_price, exit_price,
        quantity, gross_pnl, commission, net_pnl, return_pct, exit_reason, balance_after
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            # Defensive column addition if table already exists from older schema
            cursor.execute(f"ALTER TABLE execution_ledgers.{clean_strat} ADD COLUMN IF NOT EXISTS entry_order_id VARCHAR(128);")
            cursor.execute(f"ALTER TABLE execution_ledgers.{clean_strat} ADD COLUMN IF NOT EXISTS exit_order_id VARCHAR(128);")
            cursor.execute(f"ALTER TABLE execution_ledgers.{clean_strat} ADD COLUMN IF NOT EXISTS balance_after NUMERIC(18,8);")
            cursor.execute(insert_sql, (
                entry_order_id, exit_order_id, entry_time, exit_time, direction, entry_price, exit_price,
                quantity, gross_pnl, commission, net_pnl, return_pct, exit_reason, float(balance_after)
            ))
            conn.commit()
            logger.info(f"Closed trade logged to 'execution_ledgers.{clean_strat}' ({exit_reason}, Net PnL=${net_pnl:,.2f}, Balance After=${balance_after:,.2f}).")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error logging closed trade for strategy '{strategy_name}': {error}")
        raise


def upsert_execution_stats(
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
    Inserts or updates live execution performance statistics and dynamic tabular metrics in `execution.stats`.
    """
    import json
    import re
    create_execution_stats_table(conn)

    has_trades = ledger_df is not None and not ledger_df.empty
    total_trades = len(ledger_df) if has_trades else 0
    winning_trades = int((ledger_df["net_pnl"] > 0).sum()) if has_trades else 0
    losing_trades = int((ledger_df["net_pnl"] < 0).sum()) if has_trades else 0
    win_rate = float(winning_trades / total_trades * 100.0) if has_trades and total_trades > 0 else 0.0
    net_pnl = float(ledger_df["net_pnl"].sum()) if has_trades else 0.0
    final_balance = initial_balance + net_pnl

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
        "metrics": None,
        "charts": None,
    }

    if has_trades:
        try:
            from cryptosight.stats.metrices import compute_all_metrics, to_json_safe
            pnl_col = "net_pnl" if "net_pnl" in ledger_df.columns else "gross_pnl"
            if pnl_col in ledger_df.columns and not ledger_df[pnl_col].empty:
                # IMPORTANT: QuantStats explicitly requires the dates to be the INDEX of the series!
                # We must set the 'exit_time' column as the index before passing it.
                returns_series = ledger_df.set_index("exit_time")[pnl_col]
                returns_series.index = pd.to_datetime(returns_series.index)
                
                raw_metrics = compute_all_metrics(returns_series, is_percentage=False)
                clean_metrics = to_json_safe(raw_metrics)
                data_map["metrics"] = json.dumps(clean_metrics)
                
                try:
                    from cryptosight.stats.plots import generate_all_plots
                    plots, master_json_data = generate_all_plots(returns_series, is_percentage=False)
                    data_map["charts"] = json.dumps(master_json_data)
                except Exception as chart_err:
                    logger.warning(f"Could not compute chart metrics for strategy '{strategy_name}': {chart_err}")

        except Exception as e:
            logger.warning(f"Could not compute live execution metrics for strategy '{strategy_name}': {e}")

    try:
        with conn.cursor() as cursor:
            columns = list(data_map.keys())
            values = [data_map[col] for col in columns]

            col_names_str = ", ".join(columns)
            placeholders_str = ", ".join(["%s"] * len(columns))
            update_assignments = [f"{col} = EXCLUDED.{col}" for col in columns if col != "strategy_id"]
            update_str = ", ".join(update_assignments)

            upsert_sql = f"""
            INSERT INTO execution.stats ({col_names_str}, updated_at)
            VALUES ({placeholders_str}, CURRENT_TIMESTAMP)
            ON CONFLICT (strategy_id) DO UPDATE SET
                {update_str},
                updated_at = CURRENT_TIMESTAMP;
            """
            cursor.execute(upsert_sql, tuple(values))
            conn.commit()
            logger.info(f"Live execution stats saved in 'execution.stats' for strategy '{strategy_name}' (ID #{strategy_id}).")
    except Exception as error:
        conn.rollback()
        try:
            import psycopg2
            is_type_mismatch = isinstance(error, getattr(psycopg2.errors, 'DatatypeMismatch', Exception)) or "datatype" in str(error).lower() or "type mismatch" in str(error).lower()
        except Exception:
            is_type_mismatch = "datatype" in str(error).lower() or "type mismatch" in str(error).lower()

        if is_type_mismatch:
            for col, val in data_map.items():
                logger.error(f"Column '{col}' expected type mismatch: got value {val} of type {type(val)}")
        logger.error(f"Error updating 'execution.stats' for strategy #{strategy_id}: {error}")
        raise


def calculate_and_store_stats(conn, strategy_id: int, schema_name: str, table_name: str, target_schema: str = "execution"):
    """
    Queries ledger history from `{schema_name}.{table_name}`, computes QuantStats metrics,
    and updates `{target_schema}.stats` table in PostgreSQL.
    """
    from cryptosight.utils.metadata import fetch_simulator_config, fetch_execution_config
    query_sql = f"SELECT * FROM {schema_name}.{table_name};"
    try:
        df_ledger = pd.read_sql_query(query_sql, conn)
        if df_ledger is not None and not df_ledger.empty:
            if target_schema.lower() == "execution":
                exec_cfg = fetch_execution_config(conn)
                initial_balance = float(exec_cfg["reference_balance"])
            else:
                sim_cfg = fetch_simulator_config(conn)
                initial_balance = float(sim_cfg["initial_balance"])

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT strategy_name, exchange, symbol, timeframe FROM metadata.strategy_data WHERE strategy_id = %s;",
                    (strategy_id,)
                )
                row = cursor.fetchone()
                if row:
                    strat_name, exchange, symbol, timeframe = row[0], row[1], row[2], row[3]
                    if target_schema.lower() == "execution":
                        upsert_execution_stats(
                            conn=conn,
                            strategy_id=strategy_id,
                            strategy_name=strat_name,
                            exchange=exchange,
                            symbol=symbol,
                            timeframe=timeframe,
                            initial_balance=initial_balance,
                            ledger_df=df_ledger,
                        )
                    else:
                        upsert_simulation_stats(
                            conn=conn,
                            strategy_id=strategy_id,
                            strategy_name=strat_name,
                            exchange=exchange,
                            symbol=symbol,
                            timeframe=timeframe,
                            initial_balance=initial_balance,
                            ledger_df=df_ledger,
                        )
    except Exception as err:
        logger.warning(f"Could not calculate and store stats for strategy #{strategy_id}: {err}")


# ── ACCOUNT HISTORY INGESTION (STEP 10) ────────────────────────────────────────

def create_account_history_schema(conn):
    """Creates the 'account_history' schema if it does not exist."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS account_history;")
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating schema 'account_history': {error}")
        raise


def camel_to_snake(name: str) -> str:
    """Converts camelCase or PascalCase strings to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def migrate_account_history_columns(conn):
    """
    Renames existing wrongly-cased columns (e.g. 'closedpnl' -> 'closed_pnl')
    in account_history tables to snake_case using ALTER TABLE ... RENAME COLUMN.
    """
    tables = ["closed_pnl", "executions", "transaction_log"]
    known_folds = {
        "closedpnl": "closed_pnl",
        "avgexitprice": "avg_exit_price",
        "updatedtime": "updated_time",
        "createdtime": "created_time",
        "cumentryvalue": "cum_entry_value",
        "ordertype": "order_type",
        "exectype": "exec_type",
        "closefee": "close_fee",
        "orderid": "order_id",
        "execid": "exec_id",
        "execprice": "exec_price",
        "indexprice": "index_price",
        "execqty": "exec_qty",
        "execvalue": "exec_value",
        "execfee": "exec_fee",
        "feerate": "fee_rate",
        "extrafees": "extra_fees",
        "tradeprice": "trade_price",
        "transactiontime": "transaction_time",
        "ismaker": "is_maker",
    }
    try:
        with conn.cursor() as cursor:
            for tbl in tables:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'account_history' AND table_name = %s;
                """, (tbl,))
                rows = cursor.fetchall()
                if not rows:
                    continue
                existing_cols = [row[0] for row in rows]
                for col in existing_cols:
                    if col == "ingested_at":
                        continue
                    snake_col = camel_to_snake(col)
                    if snake_col == col and "_" not in col:
                        snake_col = known_folds.get(col, col)

                    if snake_col != col and snake_col not in existing_cols:
                        cursor.execute(f'ALTER TABLE account_history.{tbl} RENAME COLUMN "{col}" TO "{snake_col}";')
                        existing_cols.append(snake_col)
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.warning(f"Failed to migrate account_history columns: {error}")


def upsert_account_history_records(conn, table_name: str, records: list, pkey_col: str = "id"):
    """
    Dynamically creates/alters table `account_history.<table_name>` based on keys in `records`,
    normalizing all column names to snake_case, and upserts all records using `pkey_col` as the conflict target.
    """
    if not records:
        return

    create_account_history_schema(conn)
    migrate_account_history_columns(conn)
    full_table = f"account_history.{table_name}"

    pkey_snake = camel_to_snake(pkey_col)
    normalized_records = []
    all_keys = set()
    for r in records:
        norm_r = {camel_to_snake(k): v for k, v in r.items()}
        normalized_records.append(norm_r)
        all_keys.update(norm_r.keys())

    if pkey_snake not in all_keys and normalized_records:
        all_keys.add(pkey_snake)

    columns = list(all_keys)

    try:
        with conn.cursor() as cursor:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {full_table} (
                {pkey_snake} VARCHAR(255) PRIMARY KEY,
                ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_sql)

            for col in columns:
                if col == pkey_snake or col == "ingested_at":
                    continue
                sample_val = next((r[col] for r in normalized_records if r.get(col) is not None), None)
                if isinstance(sample_val, bool):
                    col_type = "BOOLEAN"
                elif isinstance(sample_val, (int, float)):
                    col_type = "NUMERIC(32,8)"
                elif isinstance(sample_val, (dict, list)):
                    col_type = "JSONB"
                else:
                    col_type = "VARCHAR(255)"
                cursor.execute(f"ALTER TABLE {full_table} ADD COLUMN IF NOT EXISTS {col} {col_type};")

            col_names_str = ", ".join(columns)
            placeholders_str = ", ".join(["%s"] * len(columns))
            update_assignments = [f"{col} = EXCLUDED.{col}" for col in columns if col != pkey_snake]
            update_str = ", ".join(update_assignments) if update_assignments else f"{pkey_snake} = EXCLUDED.{pkey_snake}"

            upsert_sql = f"""
            INSERT INTO {full_table} ({col_names_str}, ingested_at)
            VALUES ({placeholders_str}, CURRENT_TIMESTAMP)
            ON CONFLICT ({pkey_snake}) DO UPDATE SET
                {update_str},
                ingested_at = CURRENT_TIMESTAMP;
            """
            for r in normalized_records:
                vals = []
                for c in columns:
                    v = r.get(c)
                    if isinstance(v, (dict, list)):
                        v = json.dumps(v)
                    vals.append(v)
                cursor.execute(upsert_sql, tuple(vals))

            conn.commit()
            logger.info(f"Ingested {len(normalized_records)} records into '{full_table}'.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error ingesting into '{full_table}': {error}")
        raise


def ingest_account_executions(conn, executions: list):
    """Stores raw Bybit executions into account_history.executions."""
    upsert_account_history_records(conn, "executions", executions, pkey_col="execId")


def ingest_account_closed_pnl(conn, closed_pnl_list: list):
    """Stores raw Bybit closed PnL history into account_history.closed_pnl."""
    upsert_account_history_records(conn, "closed_pnl", closed_pnl_list, pkey_col="orderId")


def ingest_account_transaction_log(conn, tx_log_list: list):
    """Stores raw Bybit transaction log into account_history.transaction_log."""
    upsert_account_history_records(conn, "transaction_log", tx_log_list, pkey_col="id")


def create_ingestion_state_table(conn):
    """
    Creates the 'account_history.ingestion_state' table to track last ingested timestamps.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS account_history;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS account_history.ingestion_state (
        id SMALLINT PRIMARY KEY,
        last_executions_time TIMESTAMP WITH TIME ZONE DEFAULT to_timestamp(0),
        last_closed_pnl_time TIMESTAMP WITH TIME ZONE DEFAULT to_timestamp(0),
        last_tx_log_time TIMESTAMP WITH TIME ZONE DEFAULT to_timestamp(0),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            try:
                cursor.execute("ALTER TABLE account_history.ingestion_state ALTER COLUMN last_executions_time TYPE TIMESTAMP WITH TIME ZONE USING to_timestamp(last_executions_time / 1000.0);")
                cursor.execute("ALTER TABLE account_history.ingestion_state ALTER COLUMN last_closed_pnl_time TYPE TIMESTAMP WITH TIME ZONE USING to_timestamp(last_closed_pnl_time / 1000.0);")
                cursor.execute("ALTER TABLE account_history.ingestion_state ALTER COLUMN last_tx_log_time TYPE TIMESTAMP WITH TIME ZONE USING to_timestamp(last_tx_log_time / 1000.0);")
            except Exception:
                conn.rollback() 
            
            cursor.execute(create_table_sql)
            cursor.execute("INSERT INTO account_history.ingestion_state (id) VALUES (1) ON CONFLICT (id) DO NOTHING;")
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating account_history.ingestion_state: {error}")
        raise

def get_ingestion_state(conn) -> dict:
    """Returns the last ingested timestamps as a dict."""
    create_ingestion_state_table(conn)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT extract(epoch from last_executions_time)*1000, extract(epoch from last_closed_pnl_time)*1000, extract(epoch from last_tx_log_time)*1000 FROM account_history.ingestion_state WHERE id = 1;")
            row = cursor.fetchone()
            if row:
                return {
                    "last_executions_time": int(row[0]) if row[0] is not None else 0,
                    "last_closed_pnl_time": int(row[1]) if row[1] is not None else 0,
                    "last_tx_log_time": int(row[2]) if row[2] is not None else 0
                }
    except Exception as error:
        logger.error(f"Error fetching ingestion state: {error}")
    return {}

def update_ingestion_state(conn, **kwargs):
    """Updates specific last_*_time fields."""
    updates = []
    values = []
    for k, v in kwargs.items():
        if k in ("last_executions_time", "last_closed_pnl_time", "last_tx_log_time") and v is not None:
            # Convert epoch-ms integer to PostgreSQL timestamptz (prevents NULL / type-mismatch error)
            updates.append(f"{k} = to_timestamp(%s / 1000.0)")
            values.append(v)
            
    if not updates:
        return
        
    updates.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE account_history.ingestion_state SET {', '.join(updates)} WHERE id = 1;"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(values))
            conn.commit()
    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating ingestion state: {error}")
