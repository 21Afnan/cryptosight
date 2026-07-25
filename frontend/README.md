# CryptoSight Frontend

A production-grade quantitative crypto trading dashboard built with **React 18 + Vite + MUI**.  
Design philosophy: Bloomberg Terminal aesthetics — data-dense, dark-first, unmistakably a trading terminal with soft fintech crystal glass styling.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | React 18 + Vite |
| UI Library | MUI v5 (Material-UI) |
| Charts | `lightweight-charts` (OHLC/equity/drawdown) + `recharts` (bars/distributions/sparklines) |
| Routing | react-router-dom v6 |
| State | React Context (theme & sidebar) + page-local `useMockFetch` hook |
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
| Hooks & Context | `src/hooks/useMockFetch.js`, `SidebarContext.jsx`, `SearchContext.jsx` | ✅ |
| UI primitives | `StatusChip`, `StatCard`, `EmptyState`, `LoadingSkeleton`, `ConfirmDialog`, `SearchBar`, `LedgerFilterBar` | ✅ |
| Layout | `Sidebar`, `Topbar`, `PageContainer` | ✅ |
| Charts (14) | `PriceChart`, `EquityCurveChart`, `DrawdownChart`, `SparklineChart`, `DistributionChart`, `MonthlyReturnsChart`, `PositionSizeChart`, `DailyReturnsChart`, `TradeHistoryChart`, `RollingMetricsChart`, `SentimentGauge`, `SentimentTimelineChart`, `NewsVolumeChart`, `NewsSentimentChart` | ✅ |
| Mock Data (7) | `dashboardMock`, `strategiesMock`, `walletsMock`, `deploymentMock`, `backtestsMock`, `mlMock`, `sentimentMock` | ✅ |
| API Layer (7) | `dashboardApi`, `strategiesApi`, `walletsApi`, `deploymentApi`, `backtestsApi`, `mlApi`, `sentimentApi` | ✅ |
| App Shell | `App.jsx`, `main.jsx`, `index.css` | ✅ |
| Pages (10) | Dashboard, StrategyDetails, Wallets, Deployment, ExecutionDetails, BacktestRequests, BacktestDetails, MachineLearning, ModelDetails, Sentiment | ✅ |

---

## Recent Highlights

- 🟩 **Dynamic Profit/Loss Color Engine**: Cards dynamically render in Green (`#0ECB81`) for profit/healthy metrics (PnL `> $0`, Win Rate `≥ 50%`, Sharpe `≥ 1.0`, Sortino `≥ 1.0`, Calmar `≥ 1.0`) and Red (`#F6465D`) for loss/unhealthy metrics.
- 📐 **Equal-Sized Cards Grid**: All metric flashcards have fixed `minHeight: 110px`, equal flexbox alignment, and uniform border radius across both light and dark modes.
- 📈 **100% Full-Width Charts**: Equity Curve & Drawdown charts dynamically compute parent bounding box width, filling 100% of available card space.

---

## Folder Structure

```
frontend/src/
├── api/                  # Async API functions (ready for FastAPI integration)
│   ├── dashboardApi.js
│   ├── strategiesApi.js
│   ├── walletsApi.js
│   ├── deploymentApi.js
│   ├── backtestsApi.js
│   ├── mlApi.js
│   └── sentimentApi.js
├── mock/                 # Raw mock data — field names mirror PostgreSQL schema
├── theme/                # darkTheme, lightTheme, COLORS, GRADIENTS
├── hooks/                # useMockFetch ({ data, loading, error, refetch })
├── components/
│   ├── layout/           # Sidebar, Topbar, PageContainer
│   ├── ui/               # StatusChip, StatCard, EmptyState, LoadingSkeleton, ConfirmDialog, SearchBar, LedgerFilterBar
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
| `/backtests` | Backtest Requests | Presets + Config form + status catalog |
| `/backtests/:id` | Backtest Details | 8 equal dynamic cards + full-width charts + ledger |
| `/ml` | Machine Learning | Models table |
| `/ml/:id` | Model Details | Dataset info + training + evaluation metrics |
| `/sentiment` | Sentiment | Fear & Greed + 6 charts + symbol table |

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

*Last updated: July 2026 — All 10 pages, equal-sized dynamic cards, 100% chart scaling, and full data layer complete.*
