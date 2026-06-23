import datetime
from utils.logger import get_logger
from utils.db_manager import get_connection, create_schema_and_table, insert_ohlcv, get_latest_timestamp

# Import exchange clients directly
from data.binance.binance_client_exch import BinanceClient
from data.bybit.bybit_client_exch import BybitClient

logger = get_logger("Downloader")

def download_exchange_data(exchange: str, symbol: str, timeframe: str, start_time: str, end_time: str, max_retries: int, retry_delay: int):
    """
    Downloads historical data from the exchange and saves it directly to the database.
    """
    exchange_name = exchange.lower().strip()
    
    # 1. Select exchange client
    if exchange_name == "binance":
        client = BinanceClient()
    elif exchange_name == "bybit":
        client = BybitClient()
    else:
        raise ValueError(f"Unsupported exchange: {exchange_name}")

    # Standardize symbol format (e.g. BTC to BTC/USDT)
    pair_name = symbol.upper()
    if "/" not in pair_name:
        pair_name = f"{pair_name}/USDT"

    # 2. Connect to PostgreSQL
    conn = get_connection()

    try:
        # Create table if missing
        create_schema_and_table(conn, exchange_name, pair_name, timeframe)

        # Check latest timestamp in DB to resume fetching
        latest_time = get_latest_timestamp(conn, exchange_name, pair_name, timeframe)
        
        if latest_time:
            start_query_time = latest_time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Resuming {pair_name} on {exchange_name.upper()} from: {start_query_time}")
        else:
            start_query_time = start_time
            logger.info(f"Starting {pair_name} fresh on {exchange_name.upper()} from: {start_query_time}")

        # 3. Fetch raw candles from the client
        raw_candles = client.fetch_raw_candles(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_query_time,
            end_time=end_time,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

        if not raw_candles:
            logger.info(f"No new data returned from exchange for {pair_name}.")
            return

        # 4. Format timestamps and filter out already stored records
        final_data = []
        for candle in raw_candles:
            dt_utc = datetime.datetime.fromtimestamp(candle[0] / 1000.0, datetime.timezone.utc)
            # Skip duplicate timestamps that exist in the DB
            if latest_time and dt_utc <= latest_time:
                continue
            final_data.append((dt_utc, candle[1], candle[2], candle[3], candle[4], candle[5]))

        if not final_data:
            logger.info(f"No newer data to save for {pair_name}.")
            return

        # 5. Insert data directly to PostgreSQL
        insert_ohlcv(conn, exchange_name, pair_name, timeframe, final_data)

    except Exception as e:
        logger.error(f"Failed to download data for {pair_name} on {exchange_name.upper()}: {e}")
        raise e
    finally:
        conn.close()
