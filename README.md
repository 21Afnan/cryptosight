# CryptoSight Data Ingestion Pipeline

CryptoSight is a robust data ingestion pipeline designed to fetch historical and real-time cryptocurrency OHLCV (Open, High, Low, Close, Volume) data from Binance or Bybit and save it directly into a PostgreSQL database in a clean, timezone-independent UTC format.

It is designed to be fully automatic: it checks the database for existing records and resumes fetching from the latest available timestamp to prevent duplicates and gaps.

---

## 📁 Repository Structure

```text
cryptosight/
├── data/
│   ├── binance/
│   │   ├── binance_client.py      # Binance data fetching client
│   │   ├── config.yaml            # Configuration file for Binance symbol ingestion
│   │   └── main.py                # Entry point script to run Binance ingestion
│   ├── bybit/
│   │   ├── bybit_client.py        # Bybit data fetching client with forward chunk pagination
│   │   ├── config.yaml            # Configuration file for Bybit symbol ingestion
│   │   └── main.py                # Entry point script to run Bybit ingestion
│   └── downloader.py              # Central orchestrator (processes gaps, filters incomplete candles, handles merging)
├── logs/
│   ├── binance.log                # Execution logs for Binance
│   ├── bybit.log                  # Execution logs for Bybit
│   └── db.log / app.log           # Database and general execution logs
├── utils/
│   ├── config.py                  # YAML config loader and validation utility
│   ├── db.py                      # PostgreSQL connection manager (timezone forced to UTC)
│   └── logger.py                  # Logger helper with rotating file handlers
├── .env                           # Environment file for database credentials (git-ignored)
├── requirements.txt               # Project dependencies
└── README.md                      # Documentation
```

---

## ⚙️ How It Works (Data Flow)

```mermaid
graph LR
    Main["1. Run main.py"] --> Config["2. Load config.yaml"]
    Config --> Downloader["3. Run data/downloader.py"]
    Downloader --> DB_Check["4. Check latest timestamp in DB"]
    DB_Check --> API_Fetch["5. Fetch missing data from Exchange API"]
    API_Fetch --> DB_Save["6. Save data to PostgreSQL"]
```

1. **Start**: The user runs the main script for an exchange (e.g. `python data/binance/main.py`).
2. **Config**: The script reads symbols, timeframe, and target dates from the exchange's `config.yaml` via `utils/config.py`.
3. **Database Check**: The pipeline checks the database for the latest stored timestamp to avoid redownloading existing data.
4. **Fetch**: The exchange client fetches missing data from the exchange APIs.
   - *Bybit Client* uses a forward pagination chunking loop of 1000 candles to ensure complete historical data.
5. **Save**: The database manager inserts the new data into PostgreSQL.
   - Timestamps are stored as `TIMESTAMP` (without timezone) to keep them strictly in UTC, preventing timezone offset conversions (`+05:00`).
   - The active incomplete candle (last row) is dropped before saving to ensure data integrity.

---

## 🚀 Setup & How to Run

### 1. Install Dependencies
Create a virtual environment, activate it, and install the required packages:
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Database Credentials
Create a `.env` file in the root directory (based on your PostgreSQL configuration):
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_username
DB_PASSWORD=your_password
```

### 3. Edit Ingestion Settings
Update the settings in [data/binance/config.yaml](file:///d:/Neurog_Internship/cryptosight/data/binance/config.yaml) or [data/bybit/config.yaml](file:///d:/Neurog_Internship/cryptosight/data/bybit/config.yaml):
- `symbols`: Single string or list of symbols to ingest (e.g., `["BTC", "ADA"]`).
- `timeframe`: Candlestick interval (e.g., `1m`, `5m`, `1h`, `1d`).
- `start_time`: UTC timestamp to begin fetching from (e.g., `"2026-06-22 00:00:00"`).
- `end_time`: Target end time in UTC or `"now"` for real-time fetching.
- `fill_method`: Method to handle missing data gaps inline (e.g., `"ffill"` for forward fill).
- `max_retries` & `retry_delay`: API error retry parameters.

### 4. Run the Ingestion Pipeline
To ingest data from Binance:
```bash
python data/binance/main.py
```

To ingest data from Bybit:
```bash
python data/bybit/main.py
```

---

## 🛠️ Advanced Features

### Ad-hoc Data Merging & Fetching (without DB writes)
If you want to load stored data from PostgreSQL and merge it with live exchange data up to the current timestamp *without* saving new exchange records back to the database, use the `get_data` method on the `Downloader` class:

```python
from cryptosight.data.downloader import Downloader

dl = Downloader(exchange="bybit", symbol="btc", timeframe="1h")

# Loads stored DB candles, fetches missing gap up to 'now' from exchange,
# fills missing values, and returns a merged Pandas DataFrame.
df = dl.get_data(
    start_time="2026-06-22 00:00:00",
    end_time="now",
    max_retries=5,
    retry_delay=3
)
print(df.tail())
```

### Timeframe Resampling
You can easily resample your ingested candlestick data to a higher timeframe (e.g., resampling `1h` data into `4h` candles) using the `resample` method:

```python
from cryptosight.data.downloader import Downloader

dl = Downloader(exchange="binance", symbol="btc", timeframe="1h")

# Returns tuple of (original_df, resampled_df)
original_df, resampled_df = dl.resample(
    target_timeframe="4h",
    start_time="2026-06-22 00:00:00",
    end_time="now",
    max_retries=5,
    retry_delay=3
)
print(resampled_df.tail())
```
