/**
 * backtestsMock.js
 * Mirrors: metadata.backtest_data, backtests.<strategy_name> ledgers
 * Includes all 4 status states: pending, running, completed, failed
 */

function generateBacktestEquity(days = 120, startBalance = 10000) {
  const data = [];
  let value = startBalance;
  let date = new Date('2024-01-01');
  for (let i = 0; i < days; i++) {
    value *= 1 + (Math.random() - 0.43) * 0.02;
    value = Math.max(value, startBalance * 0.6);
    data.push({ time: date.toISOString().split('T')[0], value: parseFloat(value.toFixed(2)) });
    date.setDate(date.getDate() + 1);
  }
  return data;
}

function generateBacktestDrawdown(days = 120) {
  const data = [];
  let dd = 0;
  let date = new Date('2024-01-01');
  for (let i = 0; i < days; i++) {
    dd += (Math.random() - 0.58) * 0.01;
    dd = Math.max(-0.4, Math.min(0, dd));
    data.push({ time: date.toISOString().split('T')[0], value: parseFloat(dd.toFixed(4)) });
    date.setDate(date.getDate() + 1);
  }
  return data;
}

function generateRollingMetrics(days = 120) {
  const data = [];
  let date = new Date('2024-01-01');
  let sharpe = 1.0, sortino = 1.2, calmar = 0.8;
  for (let i = 0; i < days; i++) {
    sharpe += (Math.random() - 0.48) * 0.12;
    sortino += (Math.random() - 0.48) * 0.15;
    calmar += (Math.random() - 0.5) * 0.08;
    sharpe = Math.max(-0.5, Math.min(3.5, sharpe));
    sortino = Math.max(-0.5, Math.min(4.5, sortino));
    calmar = Math.max(-1, Math.min(3, calmar));
    data.push({
      date: date.toISOString().split('T')[0],
      sharpe: parseFloat(sharpe.toFixed(3)),
      sortino: parseFloat(sortino.toFixed(3)),
      calmar: parseFloat(calmar.toFixed(3)),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
}

function generateBacktestTrades(count = 40, strategyName = 'BTC_EMA_Cross_4H') {
  const trades = [];
  let entryTime = new Date('2024-01-15T00:00:00Z');
  for (let i = 0; i < count; i++) {
    const side = Math.random() > 0.6 ? 'long' : 'short';
    const entryPrice = 38000 + Math.random() * 28000;
    const pct = (Math.random() - 0.4) * 0.07;
    const exitPrice = entryPrice * (1 + (side === 'long' ? pct : -pct));
    const size = 400 + Math.random() * 1600;
    const grossPnl = (exitPrice - entryPrice) * (size / entryPrice) * (side === 'long' ? 1 : -1);
    const fees = size * 0.001;
    const netPnl = grossPnl - fees;
    const exitTime = new Date(entryTime.getTime() + (1 + Math.random() * 12) * 3600000);
    trades.push({
      trade_id: i + 1,
      strategy_name: strategyName,
      entry_time: entryTime.toISOString(),
      exit_time: exitTime.toISOString(),
      side,
      entry_price: parseFloat(entryPrice.toFixed(2)),
      exit_price: parseFloat(exitPrice.toFixed(2)),
      position_size: parseFloat(size.toFixed(2)),
      gross_pnl: parseFloat(grossPnl.toFixed(2)),
      net_pnl: parseFloat(netPnl.toFixed(2)),
      fees: parseFloat(fees.toFixed(2)),
      return_pct: parseFloat(((netPnl / size) * 100).toFixed(3)),
    });
    entryTime = new Date(exitTime.getTime() + Math.random() * 72 * 3600000);
  }
  return trades.sort((a, b) => new Date(b.entry_time) - new Date(a.entry_time));
}

function generateMonthlyReturns(months = 12) {
  const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return Array.from({ length: months }, (_, i) => ({
    month: `${labels[i % 12]} ${i < 12 ? '24' : '25'}`,
    value: parseFloat(((Math.random() - 0.38) * 0.14).toFixed(4)),
  }));
}

export const BACKTESTS = [
  {
    backtest_id: 'bt-001',
    strategy_id: 1,
    strategy_name: 'BTC_EMA_Cross_4H',
    symbol: 'BTCUSDT',
    exchange: 'Binance',
    timeframe: '4h',
    // backtest_config (metadata.backtest_data)
    backtest_config: {
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      initial_balance: 10000,
      commission: 0.0005,
      slippage: 0.0002,
      take_profit: 0.045,
      stop_loss: 0.02,
    },
    status: 'completed',
    submitted_at: '2025-07-01T08:00:00Z',
    completed_at: '2025-07-01T08:04:12Z',
    // metadata.backtest_data result fields
    total_trades: 137,
    win_rate: 0.614,
    net_pnl: 4820.50,
    final_balance: 14820.50,
    sharpe: 1.84,
    sortino: 2.31,
    calmar: 1.12,
    max_drawdown: -0.183,
    cagr: 0.287,
    profit_factor: 1.72,
    avg_trade_pnl: 35.18,
    avg_win: 142.30,
    avg_loss: -64.70,
    max_consecutive_wins: 8,
    max_consecutive_losses: 3,
    // Chart data (backtests.<strategy_name> shape)
    equity_curve: generateBacktestEquity(365, 10000),
    drawdown_curve: generateBacktestDrawdown(365),
    monthly_returns: generateMonthlyReturns(12),
    rolling_metrics: generateRollingMetrics(365),
    trades: generateBacktestTrades(137, 'BTC_EMA_Cross_4H'),
  },
  {
    backtest_id: 'bt-002',
    strategy_id: 2,
    strategy_name: 'ETH_RSI_Divergence_1H',
    symbol: 'ETHUSDT',
    exchange: 'Bybit',
    timeframe: '1h',
    backtest_config: {
      start_date: '2024-03-01',
      end_date: '2024-12-31',
      initial_balance: 10000,
      commission: 0.0006,
      slippage: 0.0002,
      take_profit: 0.03,
      stop_loss: 0.015,
    },
    status: 'completed',
    submitted_at: '2025-07-01T07:30:00Z',
    completed_at: '2025-07-01T07:37:44Z',
    total_trades: 318,
    win_rate: 0.553,
    net_pnl: 2340.80,
    final_balance: 12340.80,
    sharpe: 1.42,
    sortino: 1.78,
    calmar: 0.89,
    max_drawdown: -0.241,
    cagr: 0.198,
    profit_factor: 1.41,
    avg_trade_pnl: 7.36,
    avg_win: 64.20,
    avg_loss: -52.10,
    max_consecutive_wins: 6,
    max_consecutive_losses: 5,
    equity_curve: generateBacktestEquity(306, 10000),
    drawdown_curve: generateBacktestDrawdown(306),
    monthly_returns: generateMonthlyReturns(10),
    rolling_metrics: generateRollingMetrics(306),
    trades: generateBacktestTrades(318, 'ETH_RSI_Divergence_1H'),
  },
  {
    backtest_id: 'bt-003',
    strategy_id: 3,
    strategy_name: 'SOL_Momentum_15M',
    symbol: 'SOLUSDT',
    exchange: 'Binance',
    timeframe: '15m',
    backtest_config: {
      start_date: '2025-01-01',
      end_date: '2025-07-01',
      initial_balance: 10000,
      commission: 0.0005,
      slippage: 0.0003,
      take_profit: 0.025,
      stop_loss: 0.012,
    },
    status: 'running',
    submitted_at: '2025-07-01T10:00:00Z',
    completed_at: null,
    progress: 0.63,
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
  },
  {
    backtest_id: 'bt-004',
    strategy_id: 5,
    strategy_name: 'AVAX_Triple_MA_2H',
    symbol: 'AVAXUSDT',
    exchange: 'Bybit',
    timeframe: '2h',
    backtest_config: {
      start_date: '2024-05-01',
      end_date: '2025-07-01',
      initial_balance: 10000,
      commission: 0.0006,
      slippage: 0.0003,
      take_profit: 0.035,
      stop_loss: 0.018,
    },
    status: 'pending',
    submitted_at: '2025-07-01T10:30:00Z',
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
  },
  {
    backtest_id: 'bt-005',
    strategy_id: 7,
    strategy_name: 'DOGE_Volume_Breakout_1H',
    symbol: 'DOGEUSDT',
    exchange: 'Bybit',
    timeframe: '1h',
    backtest_config: {
      start_date: '2024-07-01',
      end_date: '2024-12-31',
      initial_balance: 10000,
      commission: 0.0006,
      slippage: 0.0003,
      take_profit: 0.05,
      stop_loss: 0.025,
    },
    status: 'failed',
    submitted_at: '2025-07-01T09:00:00Z',
    completed_at: '2025-07-01T09:00:48Z',
    error_message: 'Insufficient signal data: only 12 bars matched conditions (minimum 30 required).',
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
  },
];

// Market data options (metadata.market_data) for form pickers
export const MARKET_DATA_OPTIONS = [
  { exchange: 'Binance', symbol: 'BTCUSDT', timeframe: '4h', start_time: '2023-01-01', end_time: '2025-07-01', row_count: 5490 },
  { exchange: 'Binance', symbol: 'BTCUSDT', timeframe: '1h', start_time: '2023-01-01', end_time: '2025-07-01', row_count: 21960 },
  { exchange: 'Binance', symbol: 'ETHUSDT', timeframe: '1h', start_time: '2023-06-01', end_time: '2025-07-01', row_count: 17760 },
  { exchange: 'Bybit', symbol: 'SOLUSDT', timeframe: '15m', start_time: '2024-01-01', end_time: '2025-07-01', row_count: 43920 },
  { exchange: 'Bybit', symbol: 'AVAXUSDT', timeframe: '2h', start_time: '2024-05-01', end_time: '2025-07-01', row_count: 6216 },
  { exchange: 'Binance', symbol: 'BNBUSDT', timeframe: '1h', start_time: '2023-01-01', end_time: '2025-07-01', row_count: 21960 },
  { exchange: 'Bybit', symbol: 'DOGEUSDT', timeframe: '1h', start_time: '2024-07-01', end_time: '2025-07-01', row_count: 8760 },
  { exchange: 'Binance', symbol: 'XRPUSDT', timeframe: '4h', start_time: '2024-04-01', end_time: '2025-07-01', row_count: 3564 },
  { exchange: 'Binance', symbol: 'LINKUSDT', timeframe: '2h', start_time: '2024-08-01', end_time: '2025-07-01', row_count: 4980 },
];
