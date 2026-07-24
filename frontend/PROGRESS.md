# CryptoSight Frontend — Progress & Architecture Log

## Status
All pages complete, restyled to soft fintech crystal glass aesthetic, lightweight-charts v5 compatible, and verified against PDF spec.

## Completed

- **Dashboard Card Removal**: Removed the `Strategies by Exchange` donut card from the Dashboard per user request, leaving a clean, full-width **Strategies Overview** table.
- **Universal Column Header Sorting & Top Clearance**: Added interactive `TableSortLabel` controls across ALL strategy list table headers (**Strategy**, **Symbol**, **Exchange**, **Timeframe**, **Status**, **Net PnL**, **Win Rate**, **Sharpe**, **Max DD**). Clicking any header sorts the table by that metric. Added top breathing space (`pt: '84px'`) across all pages in `PageContainer.jsx`.

- **Layout Expansion & PnL Filter Refinement**: Expanded Dashboard table grid width from 8 columns to **9 columns** (`lg={9}`) and donut widget to 3 columns (`lg={3}`), utilizing the full available screen width to prevent clipping. Removed the `Min Return %` text field per user request, keeping the clean **PnL / Return outcome dropdown** (`All PnL / Return`, `Profitable (> 0%)`, `High Return (> +10%)`, `Loss Only (< 0%)`) and interactive column header sorting (**Return**, **Sharpe**, **Win Rate**).
- **Account Overview & Wallets Consolidation**: Removed unrequested duplicate `/account` page and sidebar entry (resolving duplicate wallet icon clutter). Consolidated the **Account Equity Growth Line Chart** and **Capital Allocation Donut Widget** directly into the **Wallets page** (`src/pages/Wallets/index.jsx`) between the summary StatCards and the wallet list table.
- **Global Table Pagination**: Integrated MUI `TablePagination` controls (with 5, 10, 25 row options and default page size 10) across all primary list tables:
  - Wallets table (`src/pages/Wallets/index.jsx`)
  - Deployment table (`src/pages/Deployment/index.jsx`)
  - Machine Learning Models table (`src/pages/MachineLearning/index.jsx`)
  - Backtest Requests table (`src/pages/BacktestRequests/index.jsx`)
- **Functional Global Topbar Search**: Created `SearchContext` and wrapped the application tree. Wired `InputBase` in `Topbar.jsx` to publish search queries that dynamically filter the **Strategies Overview** table on the Dashboard in real time.

- **Chart Watermark & Sizing Fix (Shared Chart Wrappers)**: Applied `attributionLogo: false`, initial container width (`clientWidth || 320`), `scaleMargins: { top: 0.15, bottom: 0.15 }`, and `priceFormat: { precision: 0 }` across `EquityCurveChart`, `DrawdownChart`, `PriceChart`, and `TradeHistoryChart`. Bumped compact chart card heights (`Position Size`, `Trade History`, `Monthly Returns`, `Rolling Metrics`) to `270px–280px`.
- **Topbar Title Redesign**: Removed white pill badge wrapper around Topbar page title. Rendered title text directly on translucent glass topbar with `fontSize: 1.25rem`, `fontWeight: 800`, and glowing text-shadow drop shadow on hover.
- **Model Details Visuals**: Added radial SVG score & confidence progress gauges, Recharts horizontal bar chart plotting 0–1 evaluation metrics (Accuracy, Precision, Recall, F1, AUC-ROC), and color-coded Sharpe Ratio pills. Cleaned up dead imports.
- **Wallets Drawer Visual Hierarchy**: Built reusable `WalletDetailRow` card components with section icons (`ShowChartRoundedIcon`, `SwapHorizRoundedIcon`, `ReceiptLongRoundedIcon`, `RocketLaunchRoundedIcon`), status badges, and subtle hover card backgrounds.
- **Strategy Filter Bar (`StrategyFilterBar.jsx`)**: Built dedicated filter controls for strategy tables (Strategy Name/Symbol search input, Exchange filter, Status filter, and Timeframe TF dropdown). Integrated directly onto the Dashboard "Strategies Overview" table and the Strategy List page (`/strategies`).
- **Full Lightweight-Charts v5 Compatibility**: Resolved `chart.addLineSeries is not a function` and `chart.addCandlestickSeries` by updating `TradeHistoryChart.jsx` and `PriceChart.jsx` to use `chart.addSeries(LineSeries, options)` and `chart.addSeries(CandlestickSeries, options)`. All detail pages (`/deployment/:id`, `/strategies/:id`, `/backtests/:id`) load smoothly without chart errors.
- **Enhanced Trade Ledger Filters (`LedgerFilterBar.jsx`)**: Added Start Time & End Time pickers, PnL Outcome dropdown (Profitable `> $0` vs Loss `< $0`), Min PnL & Max PnL range inputs, Side selector, and Symbol search. Integrated across Execution Details, Strategy Details, and Backtest Details tables.

