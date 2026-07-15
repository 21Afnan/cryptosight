# 🚀 CryptoSight: Enterprise Quantitative Data & Technical Analysis Engine

<div align="center">

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Enterprise_Storage-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![TA-Lib](https://img.shields.io/badge/TA--Lib-158_Indicators-green?style=for-the-badge)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_Dark_Charts-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Automated_Pipeline-orange?style=for-the-badge)

**An automated, production-grade cryptocurrency data ingestion, dynamic technical analysis, and signal generation framework built for quantitative analysts, algorithmic traders, and financial engineers.**

</div>

---

## 🌟 Executive Summary

**CryptoSight** bridges the gap between raw cryptocurrency market data feeds and institutional-grade quantitative strategies. It eliminates boilerplate data cleaning, API pagination headaches, and indicator mapping complexities by providing an end-to-end automated framework:

1. **Automated Data Ingestion**: Seamlessly connects to **Binance** and **Bybit**, fetching historical and real-time OHLCV (Open, High, Low, Close, Volume) data with smart gap detection against a **PostgreSQL** database.
2. **Dynamic 158 TA-Lib Engine**: Harnesses Python magic methods to wrap all 158 TA-Lib technical indicators dynamically, supported by an institutional parameter hierarchy and interactive multi-panel Plotly charting.
3. **YAML-Driven Quantitative Signal Pipeline**: Evaluates multi-indicator crossover conditions, tracks look-back persistence windows, and generates leak-free long/short trading signals automatically in lightweight database tables.
4. **Vectorized 10-Step Backtesting Engine**: Executes ultra-fast historical simulations with realistic market friction modeling (broker commissions, price slippage), dynamic position sizing, automated Take-Profit/Stop-Loss scanning, and stores the completed ledger directly in PostgreSQL.
5. **AI Sentiment Ingestion & NLP Pipeline**: Scrapes real-time discussions from **Reddit**, processes text dynamically (unescaping HTML entities, expanding contractions, stripping punctuation/numbers), structures text with clear headers, and predicts sentiment (Bullish/Bearish/Neutral) using **Hugging Face FinBERT** (with chunk-averaging to bypass the 512-token limit).
6. **Quantitative ML Feature Engineering & Target Pipeline (`cryptosight.ml`)**: A pure in-memory, decoupled quant data pipeline (`MLFeatureBuilder`) that resamples raw market data to target timeframes (`15m`, `1h`), calculates multi-indicator technical features and candlestick patterns (`EMA`, `RSI`, `MACD`, `DOJI`, `ENGULFING`) with automatic **Look-Ahead Bias Prevention (`.shift(1)`)**, generates state-of-the-art **Log Return (`np.log`)** and **Threshold-Filtered Classification (`1/-1/0`)** targets, and automatically exports clean ML datasets directly to CSV inside `ml/datasets/`.
7. **Quantitative Preprocessing & Backtesting Evaluation Pipeline (`cryptosight.preprocessing`)**: An institutional evaluation suite that checks feature stationarity (`ADF & KPSS tests`), executes raw unmodeled baseline backtests (`ACTUAL_DF_NO_MODEL` with threshold gates), benchmarks 6 quantitative preprocessing methods (`RobustScaler, MinMaxScaler, Winsorization, Fractional Differencing, Log, Gaussian`), cross-evaluates multi-task ML models (`Regression vs. Classification`), and generates a **Master Leaderboard & Trade Ledger Breakdown** directly via the quantitative `BacktestingEngine`.
8. **Quantitative Performance & Risk Analytics Suite (`cryptosight.stats`)**: An automated statistical evaluation and interactive visualization engine that connects to PostgreSQL backtest ledgers (`backtests.{strategy_id}`) to compute **59+ QuantStats metrics** (`CAGR`, `Sharpe Ratio`, `Sortino Ratio`, `Calmar Ratio`, `Max Drawdown`) via dynamic Python introspection (`inspect.getmembers`). Features robust `NaN`/`Inf` JSON serialization (`metrics_report.json`), and generates **6 frontend-ready Plotly quant charts** (`daily_returns`, `log_returns`, `returns`, `yearly_returns`, `drawdown`, `drawdowns_periods`) exported as both standalone HTML files and 1 consolidated master report (`all_charts.json`) containing pure JSON `plotly_figure` dicts (with `.tolist()` to eliminate base64 `bdata`) + direct `raw_values` arrays (`[{time, value}]`) tailored for effortless custom frontend integration.

---

## 🏗️ How It Was Built: Core Architectural Principles

CryptoSight was engineered with reliability, data integrity, and zero-redundancy in mind. Instead of writing ad-hoc scripts, the system is organized into modular architectural layers:

```mermaid
graph TD
    subgraph Data Ingestion Layer
        API["Exchange APIs (Binance & Bybit)"] -->|Fetch Price Data| Fetcher["Exchange Downloaders"]
        Fetcher -->|Clean & Organize| Facade["Master Data Downloader"]
        Reddit["Reddit API (PRAW Client)"] -->|Scrape Posts & Comments| RedditScraper["Reddit Scraper & Saver"]
    end

    subgraph Database & Storage Layer
        Facade -->|Check Last Saved Candle Date| SQL_Check[("PostgreSQL Database")]
        SQL_Check -->|Download Only Missing Data| Facade
        Facade -->|Fast Save & Remove Duplicates| SQL_Check
        
        RedditScraper -->|Save Raw Posts & Comments| SQL_Check
        SQL_Check -->|Fetch Unprocessed Raw Posts| AI_Sentiment["AI Sentiment Pipeline"]
        AI_Sentiment -->|Save Predict, Score & Ratio| SQL_Check
    end

    subgraph Indicators & Charting Layer
        SQL_Check -->|Load Price Candles| Engine["158 Technical Indicators Engine"]
        Engine -->|Show Interactive Charts| Dashboard["Dark Mode Web Charts"]
    end

    subgraph Trading Signals Layer
        Engine -->|Apply Indicator Rules| Signals["Trading Signal Generator (YAML Rules)"]
    end

    subgraph Backtesting & Simulation Layer
        SQL_Check -->|Load 1m Price Candles| Backtester["Strategy Backtesting Engine"]
        Signals -->|Send Trading Signals| Backtester
        Backtester -->|Simulate Trades, TP/SL & Fees| Ledger["Backtest Ledger Database Table"]
    end

    subgraph Machine Learning & Target Engineering Layer
        SQL_Check -->|Resample 1m OHLCV| ML_Resample["Step 1: Market Data Downloader & Resampler"]
        ML_Resample -->|Pass Resampled df| ML_Features["Step 2: Technical & Pattern Feature Builder"]
        ML_Features -->|Inject Indicators & Patterns| ML_Target["Step 3: Multi-Paradigm Target Generator"]
        ML_Target -->|Clean Output| ML_Dataset["Memory-Ready ML Datasets (Regression / Classification / TimeSeries)"]
    end

    subgraph Preprocessing & Evaluation Leaderboard Layer
        ML_Dataset -->|Stationarity Checks ADF/KPSS| PP_Stationarity["Stationarity & Trend Analyzer"]
        PP_Stationarity -->|Apply 6 Transforms| PP_Methods["Robust | MinMax | FracDiff | Winsorize | Log | Gaussian"]
        PP_Methods -->|Train LGBM / XGB / Linear| PP_Models["Multi-Model Cross-Evaluation"]
        PP_Models -->|Send Signals (+1, 0, -1)| Backtester
        Backtester -->|Leaderboard & PnL Table| PP_Leaderboard["Final Master Summary Table & Trade Ledger Analysis"]
    end

    subgraph Quantitative Performance & Risk Analytics Layer
        PP_Leaderboard -->|Pass Completed Backtest Ledger| Stats_Engine["Automated 59+ QuantStats Metrics Engine (metrices.py)"]
        Stats_Engine -->|Dynamic Introspection & Safe Serialization| Stats_JSON["metrics_report.json (Safe NaN / Inf / Timestamp Handling)"]
        Stats_Engine -->|Render 6 Frontend-Ready Quant Charts| Stats_Plots["daily_returns | log_returns | returns | yearly_returns | drawdown | drawdowns_periods"]
        Stats_Plots -->|Consolidate into 1 Master Report| Stats_Master["all_charts.json (plotly_figure dicts + raw_values arrays)"]
    end
```

### 🧠 1. Smart Gap Ingestion & Zero-Redundancy Storage
When running routine data updates, re-downloading entire historical datasets is inefficient and risks exchange rate-limits. CryptoSight solves this via **Smart Gap Detection**:
- The pipeline queries PostgreSQL for the exact timestamp of the last stored candle (`latest_ts`).
- It computes the precise delta between `latest_ts` and current time, instructing the exchange client to download **only the missing gap**.
- Employs high-speed PostgreSQL bulk insertion into staging tables with automated deduplication to guarantee database integrity.

### 🛡️ 2. Live Candle Protection & Timestamp Normalization
Cryptocurrency exchanges often stream unclosed, currently active candles (e.g., a 1-hour candle that is only 15 minutes old). Writing incomplete bars corrupts technical analysis indicators. CryptoSight automatically inspects the latest bar's timestamp and strips out active live candles, ensuring **only fully finalized candles** enter your permanent SQL storage. All timestamps are standardized to UTC milliseconds.

### 🔮 3. Dynamic "Magic" TA-Lib Wrapper
Instead of hardcoding functions for 158 different indicators, CryptoSight utilizes Python's dynamic object interception. When an indicator method is called on the wrapper class, the engine intercepts the call, consults a rich institutional catalog, maps column schemas, resolves parameter defaults, and executes C-compiled TA-Lib operations in microseconds.

### ⚡ 4. Look-Ahead Bias-Free Signal Generation
The quantitative signal engine evaluates trading rules defined in human-readable YAML configuration files. To ensure realistic backtesting and live trading execution:
- Conditions (such as moving average crossovers or RSI thresholds) are evaluated across configurable persistence windows.
- Generated signals are automatically **shifted by 1 bar** so that a signal triggered by the close of Bar $T$ is executed at the open of Bar $T+1$.
- **Lightweight Signals Schema**: Signals are saved in `signals.{exchange}_{symbol}_{target_timeframe}` containing only the `timestamp` and `signal` columns (dropping redundant OHLCV columns, indicators, and conditions) to keep the database extremely lightweight and fast.

### 📈 5. Vectorized Backtesting, Naming Rules & Metadata Tracking
To validate strategies before deployment, CryptoSight features a custom vectorized 10-step backtesting engine (`backtesting/backtest.py`):
- **High-Speed Ingestion**: Pulls 1-minute OHLCV candles via PostgreSQL's fast `COPY` stream.
- **Execution Pricing**: Models trade entries and exits at `next_open` or `current_close` to prevent look-ahead bias.
- **Dynamic Risk & Order Management**: Automatically calculates position sizes based on capital percentages and vector-scans future candle highs/lows to detect Take-Profit (TP) and Stop-Loss (SL) triggers.
- **Market Friction Modeling**: Incorporates broker commissions and execution slippage on both entry and exit legs, calculating accurate Gross PnL, Net PnL, and running account balances.
- **Strategy ID Integration**: Automatically creates a unique `strategy_id` based on the exchange, coin, timeframe, and sorted indicators + their periods (e.g. `binance_sol_1h_rsi_14`) to prevent naming collision and duplicate runs.
- **Database-Only Storage**: The trade ledger is saved directly in PostgreSQL under the table name `backtests.{strategy_id}` (e.g., `backtests.binance_sol_1h_rsi_14`) instead of local CSV files.
- **Metadata Configuration Tracking**: Saves high-level config snapshots and summary results (total trades, win rate, net PnL, final balance) into the relational table `metadata.backtest_data` connected via Foreign Key to `metadata.strategy_data(strategy_id)`.

### 🧪 6. Decoupled Quantitative ML Pipeline (`cryptosight.ml`)
To prepare clean, stationary, and leak-free datasets for advanced AI and machine learning training (e.g., XGBoost, LSTMs, PyTorch), CryptoSight includes an institutional quantitative ML data builder governed by the **Single Responsibility Principle**:
- **Single Source of Truth (`main.py`)**: The central entry point (`ml/main.py`) exclusively handles disk I/O and configuration loading (`load_config`), passing a pre-loaded dictionary directly into the quantitative processing engine to eliminate redundant file reads (`DRY Principle`).
- **3-Step In-Memory Quant Engine (`features.py`)**: `MLFeatureBuilder` executes a strictly ordered functional flow:
  1. *Step 1 (Resampling)*: Dynamically converts raw `1m` OHLCV database candles into any configured `target_timeframe` (`15m`, `1h`, `4h`) via `Downloader`.
  2. *Step 2 (Feature Engineering & Look-Ahead Bias Prevention)*: Delegates all technical indicators and candlestick chart patterns directly to `Indicators.get_dataframe()`. All computed features are automatically **lagged by 1 period (`.shift(1)`)** prior to merging onto the OHLCV DataFrame, guaranteeing that models never peek into the current bar's closing price when making future predictions.
  3. *Step 3 (Target Generation)*: Computes exact prediction targets tailored for three distinct paradigms:
     - `Regression (Log Return)`: Quant state-of-the-art continuous log return (`np.log(Close_future / Close_current)`) exactly `horizon` bars into the future (`shift(-horizon)`), providing symmetric time-additivity and stationarity.
     - `Classification (Threshold-Filtered Directional)`: 3-class target (`1` for Buy, `-1` for Sell, `0` for Hold/Noise) filtered by a configurable `threshold` (`0.2%` by default) so model labels only trigger on price movements that exceed exchange commissions and slippage.
     - `Time Series (Raw Future Shifting)`: Shifting raw source price sequences by `horizon` bars (`shift(-horizon)`) for sequence-to-sequence deep forecasting models (LSTMs, GRUs, Transformers).
- **Automatic CSV Exporter (`ml/datasets/`)**: Every execution of the ML pipeline automatically stores the final, clean, warm-up-dropped dataset as a CSV (`{SYM}_{timeframe}_features.csv`) directly inside `cryptosight/ml/datasets/`.
- **Flexible OHLCV Filtering (`data.enabled: false`)**: If `data.enabled` is set to `false`, the pipeline still fetches raw candles to compute all technical features and targets cleanly, but automatically drops the base `open, high, low, close, volume` columns from the final output—leaving a pure feature matrix ready for custom AI models.

### ⚖️ 7. Quantitative Preprocessing, Stationarity Testing & Threshold Optimization (`cryptosight.preprocessing`)
To scientifically determine which feature scaling technique maximizes trading profitability and model accuracy, the preprocessing suite (`preprocessing/`) executes a rigorous empirical leaderboard loop:
- **Mathematical Stationarity & Trend Decomposition (`stationarity.py`)**: Runs Augmented Dickey-Fuller (`ADF`) and Kwiatkowski-Phillips-Schmidt-Shin (`KPSS`) tests on raw features alongside rolling trend metrics to isolate non-stationary drift before training.
- **Unmodeled Baseline Backtesting (`ACTUAL_DF_NO_MODEL`)**: Before evaluating complex ML algorithms, the pipeline runs a direct backtest on the raw price/target series using a configurable signal threshold (e.g. `0.20% / 0.002`). This establishes the true empirical benchmark for trade frequency, win rate, and baseline PnL.
- **6-Paradigm Preprocessing Leaderboard (`preprocessor.py`)**: Systematically transforms out-of-sample test features using:
  1. `RobustScaler` (Median and Interquartile Range based; impervious to extreme crypto spikes/outliers)
  2. `MinMaxScaler` (Strict `[0, 1]` bounded scaling for neural networks and GRUs)
  3. `Winsorize` (Empirical outlier clipping at top/bottom `1%` boundaries)
  4. `Fractional Differencing` (`frac_d = 0.35` to make time series stationary while retaining memory and correlation)
  5. `Log Transformation` & `Gaussian Quantile Mapping` (`Normal distribution transformation`)
- **Multi-Task & Multi-Model Evaluation (`models.py`)**: Evaluates `LightGBM`, `XGBoost`, and `Linear Regression` across both **Classification (`+1, 0, -1`)** and **Regression (`Continuous log return prediction`)**.
- **Continuous Return Threshold vs. Classification Noise**: Demonstrates why raw classification (`predict_proba() > 0.50`) causes excessive over-trading in choppy/sideways markets (`360+ trades losing $5,000+ in broker fees`). By switching to `Regression` and applying a continuous `regression_signal_threshold: 0.002` (`0.20% return gate`), models only execute trades when the predicted movement exceeds round-trip broker commissions (`0.14%`) and slippage (`0.06%`).
- **Direct Engine Integration (`backtest_runner.py`)**: Passes all generated model signals (`+1, 0, -1`) and unscaled test prices directly into the built-in `BacktestingEngine` (`cryptosight.backtesting.backtest.BacktestingEngine`), generating a unified **Step 8 & 9 PnL Leaderboard** and **Step 10 Master Summary Table (`BTC_final_summary_master_table.csv`)**.

### 📊 8. Quantitative Performance & Risk Analytics Suite (`cryptosight.stats`)
To transform raw backtest ledgers into institutional performance showcases and frontend-ready data feeds, CryptoSight provides a decoupled statistical analytics suite:
- **Dynamic 59+ Metric Introspection (`metrices.py`)**: Uses Python's `inspect.getmembers()` to automatically discover and execute all scalar statistical functions inside `quantstats.stats` (`cagr`, `sharpe`, `sortino`, `calmar`, `max_drawdown`, `win_rate`, `profit_factor`, `tail_ratio`). Automatically skips multi-series or benchmark-dependent calculations without requiring manual maintenance (`DRY Principle`).
- **Safe JSON Type Normalization (`to_json_safe`)**: Recursively sanitizes mathematical edge cases (`numpy.float64`, `pd.Timestamp`, `float('nan')`, `float('inf')`) into clean JSON strings and null (`None`) values rounded to 6 decimal places, guaranteeing 100% valid JSON formatting inside `cryptosight/stats/metrics_report.json`.
- **6 Essential Quant Visualizations (`plots.py`)**: Generates interactive, dark-mode Plotly charts focused on institutional risk and return milestones:
  1. `daily_returns`: Daily resampled / period returns over time (`%`)
  2. `log_returns`: Cumulative log returns trajectory (`%`)
  3. `returns`: Baseline cumulative strategy equity curve (`%`)
  4. `yearly_returns`: Annual / year-by-year compounded returns (`%`)
  5. `drawdown`: Portfolio underwater drawdown depth & duration (`%`)
  6. `drawdowns_periods`: Highlights top 5 worst drawdown episodes overlaid directly on the `$100 Base` equity index.
- **Frontend-Ready Dual-Format JSON Architecture (`all_charts.json`)**: To support custom web dashboards (`React`, `Next.js`, `Vue`, `Chart.js`, `Recharts`, `Plotly.js`), `generate_all_plots()` consolidates all 6 charts into one master report (`all_charts.json`) providing:
  - `"plotly_figure"`: Pure JSON dictionary of `data` and `layout`. Explicitly calls `.tolist()` on all pandas indexes and series to **permanently eliminate base64 `bdata` strings**, allowing direct plug-and-play rendering.
  - `"raw_values"`: Direct lightweight JSON arrays (`[{"time": "...", "value": 1.8614}, ...]`) for custom UI cards and lightweight chart libraries without parsing complex Plotly structures.

---

## 📁 Complete Repository Structure & Guide

```text
cryptosight/
├── data/
│   ├── binance/
│   │   ├── binance_client.py      # Binance API fetcher with automatic retry & timestamp normalization
│   │   ├── config.yaml            # YAML settings (symbols, timeframe, date ranges, retry rules)
│   │   ├── main.py                # Single-call execution script for Binance ingestion
│   │   └── run_binance.bat        # One-click Windows runner script for automated ingestion
│   ├── bybit/
│   │   ├── bybit_client.py        # Bybit API fetcher with forward chunk pagination loop
│   │   ├── config.yaml            # YAML settings for Bybit ingestion
│   │   ├── main.py                # Single-call execution script for Bybit ingestion
│   │   └── run_bybit.bat          # One-click Windows runner script for automated ingestion
│   └── downloader.py              # Master orchestrator (run_pipeline, download, get_data, resample)
├── sentiment/
│   ├── config.yaml            # NLP configurations (symbols, subreddits, posts limit, model name)
│   ├── db.py                  # Schema definitions (reddit_raw and reddit_cleaned) and insertion queries
│   └── main.py                # PRAW client scraper, text preprocessor, and FinBERT analyzer
├── tal_Indicators/
│   ├── tal_ind_con.py             # Institutional catalog of 158 TA-Lib indicators & schema definitions
│   └── indicators.py              # Dynamic Indicators class wrapper & Plotly master dashboard engine
├── signals/
│   ├── strategy_config.yaml       # Quantitative strategy definitions (indicators, operators, and rules)
│   ├── conditions.py              # Evaluates multi-bar condition persistence windows
│   ├── rules.py                   # Generates integer trading signals (+1 Long, -1 Short, 0 Neutral)
│   └── main.py                    # Master execution pipeline running indicators -> conditions -> signals
├── backtesting/
│   ├── backtest.py                # Vectorized 10-step quantitative strategy backtesting engine
│   └── backt_config.yaml          # YAML settings for market selection, position sizing, fees & TP/SL
├── ml/
│   ├── main.py                    # Single-call orchestrator handling disk config loading (`get_ml_dataset`)
│   ├── features.py                # 3-Step in-memory quant engine (`MLFeatureBuilder`) for features & targets
│   └── ml_config.yaml             # YAML specifications for timeframes, features, and target paradigms
├── preprocessing/
│   ├── pp.config.yaml             # YAML configurations for method selection, task type, models & thresholds
│   ├── main.py                    # Single-call pipeline executing stationarity -> preprocessing -> leaderboard
│   ├── preprocessor.py            # Encapsulates Robust, MinMax, Winsorize, FracDiff, Log & Gaussian scaling
│   ├── stationarity.py            # Conducts Augmented Dickey-Fuller (ADF) & KPSS mathematical tests
│   ├── models.py                  # Trains & evaluates LGBM, XGBoost & Linear models across prep methods
│   ├── backtest_runner.py         # Interfaces model predictions with BacktestingEngine for PnL metrics
│   └── analyze_backtest_ledger.py # Audits trade ledgers (Long/Short ratios, TP/SL hit rates, fee drag)
├── stats/
│   ├── main.py                    # Master pipeline orchestrator: executes backtest -> computes metrics -> generates charts
│   ├── metrices.py                # Automated 59+ QuantStats metrics engine with inspect auto-discovery & safe JSON export
│   ├── plots.py                   # Generates 6 quant charts + dual-format all_charts.json (plotly_figure + raw_values)
│   ├── metrics_report.json        # Exported JSON report of all 59+ strategy performance ratios
│   └── charts/                    # Destination directory for all 6 HTML interactive charts and all_charts.json
├── csv_files/                     # Automated export directory for predictions, reports & master tables
├── logs/
│   ├── binance.log                # Rotating log file tracking Binance API execution
│   ├── bybit.log                  # Rotating log file tracking Bybit API execution
│   ├── db.log                     # Database connection and SQL query execution logs
│   └── nlp.log                    # AI Sentiment and Reddit scraping logs
├── utils/
│   ├── config.py                  # YAML loader and centralized environment variable loading utility
│   ├── db.py                      # PostgreSQL schema, connection pooling, and bulk COPY loader
│   └── logger.py                  # Centralized logger config (shared handlers, UTF-8 Windows encoding)
├── .env                           # Database and Reddit API environment variables (git-ignored)
├── requirements.txt               # Python package dependencies
└── README.md                      # Complete project documentation and operation guide
```

---

## 🛠️ Step-by-Step Guide: How to Run & Operate the Application

CryptoSight is designed for seamless operation. You do not need to write code or scripts to run data ingestion, generate quantitative signals, evaluate preprocessing techniques, or view interactive charts. Everything is controlled through simple configuration files and pre-built runners.

### Step 1: Initial Environment Preparation

1. **Virtual Environment**: Ensure Python 3.10+ is installed. Activate your project virtual environment from your system terminal or file explorer (`venv\Scripts\activate`).
2. **Dependencies**: Install the required packages listed in the project requirements file (`pip install -r requirements.txt`). Ensure `TA-Lib` is installed via pre-built Windows wheel if necessary.

---

### Step 2: Database Configuration

Create a simple text file named `.env` inside the root workspace folder containing your PostgreSQL database connection details:
- **Host**: Your local database address (usually `localhost`)
- **Port**: Standard PostgreSQL port (`5432`)
- **Name**: Your target database name
- **User & Password**: Your secure database credentials

*Note: The system automatically detects missing tables on first run and builds optimal database structures and indices without any manual intervention.*

---

### Step 3: Running Market Data Ingestion

You can configure which coin pairs to download (e.g., Bitcoin or Ethereum), the candlestick timeframe, and historical date ranges simply by opening the configuration files (`data/binance/config.yaml` or `data/bybit/config.yaml`) in any text editor.

| Execution Method | How to Run | Best For |
| :--- | :--- | :--- |
| **Option A: One-Click Windows Execution** | Simply navigate to the exchange folder inside your file explorer and **double-click** the pre-built batch file (`run_binance.bat` or `run_bybit.bat`). | Instant manual data updates without opening a terminal window. |
| **Option B: Terminal Execution** | Run the exchange main module directly using your environment runner (`python -m cryptosight.data.binance.main`). | Developers and analysts executing pipelines within interactive terminal sessions. |
| **Option C: 24/7 Automated Background Sync** | Open **Windows Task Scheduler**, create a hidden background task pointing to the batch file (`run_binance.bat`), and set the trigger to run **every 5 minutes**. | Hands-free, continuous live database synchronization. |

---

### Step 4: Generating Quantitative Trading Signals

The quantitative signal module automatically loads synchronized market data from your database, calculates technical indicators, evaluates strategy rules, and generates trading signals.

1. **Configure Your Strategy**: Open `signals/strategy_config.yaml` in any text editor to view or adjust moving average periods, RSI overbought/oversold boundaries, or logical combination rules.
2. **Execute the Signal Pipeline**: Run the signals execution module (`python -m cryptosight.signals.main`). The pipeline automatically handles parameter resolution and processes the entire dataset.
3. **Review Results**: The system outputs a clean summary directly to your console and automatically generates a comprehensive CSV report inside the `signals/` directory (`signals_pipeline_output.csv`).

---

### Step 5: Running Quantitative Backtests & Performance Simulation

Once your trading signals are generated, use the **Vectorized Backtesting Engine** to simulate historical trading performance with institutional accuracy:

1. **Configure Simulation Parameters**: Open `backtesting/backt_config.yaml` to set your target exchange, coin symbol, date ranges, starting account balance (`$10,000`), position sizing percentage, and Take-Profit/Stop-Loss boundaries.
2. **Execute the Backtest Engine**: Run `backtesting/backtest.py` from your terminal:
   ```bash
   python -m cryptosight.backtesting.backtest
   ```
3. **Review Audit Ledger & PnL Metrics**: The engine prints an instant performance showcase to your console (Total Trades, Final Balance, Net Profit) and saves the complete trade ledger inside your database under the table name `backtests.{strategy_id}` (`backtests.binance_sol_1h_rsi_14`).

---

### Step 6: Running the AI Sentiment & NLP Pipeline

CryptoSight features a built-in NLP sentiment analysis engine to scrape Reddit discussions and evaluate market sentiment:

1. **Reddit API Credentials**: Ensure your `.env` file includes Reddit credentials (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`).
2. **Configure Pipeline Settings**: Open `sentiment/config.yaml` to specify target symbols (`BTC`, `ADA`), target subreddits (`Bitcoin`, `CryptoCurrency`), scraper limits (`posts_per_symbol: 1000`), and timeframe filters (`time_filter: "all"`).
3. **Execute the Sentiment Pipeline**: Run the sentiment entry script from your terminal:
   ```bash
   python -m cryptosight.sentiment.main
   ```
4. **How Sentiment is Classified**:
   - **Intelligent Text Cleansing**: Unescapes HTML entities, expands contractions (`i've` to `i have`), translates emojis to text words, and strips all punctuation/numbers.
   - **Excluding Bot Spam**: Automatically filters out stickied/automoderator posts and comments.
   - **FinBERT Classification**: Structures text with tags (`title: <t>. body: <b>. comments: <c1>. <c2>`) and classifies sentiment (Bullish/Bearish/Neutral). Long texts are split into 500-character chunks with a 100-character overlap using a sliding-window algorithm, and individual chunk scores are averaged dynamically.
   - **Database Layout**: Stores raw posts in `reddit_raw.<symbol>` and clean results in `reddit_cleaned.<symbol>`.

---

### Step 7: Rendering Interactive Visual Dashboards

When performing exploratory research or reviewing strategy performance, CryptoSight provides a built-in visualizer that renders multi-panel, dark-mode interactive charts directly in your web browser:

1. Pass your loaded dataset into the dynamic indicators wrapper (`Indicators(df)`).
2. Compute any required technical indicators dynamically by calling their names (`ind.rsi(timeperiod=14)`).
3. Call `ind.plot_interactive_chart()` to instantly launch an interactive visual suite featuring synchronized zooming, panning, and multi-panel indicator overlays.

> **💡 Institutional Tip**: When analyzing large datasets with hundreds of thousands of candles, slice your data to the most recent 1,000 to 2,000 bars prior to visualization (`df.tail(2000)`) to ensure lightning-fast browser performance and smooth UI interaction.

---

### Step 8: Building Quantitative Machine Learning Datasets (`cryptosight.ml`)

To prepare multi-indicator, target-labeled datasets ready for AI/ML training (`Regression`, `Classification`, or `TimeSeries`), run the unified ML pipeline orchestrator:

1. **Configure Your ML Pipeline**: Open `ml/ml_config.yaml` to specify target symbols (`symbols: ["BTC"]`), `target_timeframe` (`15m`), enabled indicators (`EMA`, `RSI`, `MACD`), and target specifications (`model_type: "regression" | "classification" | "timeseries"`, `horizon: 1`, `threshold: 0.002`).
2. **Execute the ML Dataset Engine**: Run the main module directly from your terminal:
   ```bash
   python -m cryptosight.ml.main
   ```
3. **What the Pipeline Does Automatically**:
   - **Resamples Data**: Loads exact raw DB candles and resamples them to your `target_timeframe`.
   - **Prevents Look-Ahead Bias (`.shift(1)`)**: All calculated indicators and chart patterns are shifted by 1 bar (`.shift(1)`) so the model only uses historical feature information to predict future targets.
   - **Computes Prediction Target (`.shift(-horizon)`)**:
     - *Regression*: Computes continuous log returns (`np.log(future / current)`).
     - *Classification*: Assigns `1` (Buy above fees), `-1` (Sell below fees), or `0` (Hold/Chop noise).
     - *TimeSeries*: Predicts exact future dollar prices.
   - **Automatic CSV Export**: Saves the finalized dataset right inside `cryptosight/ml/datasets/{SYM}_{timeframe}_features.csv`.
4. **Console Preview & Audit Table**: Outputs a high-readability terminal preview table (`round(4)`), placing the `target` column directly beside `close` and `volume`.

---

### Step 9: Running the Quantitative Preprocessing & Backtest Leaderboard Pipeline (`cryptosight.preprocessing`)

To scientifically evaluate which preprocessing transformation (`RobustScaler`, `MinMaxScaler`, `Winsorize`, `FracDiff`, `Log`, `Gaussian`) maximizes real-world trading PnL and directional accuracy:

1. **Configure Evaluation Parameters**: Open `preprocessing/pp.config.yaml` to select your active preprocessing method (`method: "robust"`), `model_task` (`"regression"` or `"classification"`), `regression_signal_threshold` (`0.002`), and models to evaluate (`lightgbm`, `xgboost`, `linear_regression`). Ensure `ml/ml_config.yaml` has `model_type` matched to your task.
2. **Execute the Preprocessing & Leaderboard Engine**: Run the pipeline entry point from your virtual environment terminal:
   ```bash
   python -m cryptosight.preprocessing.main
   ```
3. **What the Pipeline Does Automatically**:
   - **Step 1 to 4 (Stationarity & Baseline Backtest)**: Runs ADF and KPSS stationarity tests, followed by an unmodeled raw target benchmark (`ACTUAL_DF_NO_MODEL`) to establish the true empirical baseline.
   - **Step 5 to 7 (Multi-Method Preprocessing & ML Training)**: Loops through all configured preprocessing techniques (`methods_to_test`), fits the scalers on the training split without data leakage (`fit_transform(train)` -> `transform(test)`), and cross-evaluates all selected ML models.
   - **Step 8 to 10 (Backtest Integration & Master Summary Table)**: Passes every model's test predictions directly into `BacktestingEngine.determine_entries()` and `.determine_exits()`, computing exact institutional metrics (`Total Trades, Win Rate %, Net PnL USD, Total Profit/Loss USD`). Automatically saves:
     - `csv_files/BTC_preprocessing_benchmark_report.csv` (ML Statistical Metrics)
     - `csv_files/BTC_final_summary_master_table.csv` (Combined ML + Backtest PnL Master Table)
4. **Step 11 (Audit Trade Ledger & Noise Reduction Analysis)**: Run the institutional trade ledger analyzer to deep-dive into long/short win rates, Take-Profit vs. Stop-Loss hit ratios, and commission drag:
   ```bash
   python -m cryptosight.preprocessing.analyze_backtest_ledger
   ```
   - Outputs an exhaustive breakdown explaining how continuous regression thresholds (`0.20% / 0.002`) successfully filter out 90% of sideways market noise and eliminate excessive broker fee drag compared to raw classification coin-flips (`predict_proba > 0.50`).

---

### Step 10: Running the Quantitative Performance & Risk Analytics Suite (`cryptosight.stats`)

Once your backtesting engine has simulated your strategy and saved the trade ledger, use the analytics suite to generate comprehensive statistical metrics and interactive frontend charts:

1. **Execute the Stats Analytics Pipeline**: Run the entry point from your virtual environment terminal:
   ```bash
   python -m cryptosight.stats.main
   ```
2. **What the Pipeline Does Automatically**:
   - **Runs Backtest Engine**: Executes `BacktestingEngine.run_pipeline()`, loads `backtest_ledger.csv`, and indexes `perc_pnl` strictly by **`exit_time`** (Mark-to-Exit accounting).
   - **Computes 59+ Institutional Metrics**: Auto-discovers and calculates QuantStats ratios (`CAGR`, `Sharpe`, `Sortino`, `Max Drawdown`, `Calmar`, `Win Rate`), serializing them cleanly into `cryptosight/stats/metrics_report.json`.
   - **Generates 6 Frontend-Ready Quant Charts**: Produces `daily_returns.html`, `log_returns.html`, `returns.html`, `yearly_returns.html`, `drawdown.html`, and `drawdowns_periods.html`.
   - **Exports `all_charts.json` for Web Developers**: Saves every chart with both a clean `plotly_figure` dict (pure lists without binary `bdata`) and a lightweight `raw_values` array (`[{time, value}]`) ready for Chart.js, Recharts, or custom UI components.
3. **Console Performance Overview**: Prints the top 12 headline metrics (`CAGR`, `Sharpe Ratio`, `Calmar Ratio`, `Max Drawdown`, `Win Rate`) right in your terminal for instant strategic assessment.

---

<div align="center">
<b>CryptoSight</b> — Built for Quantitative Precision & High-Performance Data Engineering.
</div>
