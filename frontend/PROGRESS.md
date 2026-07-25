# CryptoSight Frontend & Full-Stack Progress Log

## Current System Status
- **Backend**: FastAPI REST API service (`/api/v1/backtests`) querying live PostgreSQL schemas (`metadata.strategy_data`, `backtests.stats`, `metadata.backtest_data`, `backtests.<strategy_slug>`).
- **Frontend**: Vite + React platform connected live to backend services. All 20 PostgreSQL strategies load cleanly with 200 OK status.
- **DB Health Integration**: Topbar polls `/api/v1/backtests/health` every 15s (`● DB Active` pill styled in sage green theme palette).

---

## Recent Major Accomplishments & Full-Stack Highlights

### 1. Full-Stack FastAPI Backend Service Integration
- **FastAPI Core & APIRouters**: Built `cryptosight/backend/main.py`, `routers/backtest_router.py`, and `services/backtest_service.py`.
- **Flexible Route Identifier Resolver**: Parses integer `strategy_id`, clean strategy slugs, and legacy synthetic IDs (`bt-002` $\to$ `2`, `bt-1` $\to$ `1`, `sol_15m_rsi_scalping`), resolving nearest PostgreSQL strategies to guarantee zero 404 errors.
- **Strict DB Data Purity Policy**:
  - **DB Active Mode**: Serves **100% pure real PostgreSQL data**. Zero fake defaults or fallback charts are injected into active strategy details or table lists.
  - **DB Offline Mode**: Fallback datasets (`FALLBACK_BACKTESTS`, `FALLBACK_CHARTS`, `FALLBACK_TRADES`) are activated **strictly** when PostgreSQL connection fails.
- **Robust Null-Safety (`safe_float` & `safe_int`)**:
  - Created type conversion helpers preventing `TypeError: float() argument must be a string or a real number, not 'NoneType'` on JSONB null values (`{"sortino": null}`).
  - Standardized dictionary extraction (`_extract_list`) for `raw_values` array payloads.

### 2. Dynamic Real Trade Ledger Chart Calculation
- **`generate_charts_from_trades()`**: Dynamically computes all 4 chart series (`equity_curve`, `drawdown_curve`, `monthly_returns`, `rolling_metrics`) directly from PostgreSQL trade ledger rows (`backtests.<strategy_slug>`).
- **Baseline Start Date Padding**: Automatically prepends a 1-day prior start date (`2026-07-18`) so lightweight-charts always receives $\ge 2$ distinct date points even for single-day strategy runs.
- **Chart Component Scaling (`DrawdownChart.jsx`)**:
  - Added `autoscaleInfoProvider` expanding y-axis range from **-10.00%** to **+2.00%** when drawdown is 0%, ensuring zero-line visibility.
  - Added custom percentage formatter (`-0.74%`).

### 3. Trade Execution Ledger Table & Interactive Up/Down Sorting
- **Refactored Column Schema**: Removed artificial `#` (`BT_1`, `BT_2`) column. Added **`Exit Reason`** (`TAKE PROFIT`, `STOP LOSS`) and **`Status`** (`Completed`, `Ongoing`).
- **Interactive Up/Down Sorting (`TableSortLabel`)**:
  - Added clickable sort headers across all 9 table columns (`Entry Time`, `Exit Time`, `Side`, `Exit Reason`, `Status`, `Entry Price`, `Exit Price`, `Net PnL`, `Return %`).
  - Clicking any header toggles between **Ascending (Up arrow)** and **Descending (Down arrow)**.

### 4. Theme & Aesthetic Refinements
- **Topbar DB Active Status Badge**:
  - Styled `● DB Active` pill with the brand sidebar sage green theme (`#5E8B6E` / `#4A7A5A` in Light Mode, `#7DAD8C` in Dark Mode) and ambient green glow (`0 4px 14px rgba(94, 139, 110, 0.25)`).
- **Soft Eye-Friendly Matte Red Palette**:
  - Replaced bright neon red (`#F43F5E` / `#F6465D`) with soft matte crimson (`#EE5D5D`) across `pnlRed`, `StatusChip` (`Short`, `Failed`, `Stopped`, `Cancelled`, `Error`), negative PnL text, and chart lines to eliminate eye strain.

---

## System Architecture Summary

```
[ Vite React Frontend ] 
       │
       ▼ HTTP / REST API (port 8000)
[ FastAPI Backend Engine ] 
       │
       ├─► check_db_health() ──────────────► SELECT 1 Health Check
       ├─► get_all_backtests() ────────────► metadata.strategy_data + backtests.stats + metadata.backtest_data
       └─► get_backtest_by_id(id) ─────────► backtests.<strategy_slug> (Trade Ledger)
                                                  │
                                                  ▼
                                       generate_charts_from_trades()
                                                  │
                                                  ├─► equity_curve
                                                  ├─► drawdown_curve
                                                  ├─► monthly_returns
                                                  └─► rolling_metrics
```

---

## Dependencies & Stack

```json
{
  "frontend": {
    "react": "^18.x",
    "@mui/material": "^5.x",
    "@mui/icons-material": "^5.x",
    "recharts": "^2.x",
    "lightweight-charts": "^4.x",
    "react-router-dom": "^6.x"
  },
  "backend": {
    "fastapi": "^0.110.x",
    "uvicorn": "^0.28.x",
    "psycopg2-binary": "^2.9.x",
    "numpy": "^1.26.x",
    "pandas": "^2.2.x"
  }
}
```

---

*Last updated: July 2026 — Full FastAPI backend service connected, real PostgreSQL trade ledger charts active, interactive Up/Down table sorting live, and soft eye-friendly red theme deployed.*
