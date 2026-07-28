/**
 * dashboardMock.js
 * Aggregate KPI data for the Dashboard page.
 * Derived from other mock datasets — in the real API this would be a dedicated
 * GET /dashboard/summary endpoint.
 */

export const DASHBOARD_SUMMARY = {
  total_strategies: 8,
  active_strategies: 5,
  running_executions: 3,
  running_simulations: 3,
  connected_accounts: 2,
  trained_ml_models: 6,
  total_backtests: 5,
  todays_pnl: 412.80,
  todays_pnl_pct: 0.0034,
  portfolio_value: 79190.80,
  portfolio_change_pct: 0.0243,
  total_return: 0.1843,
  total_return_usd: 12640.80,

  // Strategies summary table data (for Dashboard table — minimal fields)
  strategies_summary: [
    { strategy_id: 1, strategy_name: 'BTC_EMA_Cross_4H', symbol: 'BTCUSDT', exchange: 'Binance', timeframe: '4h', status: 'active', latest_return: 0.1240, sharpe: 1.84, win_rate: 0.614 },
    { strategy_id: 2, strategy_name: 'ETH_RSI_Divergence_1H', symbol: 'ETHUSDT', exchange: 'Bybit', timeframe: '1h', status: 'active', latest_return: -0.0320, sharpe: 1.42, win_rate: 0.553 },
    { strategy_id: 3, strategy_name: 'SOL_Momentum_15M', symbol: 'SOLUSDT', exchange: 'Binance', timeframe: '15m', status: 'paused', latest_return: 0.0612, sharpe: 1.18, win_rate: 0.512 },
    { strategy_id: 4, strategy_name: 'BNB_VWAP_Mean_Rev_1H', symbol: 'BNBUSDT', exchange: 'Binance', timeframe: '1h', status: 'active', latest_return: 0.0284, sharpe: 1.61, win_rate: 0.578 },
    { strategy_id: 5, strategy_name: 'AVAX_Triple_MA_2H', symbol: 'AVAXUSDT', exchange: 'Bybit', timeframe: '2h', status: 'stopped', latest_return: -0.0142, sharpe: 1.09, win_rate: 0.527 },
    { strategy_id: 6, strategy_name: 'XRP_Bollinger_Squeeze_4H', symbol: 'XRPUSDT', exchange: 'Binance', timeframe: '4h', status: 'active', latest_return: 0.0880, sharpe: 1.53, win_rate: 0.592 },
    { strategy_id: 7, strategy_name: 'DOGE_Volume_Breakout_1H', symbol: 'DOGEUSDT', exchange: 'Bybit', timeframe: '1h', status: 'active', latest_return: 0.0087, sharpe: 0.92, win_rate: 0.511 },
    { strategy_id: 8, strategy_name: 'LINK_MACD_Crossover_2H', symbol: 'LINKUSDT', exchange: 'Binance', timeframe: '2h', status: 'paused', latest_return: 0.0421, sharpe: 1.37, win_rate: 0.565 },
  ],
};
