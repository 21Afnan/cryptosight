import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import get_connection, create_schema_and_table, insert_ohlcv, get_latest_timestamp

# Import exchange clients directly
from cryptosight.data.binance.binance_client_exch import BinanceClient
from cryptosight.data.bybit.bybit_client_exch import BybitClient

logger = get_logger("Downloader")

def download_exchange_data(exchange: str, symbol: str, timeframe: str, start_time: str, end_time: str, max_retries: int, retry_delay: int, fill_method: str):
    """
    Downloads historical data from the exchange, processes gaps and calculates
    volume percentage using pandas, and saves it directly to the database.
    """
    # Supported fill methods
    valid_methods = ["ffill", "interpolate_linear", "interpolate_time"]
    if fill_method not in valid_methods:
        raise ValueError(f"Invalid fill_method '{fill_method}'. Must be one of {valid_methods}")

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
        latest_time_pd = pd.to_datetime(latest_time, utc=True) if latest_time else None
        
        if latest_time_pd:
            start_query_time = latest_time_pd.strftime("%Y-%m-%d %H:%M:%S")
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

        # --- PANDAS PROCESSING ---

        # 1. Convert raw candles list to a pandas DataFrame
        # Each raw candle: [timestamp_ms, open, high, low, close, volume]
        timestamps = [pd.to_datetime(candle[0], unit='ms', utc=True) for candle in raw_candles]
        ohlcv_values = [candle[1:6] for candle in raw_candles]

        df = pd.DataFrame(
            ohlcv_values,
            index=timestamps,
            columns=['open', 'high', 'low', 'close', 'volume']
        ).copy()



        # Log how many missing (NaN) values exist in each column
        missing_counts = df.isnull().sum()
        logger.info(f"Missing (NaN) value counts per column before filling:\n{missing_counts}")

        # 4. Set all NaN volume values to 0.0 first
        df['volume'] = df['volume'].fillna(0.0)

        # 5. Fill missing OHLC values based on fill_method parameter
        if fill_method == "ffill":
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].ffill()
        elif fill_method == "interpolate_linear":
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].interpolate(method='linear')
        elif fill_method == "interpolate_time":
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].interpolate(method='time')

        # 6. Calculate volume_pct column
        total_volume = df['volume'].sum()
        if total_volume > 0.0:
            # Keep as float rounded to 4 decimal places to prevent small values rounding to 0
            df['volume_pct'] = ((df['volume'] / total_volume) * 100.0).round(4)

        else:
            df['volume_pct'] = 0.0

        # 7. Convert final DataFrame back to list of tuples for database insert
        final_data = []
        for ts, row in df.iterrows():
            # Skip duplicate timestamps that exist in the DB
            if latest_time_pd and ts <= latest_time_pd:
                continue
            
            # Append tuple of (timestamp_utc, open, high, low, close, volume, volume_pct)
            final_data.append((
                ts,
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume']),
                float(row['volume_pct'])
            ))

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
