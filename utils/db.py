import os
import csv
from io import StringIO
import psycopg2
from psycopg2.errors import UndefinedTable
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from cryptosight.utils.logger import get_logger

logger = get_logger("DBManager")

current_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=current_dir.parent / ".env")


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