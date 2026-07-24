/**
 * backtestsApi.js
 * Mirrors: GET /backtests, GET /backtests/:id, POST /backtests
 * TODO(security): POST /backtests would need CSRF token when real API is wired.
 */
import { BACKTESTS, MARKET_DATA_OPTIONS } from '../mock/backtestsMock';
import { findMockById } from '../utils/findMockById';

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

let backtestStore = [...BACKTESTS];

function applyFilters(data, { search = '', filter = {}, sort = {} } = {}) {
  let result = [...data];
  if (search) {
    const q = search.toLowerCase();
    result = result.filter(
      (b) =>
        b.strategy_name.toLowerCase().includes(q) ||
        b.symbol.toLowerCase().includes(q),
    );
  }
  if (filter.status) result = result.filter((b) => b.status === filter.status);
  if (filter.exchange) result = result.filter((b) => b.exchange === filter.exchange);
  if (sort.field) {
    const dir = sort.dir === 'desc' ? -1 : 1;
    result.sort((a, b) => {
      if (a[sort.field] == null) return 1;
      if (b[sort.field] == null) return -1;
      return (a[sort.field] < b[sort.field] ? -1 : 1) * dir;
    });
  }
  return result;
}

/** GET /backtests */
export async function getBacktests({ search, filter, sort, page = 1, pageSize = 50 } = {}) {
  await delay(350 + Math.random() * 200);
  const filtered = applyFilters(backtestStore, { search, filter, sort });
  const start = (page - 1) * pageSize;
  return {
    data: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  };
}

/** GET /backtests/:id */
export async function getBacktestById(id) {
  await delay(300 + Math.random() * 150);
  const bt = findMockById(backtestStore, id, ['backtest_id']);
  if (!bt) throw new Error(`Backtest "${id}" not found`);
  return { ...bt };
}

/** POST /backtests — submit a new backtest request */
export async function submitBacktest(payload) {
  await delay(600 + Math.random() * 200);
  const newBt = {
    backtest_id: `bt-${Date.now()}`,
    ...payload,
    status: 'pending',
    submitted_at: new Date().toISOString(),
    completed_at: null,
    total_trades: null,
    win_rate: null,
    net_pnl: null,
    final_balance: null,
    sharpe: null,
    sortino: null,
    calmar: null,
    max_drawdown: null,
    cagr: null,
    equity_curve: [],
    drawdown_curve: [],
    monthly_returns: [],
    rolling_metrics: [],
    trades: [],
  };
  backtestStore = [...backtestStore, newBt];
  return { ...newBt };
}

/** GET /market-data — for symbol/timeframe pickers */
export async function getMarketDataOptions() {
  await delay(200);
  return { data: MARKET_DATA_OPTIONS, total: MARKET_DATA_OPTIONS.length, page: 1, pageSize: MARKET_DATA_OPTIONS.length };
}
