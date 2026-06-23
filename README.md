# CryptoSight Data Ingestion Pipeline

CryptoSight is a data ingestion pipeline designed to fetch historical and real-time cryptocurrency OHLCV (Open, High, Low, Close, Volume) data from Binance or Bybit and save it directly into a PostgreSQL database. 

It is designed to be fully automatic: it checks the database for existing records and resumes fetching from the latest available timestamp to prevent duplicates.

---

## 📁 Repository Structure

```text
cryptosight/
├── data/
│   ├── binance/
│   │   ├── binance_client_exch.py  # Binance data fetching client
│   │   ├── config.yaml            # Configuration file for Binance symbol ingestion
│   │   └── main.py                # Entry point script to run Binance ingestion
│   └── bybit/
│       ├── bybit_client_exch.py    # Bybit data fetching client
│       ├── config.yaml            # Configuration file for Bybit symbol ingestion
│       └── main.py                # Entry point script to run Bybit ingestion
├── logs/
│   └── app.log                    # Execution logs
├── utils/
│   ├── db_manager.py              # PostgreSQL database manager (tables, connection, upserting data)
│   ├── downloader.py              # Central orchestrator that fetches and saves the data
│   └── logger.py                  # Logger helper
├── .env                           # Environment file for database credentials
├── requirements.txt               # Project dependencies
└── README.md                      # Documentation
```

---

## ⚙️ How It Works (Data Flow)

```mermaid
graph LR
    Main["1. Run main.py"] --> Config["2. Load config.yaml"]
    Config --> Downloader["3. Run utils/downloader.py"]
    Downloader --> DB_Check["4. Check latest timestamp in DB"]
    DB_Check --> API_Fetch["5. Fetch missing data from Exchange API"]
    API_Fetch --> DB_Save["6. Save data to PostgreSQL"]
```

1. **Start**: The user runs the main script for an exchange (e.g. `python data/binance/main.py`).
2. **Config**: The script reads symbols, timeframe, and target dates from the exchange's `config.yaml`.
3. **Database Check**: The pipeline checks the database for the latest stored timestamp to avoid redownloading existing data.
4. **Fetch**: The exchange client fetches missing data from the exchange APIs.
5. **Save**: The database manager inserts the new data into PostgreSQL.

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
- `symbols`: List of symbols to ingest (e.g., `SOL`, `ADA`).
- `timeframe`: Candlestick interval (e.g., `1m`, `5m`, `1h`).
- `start_time`: Time to begin fetching from (e.g., `2026-06-22 00:00:00`).

### 4. Run the Ingestion Pipeline
To ingest data from Binance:
```bash
python data/binance/main.py
```

To ingest data from Bybit:
```bash
python data/bybit/main.py
```

### 5. Check Logs
Pipeline events and errors are recorded in `logs/app.log`.
