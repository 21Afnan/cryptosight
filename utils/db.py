import os
import psycopg2
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
    """Inserts or updates OHLCV data records into the database."""
    if not ohlcv_data:
        return

    schema_name, table_name = get_table_names(exchange, symbol, timeframe)

    upsert_sql = f"""
    INSERT INTO {schema_name}.{table_name} (timestamp, open, high, low, close, volume)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (timestamp) 
    DO UPDATE SET 
        open   = EXCLUDED.open,
        high   = EXCLUDED.high,
        low    = EXCLUDED.low,
        close  = EXCLUDED.close,
        volume = EXCLUDED.volume;
    """
    try:
        with conn.cursor() as cursor:
            cursor.executemany(upsert_sql, ohlcv_data)
            conn.commit()
            logger.info(f"Saved {len(ohlcv_data)} records to '{schema_name}.{table_name}'.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error inserting data into '{schema_name}.{table_name}': {error}")
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
