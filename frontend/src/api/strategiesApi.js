import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

function applyFilters(data, { search = '', filter = {}, sort = {} } = {}) {
  let result = [...data];
  if (search) {
    const q = search.toLowerCase();
    result = result.filter(
      (s) =>
        (s.strategy_name || s.name || '').toLowerCase().includes(q) ||
        (s.symbol || '').toLowerCase().includes(q) ||
        (s.exchange || '').toLowerCase().includes(q),
    );
  }
  if (filter.status) result = result.filter((s) => s.status === filter.status);
  if (filter.exchange) result = result.filter((s) => s.exchange === filter.exchange);
  if (sort.field) {
    const dir = sort.dir === 'desc' ? -1 : 1;
    result.sort((a, b) => {
      if (a[sort.field] < b[sort.field]) return -1 * dir;
      if (a[sort.field] > b[sort.field]) return 1 * dir;
      return 0;
    });
  }
  return result;
}

/** GET /strategies — real database strategies list */
export async function getStrategies({ search, filter, sort, page = 1, pageSize = 50 } = {}) {
  const res = await axios.get(`${API_BASE_URL}/strategies`);
  const rawData = Array.isArray(res.data) ? res.data : [];

  const list = rawData.map((item) => ({
    strategy_id: item.id || item.strategy_id,
    strategy_name: item.name || item.strategy_name,
    exchange: item.exchange,
    symbol: item.symbol,
    target_timeframe: item.timeframe || item.target_timeframe,
    status: item.status || 'active',
    total_trades: item.total_trades || 0,
    win_rate: item.win_rate || 0,
    net_pnl: item.net_pnl || 0,
    latest_return: item.latest_return || 0,
    sharpe: item.sharpe != null ? Number(item.sharpe) : null,
    charts: item.charts || null,
  }));

  const filtered = applyFilters(list, { search, filter, sort });
  const start = (page - 1) * pageSize;
  return {
    data: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  };
}

/** GET /strategies/:id — fetches Performance Summary, Configuration, & Risk Management from DB */
export async function getStrategyById(id) {
  const res = await axios.get(`${API_BASE_URL}/strategies/${id}`);
  if (res.data && !res.data.error) {
    return {
      strategy_id: res.data.strategy_id,
      strategy_name: res.data.strategy_name,
      exchange: res.data.exchange,
      symbol: res.data.symbol,
      target_timeframe: res.data.target_timeframe,
      status: res.data.status,
      performance: res.data.performance,
      configuration: res.data.configuration,
      risk_management: res.data.risk_management,
      equity_curve: res.data.equity_curve,
      drawdown_curve: res.data.drawdown_curve,
      monthly_returns: res.data.monthly_returns,
      trade_distribution: res.data.trade_distribution,
      charts: res.data.charts || null,
    };
  }
  throw new Error(`Strategy details not found for ${id}`);
}

/** GET /strategies/:name/trades — real trade ledgers from simulation_ledgers table */
export async function getStrategyTrades(id, { page = 1, pageSize = 20 } = {}) {
  let stratName = String(id);
  try {
    const stratObj = await getStrategyById(id);
    if (stratObj && stratObj.strategy_name) {
      stratName = stratObj.strategy_name;
    }
  } catch (e) {
    // Keep raw id
  }

  const res = await axios.get(`${API_BASE_URL}/strategies/${encodeURIComponent(stratName)}/ledgers`);
  const trades = Array.isArray(res.data) ? res.data : [];
  const start = (page - 1) * pageSize;
  return { data: trades.slice(start, start + pageSize), total: trades.length, page, pageSize };
}
