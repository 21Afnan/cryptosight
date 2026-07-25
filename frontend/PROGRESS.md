# CryptoSight Frontend — Progress & Architecture Log

## Status
All pages complete, restyled to soft fintech crystal glass aesthetic, lightweight-charts v5 compatible, with equal-sized cards, dynamic profit/loss indicators, full-width performance charts, and spec alignment.

## Recent Accomplishments & Redesign Highlights

- **Equal-Sized Metric Cards System**: Standardized all top summary cards and backtest metric flashcards to `minHeight: 110px` with uniform padding, clean 16px/20px border radius, and flexbox vertical centering across both light and dark modes.
- **Dynamic Profit (Green) / Loss (Red) Color Indicators**:
  - Net PnL (`+$` green, `-$` red)
  - CAGR (`>= 0.0%` green, `< 0.0%` red)
  - Win Rate (`>= 50.0%` green, `< 50.0%` red)
  - Sharpe Ratio (`>= 1.00` green, `< 1.00` red)
  - Sortino Ratio (`>= 1.00` green, `< 1.00` red)
  - Calmar Ratio (`>= 1.00` green, `< 1.00` red)
  - Max Drawdown (Always red decline indicator)
- **100% Full-Width Performance Charts**:
  - Dynamically calculates chart width from outer `.MuiCardContent-root` bounding container.
  - Equity Curve Trajectory and Underwater Drawdown stretch edge-to-edge with 0% right empty space.
  - Auto-fit resize observer handles window resizing and tab switching smoothly.
- **Backtest Configuration Parameter Pills**:
  - Formatted parameters into modern 12px rounded rectangles (`borderRadius: 2`).
  - Added subtle green box-shadows (`0 4px 18px rgba(34, 197, 94, 0.15)`) and borders.
- **Quick Strategy Presets**: Added quick pre-fill cards for `BTC EMA Cross 4H`, `ETH RSI Reversion 1H`, and `SOL Breakout 1D`.
- **Text & Emoji Cleanup**: Stripped out emojis and removed unnecessary title suffixes (`— Backtest Details`, `Vectorized Engine Run`, `Grade A+`) per user design directives.

---

## Completed Features Archive

- **Dashboard Card Removal**: Removed the `Strategies by Exchange` donut card from the Dashboard per user request, leaving a clean, full-width **Strategies Overview** table.
- **Universal Column Header Sorting & Top Clearance**: Added interactive `TableSortLabel` controls across ALL strategy list table headers (**Strategy**, **Symbol**, **Exchange**, **Timeframe**, **Status**, **Net PnL**, **Win Rate**, **Sharpe**, **Max DD**). Clicking any header sorts the table by that metric. Added top breathing space (`pt: '84px'`) across all pages in `PageContainer.jsx`.
- **Layout Expansion & PnL Filter Refinement**: Expanded Dashboard table grid width from 8 columns to **9 columns** (`lg={9}`) and donut widget to 3 columns (`lg={3}`), utilizing the full available screen width to prevent clipping.
- **Account Overview & Wallets Consolidation**: Consolidated the **Account Equity Growth Line Chart** and **Capital Allocation Donut Widget** directly into the **Wallets page** (`src/pages/Wallets/index.jsx`).
- **Global Table Pagination**: Integrated MUI `TablePagination` controls across all primary list tables (Wallets, Deployment, Machine Learning, Backtest Requests).
- **Functional Global Topbar Search**: Created `SearchContext` filtering the **Strategies Overview** table in real time.

---

## Known Issues / Outstanding Tasks
- None outstanding on frontend. All 10 routes render clean data in both dark and light modes.

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

*Last updated: July 2026 — Backtesting UI complete with equal-sized dynamic cards, 100% chart scaling, and clean theme styling.*
