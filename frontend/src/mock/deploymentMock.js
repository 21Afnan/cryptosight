/**
 * deploymentMock.js
 * Mock data for deployed strategy executions.
 * Mirrors: simulations.active_positions + metadata.simulation_data
 */

export function generateDailyReturns(days = 60, startDate = '2025-05-01') {
  const data = [];
  let date = new Date(startDate);
  for (let i = 0; i < days; i++) {
    data.push({
      date: date.toISOString().split('T')[0],
      value: parseFloat(((Math.random() - 0.42) * 400).toFixed(2)),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
}

function generateSignalHistory(count = 30) {
  const signals = [];
  let date = new Date('2025-06-01T00:00:00Z');
  for (let i = 0; i < count; i++) {
    signals.push({
      signal_id: i + 1,
      timestamp: date.toISOString(),
      signal: Math.random() > 0.5 ? 'long' : (Math.random() > 0.5 ? 'short' : 'flat'),
      price: 40000 + Math.random() * 30000,
      triggered: Math.random() > 0.2,
    });
    date = new Date(date.getTime() + (1 + Math.random() * 8) * 3600000);
  }
  return signals.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

function generatePositionSizeHistory(count = 20) {
  const data = [];
  for (let i = 1; i <= count; i++) {
    data.push({
      trade: i,
      size: parseFloat((500 + Math.random() * 2000).toFixed(2)),
      side: Math.random() > 0.45 ? 'long' : 'short',
    });
  }
  return data;
}

function generateEquityForDeployment(days = 60) {
  const data = [];
  let value = 10000;
  let date = new Date('2025-05-01');
  for (let i = 0; i < days; i++) {
    value *= 1 + (Math.random() - 0.44) * 0.018;
    value = Math.max(value, 7000);
    data.push({ time: date.toISOString().split('T')[0], value: parseFloat(value.toFixed(2)) });
    date.setDate(date.getDate() + 1);
  }
  return data;
}

export const DEPLOYMENTS = [
  {
    execution_id: 'exec-001',
    strategy_id: 1,
    strategy_name: 'BTC_EMA_Cross_4H',
    symbol: 'BTCUSDT',
    exchange: 'Binance',
    wallet_id: 'wallet-001',
    wallet_label: 'Binance Spot (...4f2a)',
    // metadata.simulation_data fields
    initial_balance: 10000,
    position_size_type: 'percent',
    position_size_value: 0.10,
    commission: 0.0005,
    slippage: 0.0002,
    status: 'active',
    current_pnl: 1240.30,
    current_pnl_pct: 0.1240,
    daily_return: 0.0032,
    last_signal: 'long',
    last_signal_time: '2025-07-01T08:00:00Z',
    last_execution_time: '2025-07-01T08:01:00Z',
    // simulations.active_positions
    active_position: {
      entry_price: 61240.50,
      current_price: 63480.20,
      side: 'long',
      size: 0.162,
      unrealized_pnl: 362.45,
      tp: 64000.00,
      sl: 59800.00,
      opened_at: '2025-07-01T04:00:00Z',
    },
    started_at: '2025-06-15T00:00:00Z',
    equity_curve: generateEquityForDeployment(60),
    daily_returns: generateDailyReturns(60),
    position_size_history: generatePositionSizeHistory(20),
    signal_history: generateSignalHistory(30),
  },
  {
    execution_id: 'exec-002',
    strategy_id: 4,
    strategy_name: 'BNB_VWAP_Mean_Rev_1H',
    symbol: 'BNBUSDT',
    exchange: 'Binance',
    wallet_id: 'wallet-001',
    wallet_label: 'Binance Spot (...4f2a)',
    initial_balance: 10000,
    position_size_type: 'percent',
    position_size_value: 0.15,
    commission: 0.0005,
    slippage: 0.0002,
    status: 'active',
    current_pnl: 284.10,
    current_pnl_pct: 0.0284,
    daily_return: 0.0011,
    last_signal: 'long',
    last_signal_time: '2025-07-01T07:00:00Z',
    last_execution_time: '2025-07-01T07:01:00Z',
    active_position: {
      entry_price: 576.40,
      current_price: 581.20,
      side: 'long',
      size: 17.3,
      unrealized_pnl: 83.04,
      tp: 595.00,
      sl: 562.00,
      opened_at: '2025-07-01T07:00:00Z',
    },
    started_at: '2025-06-20T00:00:00Z',
    equity_curve: generateEquityForDeployment(60),
    daily_returns: generateDailyReturns(60),
    position_size_history: generatePositionSizeHistory(18),
    signal_history: generateSignalHistory(25),
  },
  {
    execution_id: 'exec-003',
    strategy_id: 2,
    strategy_name: 'ETH_RSI_Divergence_1H',
    symbol: 'ETHUSDT',
    exchange: 'Bybit',
    wallet_id: 'wallet-002',
    wallet_label: 'Bybit Unified (...9c3e)',
    initial_balance: 10000,
    position_size_type: 'percent',
    position_size_value: 0.08,
    commission: 0.0006,
    slippage: 0.0002,
    status: 'active',
    current_pnl: -320.15,
    current_pnl_pct: -0.0320,
    daily_return: -0.0018,
    last_signal: 'short',
    last_signal_time: '2025-07-01T06:00:00Z',
    last_execution_time: '2025-07-01T06:01:00Z',
    active_position: {
      entry_price: 3480.00,
      current_price: 3574.20,
      side: 'short',
      size: 3.4,
      unrealized_pnl: -320.15,
      tp: 3200.00,
      sl: 3600.00,
      opened_at: '2025-07-01T06:00:00Z',
    },
    started_at: '2025-06-10T00:00:00Z',
    equity_curve: generateEquityForDeployment(60),
    daily_returns: generateDailyReturns(60),
    position_size_history: generatePositionSizeHistory(22),
    signal_history: generateSignalHistory(35),
  },
  {
    execution_id: 'exec-004',
    strategy_id: 7,
    strategy_name: 'DOGE_Volume_Breakout_1H',
    symbol: 'DOGEUSDT',
    exchange: 'Bybit',
    wallet_id: 'wallet-002',
    wallet_label: 'Bybit Unified (...9c3e)',
    initial_balance: 10000,
    position_size_type: 'fixed',
    position_size_value: 700,
    commission: 0.0006,
    slippage: 0.0003,
    status: 'paused',
    current_pnl: 87.30,
    current_pnl_pct: 0.0087,
    daily_return: 0.0,
    last_signal: 'flat',
    last_signal_time: '2025-07-01T09:00:00Z',
    last_execution_time: '2025-07-01T09:01:00Z',
    active_position: null,
    started_at: '2025-07-01T00:00:00Z',
    equity_curve: generateEquityForDeployment(30),
    daily_returns: generateDailyReturns(30, '2025-06-01'),
    position_size_history: generatePositionSizeHistory(8),
    signal_history: generateSignalHistory(15),
  },
];
