/**
 * backtestsApi.js
 * FastAPI Backend integrated API client for /api/v1/backtests and DB connection health.
 * Communicates directly with http://localhost:8000/api/v1/backtests
 */

const BASE_URL = 'http://localhost:8000/api/v1/backtests';

/** GET /api/v1/backtests/health — Real PostgreSQL DB Connection Health Status Indicator */
export async function getDbHealth() {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    return { status: 'inactive', connected: false, error: err.message };
  }
}

/** GET /api/v1/backtests — Fetch backtest list from FastAPI backend service */
export async function getBacktests({ search = '', filter = {}, sort = {}, page = 1, pageSize = 50 } = {}) {
  const queryParams = new URLSearchParams();
  if (search) queryParams.append('search', search);
  if (filter.status) queryParams.append('status', filter.status);

  const res = await fetch(`${BASE_URL}?${queryParams.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch backtests from backend service: ${res.statusText}`);
  }
  const json = await res.json();
  return {
    data: json.data || [],
    total: json.count || json.data?.length || 0,
    page,
    pageSize,
  };
}

/** GET /api/v1/backtests/:id — Fetch backtest details from FastAPI backend service */
export async function getBacktestById(id) {
  const res = await fetch(`${BASE_URL}/${id}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch backtest details for "${id}" from backend service: ${res.statusText}`);
  }
  const json = await res.json();
  return json.data;
}

/** GET /market-data — 8 Standard Configured Trading Pairs */
export async function getMarketDataOptions() {
  return {
    data: [
      { exchange: 'Binance', symbol: 'BTC/USDT', timeframe: '1m' },
      { exchange: 'Bybit', symbol: 'ETH/USDT', timeframe: '1m' },
      { exchange: 'Binance', symbol: 'SOL/USDT', timeframe: '1m' },
      { exchange: 'Bybit', symbol: 'LTC/USDT', timeframe: '1m' },
      { exchange: 'Binance', symbol: 'DOGE/USDT', timeframe: '1m' },
      { exchange: 'Bybit', symbol: 'MINA/USDT', timeframe: '1m' },
      { exchange: 'Binance', symbol: 'SUI/USDT', timeframe: '1m' },
      { exchange: 'Bybit', symbol: 'ADA/USDT', timeframe: '1m' },
    ],
    total: 8,
    page: 1,
    pageSize: 8,
  };
}
