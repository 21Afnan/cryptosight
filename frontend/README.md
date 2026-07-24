# CryptoSight Frontend

A production-grade quantitative crypto trading dashboard built with **React 18 + Vite + MUI**.  
Design philosophy: Bloomberg Terminal aesthetics — data-dense, dark-first, unmistakably a trading terminal.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | React 18 + Vite |
| UI Library | MUI v5 (Material-UI) |
| Charts | `lightweight-charts` (OHLC/equity/drawdown) + `recharts` (bars/distributions/sparklines) |
| Routing | react-router-dom v6 |
| State | React Context (theme only) + page-local `useMockFetch` hook |
| Styling | MUI `sx` prop + custom theme overrides (no TailwindCSS) |
| Fonts | Inter (Google Fonts, loaded via index.html) |

---

## Quick Start

```bash
cd d:\Neurog_Internship\cryptosight\frontend
npm install
npm run dev       # → localhost:5173
npm run build     # production bundle check
```

---

## Build Status

### ✅ Completed

| Layer | Files | Status |
|---|---|---|
| Scaffold & Config | `index.html`, `vite.config.js`, `package.json` | ✅ |
| Theme | `src/theme/theme.js` | ✅ |
| Hook | `src/hooks/useMockFetch.js` | ✅ |
| UI primitives | `StatusChip`, `StatCard`, `EmptyState`, `LoadingSkeleton`, `ConfirmDialog`, `SearchBar` | ✅ |
| Layout | `Sidebar`, `Topbar`, `PageContainer` | ✅ |
| Charts (14) | `PriceChart`, `EquityCurveChart`, `DrawdownChart`, `SparklineChart`, `DistributionChart`, `MonthlyReturnsChart`, `PositionSizeChart`, `DailyReturnsChart`, `TradeHistoryChart`, `RollingMetricsChart`, `SentimentGauge`, `SentimentTimelineChart`, `NewsVolumeChart`, `NewsSentimentChart` | ✅ |
| Mock Data (7) | `dashboardMock`, `strategiesMock`, `walletsMock`, `deploymentMock`, `backtestsMock`, `mlMock`, `sentimentMock` | ✅ |
| API Layer (7) | `dashboardApi`, `strategiesApi`, `walletsApi`, `deploymentApi`, `backtestsApi`, `mlApi`, `sentimentApi` | ✅ |
| App Shell | `App.jsx`, `main.jsx`, `index.css` | ✅ |
| Pages (10) | Dashboard, StrategyDetails, Wallets, Deployment, ExecutionDetails, BacktestRequests, BacktestDetails, MachineLearning, ModelDetails, Sentiment | ✅ |

---

## Folder Structure

```
frontend/src/
├── api/                  # Async API functions (swap body for real FastAPI later)
│   ├── dashboardApi.js
│   ├── strategiesApi.js
│   ├── walletsApi.js
│   ├── deploymentApi.js
│   ├── backtestsApi.js
│   ├── mlApi.js
│   └── sentimentApi.js
├── mock/                 # Raw mock data — field names mirror PostgreSQL schema
│   ├── dashboardMock.js
│   ├── strategiesMock.js
│   ├── walletsMock.js
│   ├── deploymentMock.js
│   ├── backtestsMock.js
│   ├── mlMock.js
│   └── sentimentMock.js
├── theme/
│   └── theme.js          # darkTheme, lightTheme, COLORS, GRADIENTS
├── hooks/
│   └── useMockFetch.js   # { data, loading, error, refetch }
├── components/
│   ├── layout/           # Sidebar, Topbar, PageContainer
│   ├── ui/               # StatusChip, StatCard, EmptyState, LoadingSkeleton, ConfirmDialog, SearchBar
│   └── charts/           # 14 chart components
└── pages/
    ├── Dashboard/
    ├── StrategyDetails/
    ├── Wallets/
    ├── Deployment/
    ├── ExecutionDetails/
    ├── BacktestRequests/
    ├── BacktestDetails/
    ├── MachineLearning/
    ├── ModelDetails/
    └── Sentiment/
```

---

## Routes

| Path | Page | Notes |
|---|---|---|
| `/` | Dashboard | 10 KPI cards + strategies table |
| `/strategies` | Strategy List | All strategies table |
| `/strategies/:id` | Strategy Details | Config + charts + trades |
| `/wallets` | Wallet Management | CRUD + drawer with 4 sections |
| `/deployment` | Deployment | Active executions table |
| `/deployment/:id` | Execution Details | Position + 4 charts + signal history |
| `/backtests` | Backtest Requests | Config form + 5-tab status list |
| `/backtests/:id` | Backtest Details | Full stats + 4 charts + trade list |
| `/ml` | Machine Learning | Models table |
| `/ml/:id` | Model Details | Dataset info + training + feature importance |
| `/sentiment` | Sentiment | Fear & Greed + 6 charts + symbol table |

---

## Design System

### Colors (`COLORS` export from theme.js)

| Token | Value | Use |
|---|---|---|
| `accent` | `#38BDF8` | Brand, active states, links |
| `pnlGreen` | `#16C784` | Profit, long, bullish |
| `pnlRed` | `#EA3943` | Loss, short, bearish |
| `warning` | `#F0B90B` | Pending, paused, neutral sentiment |
| `darkBg` | `#0A0B0F` | Page background (dark) |
| `lightBg` | `#F8F9FB` | Page background (light) |

### Theme Toggle
- Stored in `localStorage` key `cryptosight_theme`
- Toggle button in Topbar (top-right)
- ThemeContext wraps the entire app via `App.jsx`

---

## Security Notes

- ✅ No `dangerouslySetInnerHTML` used anywhere  
- ✅ API keys always masked (`****...XXXX`) — never stored/displayed in full  
- ✅ No `console.log` of financial data  
- ✅ No real network calls — all data is in-memory mock  
- ✅ React JSX auto-escaping enforced throughout  
- `TODO(security)` markers in: `walletsApi.js`, `backtestsApi.js`, `useMockFetch.js`  

---

## Connecting to Real FastAPI Backend

When the backend is ready:  
1. Replace the `import` + `delay()` body in each `src/api/*.js` file with `axios.get('/api/...')` calls  
2. Ensure all responses match the same paginated shape: `{ data: [...], total, page, pageSize }`  
3. The mock files in `src/mock/` can be kept as test fixtures  
4. Add HTTPS enforcement, CSRF tokens, and auth headers as noted in TODO(security) markers  

---

## Dependencies

```json
{
  "@mui/material": "^5.x",
  "@mui/icons-material": "^5.x",
  "@emotion/react": "^11.x",
  "@emotion/styled": "^11.x",
  "recharts": "^2.x",
  "lightweight-charts": "^4.x",
  "react-router-dom": "^6.x"
}
```

---

*Last updated: 2025-07-24 — All 10 pages and full data layer complete.*
