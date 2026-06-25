import time
import pandas as pd
from pybit.unified_trading import HTTP
from cryptosight.utils.logger import get_logger

logger = get_logger("BybitClient")

TIMEFRAME_MAP = {
    "1m":  {"interval": "1",   "candle_ms": 1  * 60 * 1000},
    "3m":  {"interval": "3",   "candle_ms": 3  * 60 * 1000},
    "5m":  {"interval": "5",   "candle_ms": 5  * 60 * 1000},
    "15m": {"interval": "15",  "candle_ms": 15 * 60 * 1000},
    "30m": {"interval": "30",  "candle_ms": 30 * 60 * 1000},
    "1h":  {"interval": "60",  "candle_ms": 1  * 60 * 60 * 1000},
    "2h":  {"interval": "120", "candle_ms": 2  * 60 * 60 * 1000},
    "4h":  {"interval": "240", "candle_ms": 4  * 60 * 60 * 1000},
    "6h":  {"interval": "360", "candle_ms": 6  * 60 * 60 * 1000},
    "12h": {"interval": "720", "candle_ms": 12 * 60 * 60 * 1000},
    "1d":  {"interval": "D",   "candle_ms": 24 * 60 * 60 * 1000},
    "1w":  {"interval": "W",   "candle_ms": 7  * 24 * 60 * 60 * 1000},
    "1M":  {"interval": "M",   "candle_ms": 30 * 24 * 60 * 60 * 1000},
}

class BybitClient:

    def __init__(self):
        self.session = HTTP(testnet=False)

    def fetch_candles(
        self,
        symbol:      str,
        timeframe:   str,
        start_time:  str,
        end_time:    str,
        max_retries: int,
        retry_delay: int,
        limit:       int = 1000
    ) -> pd.DataFrame:

        # Validate timeframe before doing anything
        if timeframe not in TIMEFRAME_MAP:
            raise ValueError(
                f"Unsupported timeframe '{timeframe}'. "
                f"Supported: {list(TIMEFRAME_MAP.keys())}"
            )

        # Convert human-readable strings to milliseconds — Bybit only understands ms
        start_ms = int(pd.to_datetime(start_time, format="%Y-%m-%d %H:%M:%S", utc=True).value // 10**6)
        end_ms   = int(pd.Timestamp.now(tz="UTC").value // 10**6) if (not end_time or end_time == "now") \
                   else int(pd.to_datetime(end_time, format="%Y-%m-%d %H:%M:%S", utc=True).value // 10**6)

        # interval  → what Bybit API expects  e.g "1h" → "60"
        # candle_ms → how many ms one candle spans, used for pagination
        interval  = TIMEFRAME_MAP[timeframe]["interval"]
        candle_ms = TIMEFRAME_MAP[timeframe]["candle_ms"]

        bybit_symbol = f"{symbol.upper()}USDT"
        logger.info(f"Fetching {bybit_symbol} | {timeframe} | {start_time} → {end_time}")

        all_candles = []
        current_ms  = start_ms  # cursor — moves forward after every page

        while current_ms < end_ms:

            # End of this page — max `limit` candles or end_ms, whichever is smaller
            page_end_ms = min(current_ms + limit * candle_ms, end_ms)

            retries  = 0
            response = None

            while retries < max_retries:
                try:
                    response = self.session.get_kline(
                        category="linear",
                        symbol=bybit_symbol,
                        interval=interval,
                        start=current_ms,
                        end=page_end_ms,
                        limit=limit
                    )
                    if response.get("retCode") != 0:
                        raise ValueError(f"Bybit API error: {response.get('retMsg')}")
                    break

                except Exception as e:
                    retries += 1
                    logger.warning(f"Attempt {retries}/{max_retries} failed: {e}")
                    if retries < max_retries:
                        time.sleep(retry_delay)  # wait before retrying
                    else:
                        logger.error("Max retries reached. Aborting.")
                        raise

            klines = response.get("result", {}).get("list", [])

            # No data in this window — skip ahead
            if not klines:
                current_ms = page_end_ms + 1
                continue

            klines.reverse()  # Bybit returns newest-first, we need oldest-first

            batch = []
            for k in klines:
                batch.append({
                    "timestamp": int(k[0]),    # string → int
                    "open":      float(k[1]),  # string → float
                    "high":      float(k[2]),
                    "low":       float(k[3]),
                    "close":     float(k[4]),
                    "volume":    float(k[5])   # unit: base coin (e.g BTC)
                })

            all_candles.extend(batch)  # merge this page into full result

            # Advance cursor — +1 to avoid re-fetching the last candle
            last_ts = batch[-1]["timestamp"]
            if last_ts <= current_ms:
                break  # not advancing — safety exit to prevent infinite loop
            current_ms = last_ts + 1

        df = pd.DataFrame(all_candles)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        logger.info(f"Done. Total candles: {len(df)}")
        return df