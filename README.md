<div id="top"></div>
<div align="center">

# 🚀 CryptoSight: Enterprise Quantitative Data, Algorithmic Engine & Trading Terminal

[![Built by Afnan Shoukat](https://img.shields.io/badge/Built%20by-Afnan%20Shoukat-00E676?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/afnanshoukat)
[![GitHub Profile](https://img.shields.io/badge/GitHub-21Afnan-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/21Afnan)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18%2B%20Dashboard-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Enterprise%20Storage-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![TA-Lib](https://img.shields.io/badge/TA--Lib-158%20Indicators-FF6F00?style=for-the-badge)](https://ta-lib.org)

**An institutional, production-grade cryptocurrency data ingestion, dynamic technical analysis, NLP sentiment classification, ML feature engineering, vectorized backtesting, FastAPI REST backend services, and interactive React trading dashboard.**

[🌟 Key Pillars](#features) • [🏗️ System Flowchart](#flowchart) • [📊 Status: Done vs Left](#status) • [⚡ Quick Start Guide](#quickstart) • [📁 Repository Structure](#structure) • [👨‍💻 Author](#author)

</div>

---

<div id="features"></div>

## 🌟 Executive Summary & 10 Quantitative Pillars

**CryptoSight** bridges the gap between raw exchange data feeds and institutional quantitative strategies. It eliminates boilerplate data cleaning, API pagination headaches, and indicator mapping complexities by providing an end-to-end automated framework organized into **10 Quantitative Pillars**:

| Status | Pillar | Module | High-Level Institutional Functionality |
| :---: | :--- | :--- | :--- |
| 🟢 **COMPLETED** | **1. Ingestion** | `cryptosight.data` | **Binance & Bybit Ingestion** with smart SQL gap-fill, COPY binary streams, and live candle stripping (`latest_ts` synchronization). |
| 🟢 **COMPLETED** | **2. TA Engine** | `cryptosight.tal_Indicators` | **Dynamic 158 TA-Lib Wrapper** utilizing Python `__getattr__` interception with parameter hierarchy & Plotly visual rendering. |
| 🟢 **COMPLETED** | **3. Signals** | `cryptosight.signals` | **YAML-Driven Signal Pipeline** with multi-crossover conditions and automatic `.shift(1)` look-ahead bias prevention. |
| 🟢 **COMPLETED** | **4. Simulator Engine**| `cryptosight.simulator` | **Event-Driven Simulation Engine** maintaining live active positions (`simulations.active_positions`), trade ledgers (`simulation_ledgers`), and dynamic performance metrics (`simulations.stats`). |
| 🟢 **COMPLETED** | **5. Backtester** | `cryptosight.backtesting` | **Vectorized 10-Step Backtesting Engine** simulating realistic commissions (`0.05%`), slippage (`0.02%`), dynamic TP/SL, and SQL ledger exports. |
| 🟢 **COMPLETED** | **6. Sentiment** | `cryptosight.sentiment` | **Reddit NLP Pipeline** with PRAW scraping, text cleaning, and **Hugging Face FinBERT** chunk-averaged classification. |
| 🟢 **COMPLETED** | **7. ML Ecosystem** | `cryptosight.ml` | **Quant ML Engine** with lag-free feature extraction (`.shift(1)`), stationarity scaling, XGBoost/LightGBM/LSTM models, and out-of-sample forward inference. |
| 🟢 **COMPLETED** | **8. Analytics** | `cryptosight.stats` | **Institutional QuantStats Suite** computing 59+ financial performance ratios (`CAGR, Sharpe, Sortino, Calmar`) embedded as dynamic PostgreSQL tabular columns. |
| 🟢 **COMPLETED** | **9. Terminal Platform** | `cryptosight.backend` & `frontend` | **FastAPI REST API & React Dashboard** with live PostgreSQL trade ledger chart generation (`generate_charts_from_trades`), topbar health polling (`● DB Active`), interactive Up/Down table header sorting, and soft eye-friendly red design system. |
| 🟢 **COMPLETED** | **10. Live Execution** | `cryptosight.execution` | **Automated Bybit Live Execution Engine** managing live positions (`execution.active_positions`), strategy ledgers (`execution_ledgers`), exchange history sync (`account_history.*`), TP/SL/Reversal reconciliation, and real-time execution stats (`execution.stats` & `account.stats`). |

> [!IMPORTANT]
> **Zero Data Leakage Guarantee (`.shift(1)`)**: Every single technical indicator, moving average, and pattern calculated inside CryptoSight is explicitly shifted forward by 1 period (`Bar T -> Bar T+1`) before generating target labels or execution signals. This mathematically prevents future look-ahead bias during historical backtests and ML cross-validation.

> [!NOTE]
> **Strict Financial Data Governance & Zero Fake Data Policy**: All backend services (including `wallet_service.py`) operate under a strict zero-fabricated-data policy. If live exchange APIs or database analytics are unavailable, financial endpoints issue explicit `*_unavailable` boolean flags (`balance_unavailable`, `pnl_unavailable`, `equity_curve_unavailable`) and structured warning logs rather than returning hardcoded fallbacks.

<div align="right"><a href="#top">⬆️ Back to Top</a></div>

---

<div id="flowchart"></div>

## 🏗️ System Architecture & Full-Stack Pipeline Flowchart

```mermaid
graph TD
    subgraph Data_Ingestion["Data Ingestion Layer"]
        API["Exchange APIs - Binance & Bybit"] -->|"Fetch Historical & Live Price Data"| Fetcher["Exchange Downloaders"]
        Fetcher -->|"Clean & Organize OHLCV"| Facade["Master Data Downloader"]
        Reddit["Reddit API - PRAW Client"] -->|"Scrape Posts & Comments"| RedditScraper["Reddit Scraper & Saver"]
    end

    subgraph Database_Layer["PostgreSQL Database & Storage Layer"]
        Facade -->|"Check Last Saved Candle Date"| SQL_Check["PostgreSQL Database"]
        SQL_Check -->|"Download Only Missing Gap"| Facade
        Facade -->|"Fast Bulk Save via COPY Stream"| SQL_Check
        
        RedditScraper -->|"Save Raw Posts & Comments"| SQL_Check
        SQL_Check -->|"Fetch Unprocessed Raw Posts"| AI_Sentiment["AI Sentiment Pipeline FinBERT"]
        AI_Sentiment -->|"Save Bullish/Bearish Scores"| SQL_Check
    end

    subgraph Indicators_Layer["Indicators & Charting Layer"]
        SQL_Check -->|"Load Price Candles"| Engine["158 Technical Indicators Engine TA-Lib Wrapper"]
        Engine -->|"Render Interactive Visuals"| Dashboard["Dark Mode Web Charts Plotly"]
    end

    subgraph Signals_Layer["Trading Signals Layer"]
        Engine -->|"Apply Crossover Rules"| Signals["Trading Signal Generator YAML Rules"]
        Signals -->|"Store Pre-Computed Signals"| SQL_Signals["signals Schema"]
    end

    subgraph Simulation_Layer["Event-Driven Simulator & Backtesting Engine"]
        SQL_Check -->|"Load 1m Base Candles"| Simulator["Event-Driven Simulator Engine"]
        Signals -->|"Feed Target Signals"| Simulator
        Simulator -->|"Track Live Trades"| ActivePos["simulations.active_positions"]
        Simulator -->|"Stream Trade Logs"| Ledgers["simulation_ledgers Schema"]
        Simulator -->|"Dynamic QuantStats Metrics"| StatsTable["simulations.stats Table"]
        
        SQL_Check -->|"Load Price Candles"| Backtester["Vectorized 10-Step Backtester"]
        Backtester -->|"Export Trade Ledgers"| SQL_Backtests["backtests Schema"]
        Backtester -->|"Update Summary Stats"| SQL_BacktestData["metadata.backtest_data Table"]
    end

    subgraph Execution_Engine_Layer["Bybit Automated Live Execution Engine"]
        Signals -->|"Poll Strategy Signals"| ExecEngine["Live Execution Engine (engine.py)"]
        ExecEngine -->|"Place Orders / Manage Positions"| BybitAPI["Bybit UTA V5 REST API"]
        BybitAPI -->|"Track Open Trades"| LivePos["execution.active_positions"]
        BybitAPI -->|"Sync History"| AccHist["account_history Schema (executions, closed_pnl, transaction_log)"]
        ExecEngine -->|"Reconcile & Log Completed Trades"| ExecLedgers["execution_ledgers Schema"]
        ExecEngine -->|"Compute Live Performance Metrics"| ExecStats["execution.stats & account.stats"]
    end

    subgraph Backend_Services_Layer["FastAPI REST API Services Layer"]
        SQL_Check -->|"Query Strategies & Stats"| FastAPI["FastAPI Service Layer (backtest_service.py DB queries & chart calculation)"]
        SQL_Backtests -->|"Fetch Real Trade Ledgers"| FastAPI
        FastAPI -->|"Dynamic Chart Calculations (generate_charts_from_trades)"| API_Routes["REST Router (/api/v1/backtests)"]
    end

    subgraph Frontend_Dashboard_Layer["React 18 Trading Dashboard"]
        API_Routes -->|"Stream JSON Payloads"| ReactApp["Vite + React 18 Dashboard"]
        ReactApp -->|"Render Equity & Drawdown Curves"| LightweightCharts["Lightweight Charts v5 & Recharts"]
        ReactApp -->|"Interactive Up/Down Sorting"| TradeLedgerTable["Trade Execution Ledger Table"]
        ReactApp -->|"Poll DB Health (15s)"| DBStatusChip["● DB Active Topbar Pill"]
    end
```

<div align="right"><a href="#top">⬆️ Back to Top</a></div>

---

<div id="status"></div>

## 📊 Deep Feature Breakdown: What is DONE vs What is LEFT

### 🟢 **What is DONE (Fully Implemented)**

#### 1. Backend Core & Quantitative Engines
- **Data Ingestion Engine (`cryptosight.data`)**:
  - Binance and Bybit historical & live candle downloader.
  - PostgreSQL binary COPY streaming (`copy_expert`) for ultra-fast bulk writes.
  - Automatic OHLCV gap-filling based on `latest_ts` in PostgreSQL.
  - Live candle stripping to eliminate incomplete bar look-ahead bias.
  - Multi-timeframe OHLCV resampling (1m, 5m, 15m, 1h, 4h, 1d).
- **Technical Analysis Engine (`cryptosight.tal_Indicators`)**:
  - Dynamic Python `__getattr__` wrapper covering all **158 TA-Lib indicators**.
  - Parameter hierarchy fallbacks (Custom Config $\to$ Defaults).
  - Plotly indicator overlay generation.
- **Quant Signal Generator (`cryptosight.signals`)**:
  - YAML rule definition engine (`strategy_config.yaml`).
  - Multi-indicator crossover conditions (e.g. EMA cross, RSI boundaries, MACD histograms).
  - Mandatory `.shift(1)` look-ahead bias protection across all signals.
- **Event-Driven Simulator (`cryptosight.simulator`)**:
  - Bar-by-bar execution simulator on 1m price feeds.
  - Dynamic active position tracking in `simulations.active_positions`.
  - Detailed trade log record keeping in `simulation_ledgers`.
  - Performance statistics aggregation in `simulations.stats`.
- **Vectorized Backtesting Engine (`cryptosight.backtesting`)**:
  - 10-step vectorized backtest execution engine.
  - Models realistic taker/maker commissions (0.05%), slippage (0.02%), stop-loss, take-profit, trailing stops.
  - Exports full strategy trade ledgers to `backtests.<strategy_slug>` tables.
  - Populates strategy metadata in `metadata.backtest_data` & `backtests.stats`.
- **NLP Sentiment Classification (`cryptosight.sentiment`)**:
  - Reddit PRAW API scraper for crypto subreddits.
  - Text normalization & cleaning pipeline.
  - **Hugging Face FinBERT** classification pipeline (Bullish, Bearish, Neutral).
  - Sentiment metrics stored in PostgreSQL DB.
- **Machine Learning Ecosystem (`cryptosight.ml`)**:
  - Lag-free feature engineering pipeline (`.shift(1)`).
  - Classification models (XGBoost, LightGBM, Random Forest) & Sequence models (LSTM).
  - Out-of-sample forward inference pipeline.
  - Scaler & model artifact storage (`.pkl`, `.json`, `.pt`).
  - Dedicated `ml_backtests` trade ledger export schema.
- **Statistical Analytics (`cryptosight.stats`)**:
  - 59+ institutional performance ratios (CAGR, Sharpe Ratio, Sortino Ratio, Calmar Ratio, Profit Factor, Expectancy, Max Drawdown, Tail Ratio).
  - Dynamic Plotly chart generators (Equity, Drawdown, Monthly Returns heatmap/bar, Rolling Sharpe/Volatility).
- **Automated Live Bybit Execution Engine (`cryptosight.execution`)**:
  - Bybit UTA V5 REST API integration (`bybit_executor.py`).
  - Master execution engine (`engine.py`) polling live signals, managing active positions (`execution.active_positions`), and placing orders.
  - Exchange history synchronization (`account_history.executions`, `closed_pnl`, `transaction_log`).
  - Position reconciliation & performance stats (`execution.stats` & `account.stats`).
- **FastAPI REST API Backend Services (`cryptosight.backend`)**:
  - APIRouters & Services for `/api/v1/dashboard/summary`, `/api/v1/strategies`, `/api/v1/backtests`, `/api/v1/wallets`, and `/api/v1/ml`.
  - Real-time DB health endpoint `/api/v1/backtests/health` connected to PostgreSQL.
  - Real-time chart calculation service (`generate_charts_from_trades`) calculating 4 series (Equity, Drawdown, Monthly Returns, Rolling Metrics) directly from raw SQL trade ledgers.
  - Zero-fake-data policy with explicit `*_unavailable` flags when APIs are disconnected.

#### 2. Frontend React 18 Dashboard (`cryptosight/frontend`)
- **11 Interactive Dashboard Pages**:
  1. `Dashboard` (`/`): Executive overview, portfolio total value, strategy count, asset donut allocation, strategy ranking table.
  2. `StrategyDetails` (`/strategies` & `/strategies/:id`): Strategy catalog, configuration parameters, YAML rules inspector, risk settings, trade ledger.
  3. `Wallets` (`/wallets`): Wallet balances, exchange connection modal (Binance/Bybit), API credentials status, equity growth curve.
  4. `Deployment` (`/deployment`): Live strategy runner overview, active position count, engine status toggle, live PnL, and strict ledger gatekeeping (warning toast when opening strategies without a DB ledger).
  5. `ExecutionDetails` (`/deployment/:id`): Institutional live trade execution inspector featuring a 100% full-width 8-metric KPI matrix (`Current PnL`, `PnL %`, `Win Rate`, `Profit Factor`, `Total Trades`, `Max Drawdown`, `Last Signal`, `Last Execution`), an 8-parameter **Execution Configuration** matrix mapped 1:1 with `metadata.execution_config`, full-width **Performance Charts & Oscillators** with 4 tabs (`Equity Curve & Drawdown`, `PnL Per Trade`, `Trade History & Position Size`, `Monthly Returns`), dynamic PostgreSQL trade ledger calculations (`execution_service.py`), and clean timestamp formatting (automatically stripping `.microseconds`, `+00:00`, `UTC`, and `Z` noise).
  6. `BacktestRequests` (`/backtests`): Vectorized backtest list, status pills, run new backtest modal form.
  7. `BacktestDetails` (`/backtests/:id`): Full strategy backtest inspector with 4 Lightweight Charts tabs (Equity, Drawdown, Monthly Returns, Rolling Metrics), 59+ QuantStats metrics grid, and interactive trade ledger.
  8. `MachineLearning` (`/ml`): Model catalog, task type filter (classification/regression), symbol filter, model accuracy/F1 score KPI cards.
  9. `ModelDetails` (`/ml/:id`): Detailed ML model inspector with confusion matrix / classification report, feature importances, hyperparameters, forward inference signal chart, model backtest trade ledger.
  10. `Sentiment` (`/sentiment`): Sentiment overview, FinBERT classification status, market bullish/bearish gauge, asset sentiment breakdown, raw Reddit post feed.
  11. `AccountOverview`: Account settings and security parameters.
- **Design System & Theme Switcher**:
  - Full Dark Mode and Light Mode support with seamless state persistence (`localStorage`).
  - Topbar `● DB Active` pill styled in custom sage green theme palette with ambient glow.
  - Soft matte red palette (`#EE5D5D`) for zero eye strain on negative PnL and trade status chips.
  - Up/Down interactive sorting on all table headers (`TableSortLabel`).

---

### 🟡 **What is LEFT / IN-PROGRESS / UPCOMING ROADMAP**

1. **Authentication & User Authorization**:
   - **Status**: Pending.
   - **Description**: FastAPI currently operates without JWT / OAuth2 auth middleware. User login/signup pages and API token header validation are scheduled for future security hardening.
2. **Real-Time WebSockets (`ws://`) Streaming**:
   - **Status**: Planned.
   - **Description**: Frontend currently uses 15s REST polling for DB health and data fetching. Adding a dedicated WebSocket server (`cryptosight.backend.ws`) for live tick prices and real-time trade execution notifications will minimize latency.
3. **Distributed Async Task Queue (Celery + Redis)**:
   - **Status**: Planned.
   - **Description**: Backtest submission (`POST /api/v1/backtests`) currently runs via FastAPI `BackgroundTasks` in-process. For large multi-year 1m backtests, delegating to Celery workers with Redis message broker is planned.
4. **Multi-Exchange Execution Expansion (Binance Futures & OKX)**:
   - **Status**: In-Progress.
   - **Description**: The live execution engine currently targets **Bybit UTA V5**. Expanding `bybit_executor.py` into a unified multi-exchange facade for Binance Futures and OKX live trading.
5. **Real-Time Alerting System (Telegram / Discord Webhooks)**:
   - **Status**: Planned.
   - **Description**: Webhook alerting config fields exist in `strategy_config.yaml`. Adding a dedicated notification dispatcher service for immediate trade entry/exit alerts to Telegram and Discord.
6. **Automated Unit & E2E Test Suite Expansion**:
   - **Status**: In-Progress.
   - **Description**: Adding comprehensive PyTest backend tests for backtest math validation and Playwright/Cypress end-to-end frontend regression testing.

<div align="right"><a href="#top">⬆️ Back to Top</a></div>

---

<div id="quickstart"></div>

## ⚡ Quick Start Guide

### 1️⃣ **Environment Setup**
```bash
# Clone the repository
git clone https://github.com/21Afnan/cryptosight.git
cd cryptosight

# Create and activate Python virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Install Python backend dependencies
pip install -r requirements.txt

# Install React frontend dependencies
cd frontend
npm install
cd ..
```

### 2️⃣ **Running FastAPI Backend Server**
```bash
# Launch FastAPI server on port 8000 with auto-reload
python -m uvicorn cryptosight.backend.main:app --reload --port 8000
```
- **Interactive Swagger Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **Health Check Endpoint**: [`http://localhost:8000/api/v1/backtests/health`](http://localhost:8000/api/v1/backtests/health)

### 3️⃣ **Running React Frontend Trading Dashboard**
```bash
# Launch Vite development server on port 5173
cd frontend
npm run dev
```
- **Trading Dashboard UI**: [`http://localhost:5173`](http://localhost:5173)

### 4️⃣ **Running Ingestion, Execution, Backtesting & ML Pipelines**
```bash
# Download Binance & Bybit Market Data
python -m cryptosight.data.binance.main
python -m cryptosight.data.bybit.main

# Run Live Bybit Automated Execution Engine
python -m cryptosight.execution.main

# Run Vectorized Backtest Engine
python -m cryptosight.backtesting.backtest

# Run Machine Learning Pipeline
python -m cryptosight.ml.main
```

<div align="right"><a href="#top">⬆️ Back to Top</a></div>

---

<div id="structure"></div>

## 📁 Complete Repository Structure

```text
cryptosight/
├── backend/                       # FastAPI REST API backend services & routers
│   ├── main.py                    # FastAPI application setup, CORS middleware & route registration
│   ├── routers/                   # APIRouters (dashboard, strategy, backtest, wallet, ml)
│   └── services/                  # Business logic & PostgreSQL query builders
├── data/                          # Exchange downloaders with smart SQL gap fill & live bar protection
│   ├── downloader.py              # Master Downloader class with SQL COPY stream & resampling
│   ├── binance/                   # Binance API fetcher, config.yaml & main runner
│   └── bybit/                     # Bybit API fetcher, config.yaml & main runner
├── execution/                     # Live Bybit Automated Execution Engine & Reconciliation Pipeline
│   ├── engine.py                  # Master execution loop, position tracking & auto-reconciliation
│   ├── bybit_executor.py          # Bybit V5 REST API executor, order placement & PnL/fee fetcher
│   ├── account_stats.py           # Account-level performance statistics engine & PostgreSQL upsert
│   ├── selector.py                # Top performing strategy selector from metadata
│   └── main.py                    # Master execution entry point
├── tal_Indicators/                # Dynamic __getattr__ wrapper for all 158 TA-Lib technical indicators
├── signals/                       # YAML/DB-driven quant signal generator & multi-crossover rule engine
├── simulator/                     # Real-time event-driven simulation engine with active position tracking
├── backtesting/                   # Vectorized 10-step backtester modeling commissions, slippage & SQL ledger
├── sentiment/                     # PRAW Reddit scraper, text cleaning engine & Hugging Face FinBERT classifier
├── ml/                            # Comprehensive end-to-end Machine Learning ecosystem
├── stats/                         # Institutional statistical analytics & frontend charts suite (QuantStats + Plotly)
├── frontend/                      # React 18 / Vite quantitative trading dashboard interface
│   ├── src/                       # React components, charts, pages, theme design system & contexts
│   └── PROGRESS.md                # Detailed frontend & full-stack development log
├── csv_files/                     # Automated export directory for predictions, reports & master tables
├── logs/                          # Rotating execution logs with SafeRotatingFileHandler
├── utils/                         # Shared utilities (db.py PostgreSQL pool, metadata.py schema managers, logger.py)
├── .env                           # Database & API credentials (git-ignored)
├── README.md                      # Enterprise system documentation
└── requirements.txt               # Python package dependencies
```

<div align="right"><a href="#top">⬆️ Back to Top</a></div>

---

<div id="author"></div>
<div align="center">

## 👨‍💻 Built & Engineered by Afnan Shoukat

**Full-Stack Quantitative Engineer • Financial Data Scientist • Algorithmic Systems Architect**

[![Connect on LinkedIn](https://img.shields.io/badge/Connect%20on-LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/afnanshoukat)
[![Follow on GitHub](https://img.shields.io/badge/Follow%20on-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/21Afnan)

*Designed with enterprise precision, zero data leakage, and institutional quantitative rigor.*

© 2026 CryptoSight. All rights reserved.

</div>