- **Full Lightweight-Charts v5 Compatibility**: Resolved `chart.addLineSeries is not a function` and `chart.addCandlestickSeries` by updating `TradeHistoryChart.jsx` and `PriceChart.jsx` to use `chart.addSeries(LineSeries, options)` and `chart.addSeries(CandlestickSeries, options)`. All detail pages (`/deployment/:id`, `/strategies/:id`, `/backtests/:id`) load smoothly without chart errors.
- **Enhanced Trade Ledger Filters (`LedgerFilterBar.jsx`)**: Added Start Time & End Time pickers, PnL Outcome dropdown (Profitable `> $0` vs Loss `< $0`), Min PnL & Max PnL range inputs, Side selector, and Symbol search. Integrated across Execution Details, Strategy Details, and Backtest Details tables.

- **Sentiment Page Chart Expansion**: Removed squished "Fear & Greed (90d)" chart card. Expanded top row cards to a balanced 4-column layout (`md={4}` each) for the Fear & Greed Gauge, Market Overview, and Sentiment Distribution Pie Chart. Expanded pie outer radius (`105px`) and overall timeline/news chart heights (`280px` / `260px`).
- **Sage Green 3D Crystal Glass Topbar (Image 1 Style)**: Implemented sage green translucent glass navbar with 3D top specular border highlight. Pure white rounded pill page title badge that scales up and glows with a green drop shadow on hover. Pill search bar with right-aligned search icon matching Image 1.
- **Circular Score Gauge Widget (Image 2 Style)**: Redesigned `SentimentGauge.jsx` with circular green gradient progress arc, central bold score (`68 PREDICTED`), soft sage green radial glow background, and smooth hover scale bigger animation with glowing green drop shadow.
- **Lightweight-Charts v5 Compatibility Fix**: Fixed `chart.addAreaSeries is not a function` error across `EquityCurveChart.jsx` and `DrawdownChart.jsx` by supporting `chart.addSeries(AreaSeries, options)` syntax.

- **Sage Green 3D Crystal Glass Topbar (Image 1 Style)**: Implemented sage green translucent glass navbar with 3D top specular border highlight. Pure white rounded pill page title badge that scales up and glows with a green drop shadow on hover. Pill search bar with right-aligned search icon matching Image 1.
- **Circular Score Gauge Widget (Image 2 Style)**: Redesigned `SentimentGauge.jsx` with circular green gradient progress arc, central bold score (`68 PREDICTED`), soft sage green radial glow background, and smooth hover scale bigger animation with glowing green drop shadow.
- **Lightweight-Charts v5 Compatibility Fix**: Fixed `chart.addAreaSeries is not a function` error across `EquityCurveChart.jsx` and `DrawdownChart.jsx` by supporting `chart.addSeries(AreaSeries, options)` syntax.
- **Dynamic Responsive Layout & Sidebar Collapse Context**: Created `SidebarContext` (`src/context/SidebarContext.jsx`). Synchronized `Sidebar.jsx`, `Topbar.jsx`, and `PageContainer.jsx` so collapsing/expanding the sidebar dynamically resizes topbar width (`left: 76px` vs `240px`) and page content margin with zero empty gap.

- **Lightweight-Charts v5 Compatibility Fix**: Fixed `chart.addAreaSeries is not a function` error across `EquityCurveChart.jsx` and `DrawdownChart.jsx` by supporting `chart.addSeries(AreaSeries, options)` syntax.
- **Dynamic Responsive Layout & Sidebar Collapse Context**: Created `SidebarContext` (`src/context/SidebarContext.jsx`). Synchronized `Sidebar.jsx`, `Topbar.jsx`, and `PageContainer.jsx` so collapsing/expanding the sidebar dynamically resizes topbar width (`left: 76px` vs `240px`) and page content margin with zero empty gap.
- **Account Overview Page (`/account`)**: Added dedicated Accounts Overview page featuring StatCards with 3D hover effects, combined Account Equity Growth graph, Account Capital Allocation donut chart, and an Accounts & Active Running Strategies table showing which strategies are running on each exchange account.

