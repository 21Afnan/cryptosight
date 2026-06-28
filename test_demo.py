import sys
import os
sys.path.insert(0, os.path.abspath(".."))

import pandas as pd
from cryptosight.data.downloader import Downloader

# Set display options so pandas prints nicely
pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 1000)

def test_exchange(exchange_name: str, symbol: str):
    print("=" * 60)
    print(f"TESTING EXCHANGE: {exchange_name.upper()} ({symbol.upper()})")
    print("=" * 60)

    dl = Downloader(exchange=exchange_name, symbol=symbol, timeframe="1m")

    # Fetch last 30 minutes of data up to 'now'
    start_time = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    end_time = "now"

    print(f"\n[1] {exchange_name.upper()} | Testing get_data() (1m candles)...")
    df = dl.get_data(
        start_time=start_time,
        end_time=end_time,
        max_retries=3,
        retry_delay=2
    )

    if not df.empty:
        print(f"\n[SUCCESS] {exchange_name.upper()} get_data() loaded {len(df)} candles!")
        print("\nFirst 3 Candles (1m):")
        print(df.head(3))
        print("\nLast 3 Candles (1m):")
        print(df.tail(3))
    else:
        print(f"\n[FAILED] No data returned for {exchange_name.upper()}.")

    print("\n" + "-" * 60)
    print(f"[2] {exchange_name.upper()} | Testing resample() (Converting 1m -> 5m)...")
    orig_df, resampled_df = dl.resample(
        target_timeframe="5m",
        start_time=start_time,
        end_time=end_time,
        max_retries=3,
        retry_delay=2
    )

    if not resampled_df.empty:
        print(f"\n[SUCCESS] {exchange_name.upper()} resample() converted to {len(resampled_df)} 5m candles!")
        print("\nFirst 3 Resampled Candles (5m):")
        print(resampled_df.head(3))
        print("\nLast 3 Resampled Candles (5m):")
        print(resampled_df.tail(3))
    else:
        print(f"\n[FAILED] No resampled data returned for {exchange_name.upper()}.")
    print("\n")


def main():
    print("#" * 60)
    print("CRYPTOSIGHT MULTI-EXCHANGE TEST DEMO")
    print("#" * 60 + "\n")

    # Test Binance
    test_exchange("binance", "btc")

    # Test Bybit
    test_exchange("bybit", "btc")

    print("#" * 60)
    print("All Exchange Tests Completed!")
    print("#" * 60)

if __name__ == "__main__":
    main()
