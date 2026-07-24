/**
 * strategiesMock.js
 * Raw mock data for strategies, mirroring:
 *   - metadata.strategy_data
 *   - metadata.backtest_data
 *   - simulations.stats (subset: Sharpe, Sortino, Calmar, MaxDD, CAGR, WinRate)
 *   - simulations.active_positions
 *   - simulation_ledgers (recent trades shape)
 */

export const STRATEGIES = [
  {
    // metadata.strategy_data fields
    strategy_id: 1,
    strategy_name: 'BTC_EMA_Cross_4H',
    exchange: 'Binance',
    symbol: 'BTCUSDT',
    target_timeframe: '4h',
    timeframe: '1m',
    start_time: '2024-01-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      EMA_fast: { period: 9 },
      EMA_slow: { period: 21 },
      RSI: { period: 14 },
      ATR: { period: 14 },
    },
    strategy_config: {
      take_profit: 0.045,
      stop_loss: 0.02,
      position_size: 0.1,
      signal_condition: 'EMA_fast > EMA_slow AND RSI > 50',
    },
    total_rows: 262800,
    long_signals: 142,
    short_signals: 0,
    last_signal_time: '2025-07-01T08:00:00Z',
    last_updated: '2025-07-01T08:05:00Z',
    // From metadata.backtest_data
    backtest_config: { initial_balance: 10000, commission: 0.0005, slippage: 0.0002 },
    total_trades: 137,
    win_rate: 0.614,
    net_pnl: 4820.5,
    final_balance: 14820.5,
    // From simulations.stats
    sharpe: 1.84,
    sortino: 2.31,
    calmar: 1.12,
    max_drawdown: -0.183,
    cagr: 0.287,
    status: 'active',
    // Equity curve data (shortened for mock — real would be DB query)
    equity_curve: generateEquityCurve(10000, 180, 0.0012, 0.025, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(180, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(18, 2024, 1),
    trade_distribution: generateDistribution(),
  },
  {
    strategy_id: 2,
    strategy_name: 'ETH_RSI_Divergence_1H',
    exchange: 'Bybit',
    symbol: 'ETHUSDT',
    target_timeframe: '1h',
    timeframe: '1m',
    start_time: '2024-03-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      RSI: { period: 14 },
      MACD: { fast: 12, slow: 26, signal: 9 },
      BB: { period: 20, std: 2 },
    },
    strategy_config: {
      take_profit: 0.03,
      stop_loss: 0.015,
      position_size: 0.08,
      signal_condition: 'RSI_divergence AND price > BB_lower',
    },
    total_rows: 350400,
    long_signals: 234,
    short_signals: 89,
    last_signal_time: '2025-07-01T10:00:00Z',
    last_updated: '2025-07-01T10:05:00Z',
    backtest_config: { initial_balance: 10000, commission: 0.0006, slippage: 0.0002 },
    total_trades: 318,
    win_rate: 0.553,
    net_pnl: 2340.8,
    final_balance: 12340.8,
    sharpe: 1.42,
    sortino: 1.78,
    calmar: 0.89,
    max_drawdown: -0.241,
    cagr: 0.198,
    status: 'active',
    equity_curve: generateEquityCurve(10000, 120, 0.0008, 0.02, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(120, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(16, 2024, 3),
    trade_distribution: generateDistribution(),
  },
  {
    strategy_id: 3,
    strategy_name: 'SOL_Momentum_15M',
    exchange: 'Binance',
    symbol: 'SOLUSDT',
    target_timeframe: '15m',
    timeframe: '1m',
    start_time: '2024-06-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      ADX: { period: 14 },
      STOCH: { fastk: 14, slowk: 3, slowd: 3 },
      VWAP: {},
    },
    strategy_config: {
      take_profit: 0.025,
      stop_loss: 0.012,
      position_size: 0.12,
      signal_condition: 'ADX > 25 AND STOCH_K > STOCH_D',
    },
    total_rows: 438000,
    long_signals: 512,
    short_signals: 198,
    last_signal_time: '2025-07-01T09:45:00Z',
    last_updated: '2025-07-01T09:50:00Z',
    backtest_config: { initial_balance: 10000, commission: 0.0005, slippage: 0.0003 },
    total_trades: 687,
    win_rate: 0.512,
    net_pnl: 1876.2,
    final_balance: 11876.2,
    sharpe: 1.18,
    sortino: 1.44,
    calmar: 0.74,
    max_drawdown: -0.312,
    cagr: 0.156,
    status: 'paused',
    equity_curve: generateEquityCurve(10000, 90, 0.0006, 0.03, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(90, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(13, 2024, 6),
    trade_distribution: generateDistribution(),
  },
  {
    strategy_id: 4,
    strategy_name: 'BNB_VWAP_Mean_Rev_1H',
    exchange: 'Binance',
    symbol: 'BNBUSDT',
    target_timeframe: '1h',
    timeframe: '1m',
    start_time: '2024-02-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      VWAP: {},
      EMA: { period: 20 },
      ATR: { period: 14 },
    },
    strategy_config: {
      take_profit: 0.02,
      stop_loss: 0.01,
      position_size: 0.15,
      signal_condition: 'price < VWAP * 0.995 AND EMA_slope > 0',
    },
    total_rows: 394200,
    long_signals: 389,
    short_signals: 0,
    last_signal_time: '2025-07-01T07:00:00Z',
    last_updated: '2025-07-01T07:05:00Z',
    backtest_config: { initial_balance: 10000, commission: 0.0005, slippage: 0.0002 },
    total_trades: 384,
    win_rate: 0.578,
    net_pnl: 3102.4,
    final_balance: 13102.4,
    sharpe: 1.61,
    sortino: 2.04,
    calmar: 1.01,
    max_drawdown: -0.208,
    cagr: 0.231,
    status: 'active',
    equity_curve: generateEquityCurve(10000, 150, 0.001, 0.022, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(150, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(17, 2024, 2),
    trade_distribution: generateDistribution(),
  },
  {
    strategy_id: 5,
    strategy_name: 'AVAX_Triple_MA_2H',
    exchange: 'Bybit',
    symbol: 'AVAXUSDT',
    target_timeframe: '2h',
    timeframe: '1m',
    start_time: '2024-05-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      SMA_fast: { period: 5 },
      SMA_mid:  { period: 13 },
      SMA_slow: { period: 34 },
      Volume: {},
    },
    strategy_config: {
      take_profit: 0.035,
      stop_loss: 0.018,
      position_size: 0.09,
      signal_condition: 'SMA_fast > SMA_mid > SMA_slow AND Volume > avg_volume',
    },
    total_rows: 306000,
    long_signals: 178,
    short_signals: 42,
    last_signal_time: '2025-07-01T06:00:00Z',
    last_updated: '2025-07-01T06:10:00Z',
    backtest_config: { initial_balance: 10000, commission: 0.0006, slippage: 0.0003 },
    total_trades: 214,
    win_rate: 0.527,
    net_pnl: 1423.7,
    final_balance: 11423.7,
    sharpe: 1.09,
    sortino: 1.31,
    calmar: 0.62,
    max_drawdown: -0.278,
    cagr: 0.134,
    status: 'stopped',
    equity_curve: generateEquityCurve(10000, 70, 0.0005, 0.035, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(70, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(14, 2024, 5),
    trade_distribution: generateDistribution(),
  },
  {
    strategy_id: 6,
    strategy_name: 'XRP_Bollinger_Squeeze_4H',
    exchange: 'Binance',
    symbol: 'XRPUSDT',
    target_timeframe: '4h',
    timeframe: '1m',
    start_time: '2024-04-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      BB: { period: 20, std: 2 },
      KC: { period: 20, multiplier: 1.5 },
      MOMENTUM: { period: 12 },
    },
    strategy_config: {
      take_profit: 0.04,
      stop_loss: 0.02,
      position_size: 0.11,
      signal_condition: 'BB_width < KC_width AND MOMENTUM > 0',
    },
    total_rows: 350400,
    long_signals: 96,
    short_signals: 48,
    last_signal_time: '2025-06-30T20:00:00Z',
    last_updated: '2025-06-30T20:10:00Z',
    backtest_config: { initial_balance: 10000, commission: 0.0005, slippage: 0.0002 },
    total_trades: 142,
    win_rate: 0.592,
    net_pnl: 2654.3,
    final_balance: 12654.3,
    sharpe: 1.53,
    sortino: 1.91,
    calmar: 0.97,
    max_drawdown: -0.226,
    cagr: 0.214,
    status: 'active',
    equity_curve: generateEquityCurve(10000, 100, 0.0009, 0.028, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(100, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(15, 2024, 4),
    trade_distribution: generateDistribution(),
  },
  {
    strategy_id: 7,
    strategy_name: 'DOGE_Volume_Breakout_1H',
    exchange: 'Bybit',
    symbol: 'DOGEUSDT',
    target_timeframe: '1h',
    timeframe: '1m',
    start_time: '2024-07-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      Volume: {},
      OBV: {},
      EMA: { period: 20 },
    },
    strategy_config: {
      take_profit: 0.05,
      stop_loss: 0.025,
      position_size: 0.07,
      signal_condition: 'Volume > avg_volume * 2 AND OBV_slope > 0',
    },
    total_rows: 525600,
    long_signals: 67,
    short_signals: 23,
    last_signal_time: '2025-07-01T09:00:00Z',
    last_updated: '2025-07-01T09:05:00Z',
    backtest_config: { initial_balance: 10000, commission: 0.0006, slippage: 0.0003 },
    total_trades: 88,
    win_rate: 0.511,
    net_pnl: 987.4,
    final_balance: 10987.4,
    sharpe: 0.92,
    sortino: 1.14,
    calmar: 0.52,
    max_drawdown: -0.341,
    cagr: 0.098,
    status: 'active',
    equity_curve: generateEquityCurve(10000, 60, 0.0004, 0.04, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(60, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(12, 2024, 7),
    trade_distribution: generateDistribution(),
  },
  {
    strategy_id: 8,
    strategy_name: 'LINK_MACD_Crossover_2H',
    exchange: 'Binance',
    symbol: 'LINKUSDT',
    target_timeframe: '2h',
    timeframe: '1m',
    start_time: '2024-08-01T00:00:00Z',
    end_time: '2025-07-01T00:00:00Z',
    indicators_config: {
      MACD: { fast: 12, slow: 26, signal: 9 },
      RSI: { period: 14 },
      SMA: { period: 50 },
    },
    strategy_config: {
      take_profit: 0.038,
      stop_loss: 0.019,
      position_size: 0.1,
      signal_condition: 'MACD_line > MACD_signal AND RSI > 45 AND price > SMA',
    },
    total_rows: 262800,
    long_signals: 104,
    short_signals: 38,
    last_signal_time: '2025-07-01T08:00:00Z',
    last_updated: '2025-07-01T08:10:00Z',
    backtest_config: { initial_balance: 10000, commission: 0.0005, slippage: 0.0002 },
    total_trades: 138,
    win_rate: 0.565,
    net_pnl: 2187.6,
    final_balance: 12187.6,
    sharpe: 1.37,
    sortino: 1.72,
    calmar: 0.84,
    max_drawdown: -0.254,
    cagr: 0.178,
    status: 'paused',
    equity_curve: generateEquityCurve(10000, 80, 0.0007, 0.03, '2025-01-01'),
    drawdown_curve: generateDrawdownCurve(80, '2025-01-01'),
    monthly_returns: generateMonthlyReturns(11, 2024, 8),
    trade_distribution: generateDistribution(),
  },
];

// ─── Mock recent trades (simulation_ledgers shape) ───────────────────────────
export function generateTrades(strategyName, count = 20) {
  const sides = ['long', 'short'];
  const trades = [];
  let entryTime = new Date('2025-06-01T00:00:00Z');
  for (let i = 0; i < count; i++) {
    const side = sides[Math.floor(Math.random() * (strategyName.includes('EMA') ? 1 : 2))];
    const entryPrice = 40000 + Math.random() * 30000;
    const pct = (Math.random() - 0.42) * 0.08;
    const exitPrice = entryPrice * (1 + (side === 'long' ? pct : -pct));
    const size = 500 + Math.random() * 1500;
    const grossPnl = (exitPrice - entryPrice) * (size / entryPrice) * (side === 'long' ? 1 : -1);
    const fees = size * 0.001;
    const netPnl = grossPnl - fees;
    const exitTime = new Date(entryTime.getTime() + (2 + Math.random() * 10) * 3600000);
    trades.push({
      trade_id: i + 1,
      strategy_name: strategyName,
      entry_time: entryTime.toISOString(),
      exit_time: exitTime.toISOString(),
      side,
      entry_price: entryPrice,
      exit_price: exitPrice,
      position_size: size,
      gross_pnl: grossPnl,
      net_pnl: netPnl,
      fees,
      return_pct: (netPnl / size) * 100,
      status: 'closed',
    });
    entryTime = new Date(exitTime.getTime() + Math.random() * 48 * 3600000);
  }
  return trades.sort((a, b) => new Date(b.entry_time) - new Date(a.entry_time));
}

// ─── Helpers to generate curve data ──────────────────────────────────────────
function generateEquityCurve(start, days, drift, vol, startDate) {
  const data = [];
  let value = start;
  let date = new Date(startDate);
  for (let i = 0; i < days; i++) {
    value *= 1 + drift + (Math.random() - 0.5) * vol;
    value = Math.max(value, start * 0.5);
    data.push({
      time: date.toISOString().split('T')[0],
      value: parseFloat(value.toFixed(2)),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
}

function generateDrawdownCurve(days, startDate) {
  const data = [];
  let date = new Date(startDate);
  let dd = 0;
  for (let i = 0; i < days; i++) {
    dd += (Math.random() - 0.6) * 0.008;
    dd = Math.max(-0.45, Math.min(0, dd));
    data.push({
      time: date.toISOString().split('T')[0],
      value: parseFloat(dd.toFixed(4)),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
}

function generateMonthlyReturns(months, startYear, startMonth) {
  const labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const data = [];
  let year = startYear;
  let month = startMonth - 1;
  for (let i = 0; i < months; i++) {
    data.push({
      month: `${labels[month]} ${String(year).slice(2)}`,
      value: parseFloat(((Math.random() - 0.38) * 0.14).toFixed(4)),
    });
    month++;
    if (month > 11) { month = 0; year++; }
  }
  return data;
}

function generateDistribution() {
  const ranges = [
    { range: '<-3%', positive: false },
    { range: '-3–-2%', positive: false },
    { range: '-2–-1%', positive: false },
    { range: '-1–0%', positive: false },
    { range: '0–1%', positive: true },
    { range: '1–2%', positive: true },
    { range: '2–3%', positive: true },
    { range: '>3%', positive: true },
  ];
  return ranges.map(r => ({
    ...r,
    count: Math.floor(r.positive ? 8 + Math.random() * 25 : 3 + Math.random() * 18),
  }));
}