- **Account Overview Page (`/account`)**: Added dedicated Accounts Overview page featuring StatCards with 3D hover effects, combined Account Equity Growth graph, Account Capital Allocation donut chart, and an Accounts & Active Running Strategies table showing which strategies are running on each exchange account.
- **Crystal Glass Topbar (`Topbar.jsx`)**: Implemented transparent crystal glass panel (`backdropFilter: 'blur(24px) saturate(190%)'`), removed CryptoSight subtitle, and styled page titles inside elevated crystal badges with hover color glow and drop shadows.
- **Dashboard Equal-Sized StatCards Grid**: Converted Dashboard StatCards container to a 5-column CSS grid so all flashcards are 100% equal in width, height, and alignment.
- **Dashboard Piechart Layout Fix**: Adjusted layout columns to 8:4 ratio to give the Portfolio Allocation donut chart ample space without clipping.
- **Global Error Boundary & ID Lookup Fix**: Fixed parameter mutation in `findMockById.js` and added `ErrorBoundary.jsx` around application routes to prevent blank white page crashes.

### Session 1 — Green Scaffolding & Initial Build
- Created React 18 + Vite scaffolding.
- Defined base MUI theme, dark/light mode toggle.
- Created `useMockFetch` hook for async simulated API responses.
- Implemented 6 UI primitives (`StatusChip`, `StatCard`, `EmptyState`, `LoadingSkeleton`, `ConfirmDialog`, `SearchBar`).
- Created 14 chart components using `lightweight-charts` & `recharts`.
- Created 7 mock data files matching PostgreSQL schema.
- Created 7 API simulation modules (`dashboardApi`, `strategiesApi`, `walletsApi`, `deploymentApi`, `backtestsApi`, `mlApi`, `sentimentApi`).
- Built all 10 pages: Dashboard, Strategy Details, Wallets, Deployment, Execution Details, Backtest Requests, Backtest Details, Machine Learning, Model Details, Sentiment.

### Session 2 — Soft Fintech Redesign Pass
- Rewrote `theme.js`: Sage green accent (`#5E8B6E`), warm off-white background (`#F4F7F4`), shadow-only borderless cards (`20px` radius), pill buttons (`999px` radius), distinct PnL green (`#22C55E`) and red (`#F43F5E`).
- Restyled `Sidebar.jsx` with solid sage green background & inverted white pill for active route.
- Restyled `Topbar.jsx` with pill search bar and theme toggle button.
- Restyled `StatCard.jsx` with pastel icon bubble backgrounds cycling through colors.
- Created `AllocationDonut.jsx` and added Hero Banner + Donut widget to Dashboard.
- Restyled `StatusChip.jsx` to soft filled pills with glowing status dots.

### Session 3 — Polish, Bug Fixes & Completeness
- Created `src/utils/findMockById.js` for safe type-coerced ID lookup across all detail routes. Fixed blank white page on `/backtests/:id`.
- Added `AddWalletDialog` to Wallets page allowing users to add new exchange wallets in-memory.
- Removed plain-text API key display from Wallet drawer summary view per spec.
- Added top summary `StatCard` row to Wallets page (Total Balance, Active Wallets, Unrealized PnL, Total PnL).
- Created `LedgerFilterBar.jsx` for interactive filtering (date range, side, symbol) on all trade ledger tables.
- Added page title & breadcrumbs to Topbar and restyled Topbar background to translucent sage glass (`backdropFilter: blur`).
- Removed broken Feature Importance chart from Model Details per PDF spec alignment.
- Fixed Fear & Greed (90d) timeline chart and verified News Sentiment — Per Symbol table rendering.

---

## Known Issues / Not Yet Fixed
- None currently outstanding. All 10 routes render clean data in both dark and light modes.

---

## Deviations from Spec
1. **API Key Masking**: Plaintext API keys removed from summary drawer view per security & UX guidelines. Key fields only belong in credentials entry/edit forms.
2. **Feature Importance Chart**: Excluded from Model Details page per PDF spec alignment (PDF spec lists Dataset Info, Training Config, Evaluation Metrics, Hyperparameters, and Backtest Metrics only).

---

## Architecture Notes

### Shared Utilities
- `src/utils/findMockById.js`: Safe ID lookup coercing string/number differences between route params and mock data schemas.
- `src/hooks/useMockFetch.js`: Standardized async fetch wrapper managing `loading`, `error`, `data`, and `refetch`.
- `src/theme/theme.js`: Exports `darkTheme`, `lightTheme`, `COLORS`, `GRADIENTS`, `ICON_BUBBLE_COLORS`.
- `src/components/ui/LedgerFilterBar.jsx`: Reusable trade table filter bar for date ranges, side selection, and symbol search.

### Data Layer
- All REST API endpoints in `src/api/*.js` return Promises wrapping mock objects from `src/mock/*.js`.
- Swapping to a real FastAPI backend only requires changing the fetch implementation inside `src/api/*.js`.
