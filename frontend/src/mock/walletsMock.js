/**
 * walletsMock.js
 * Invented schema for exchange accounts / wallets.
 * No matching Postgres table yet — schema designed to be clean and future-proof.
 *
 * Fields:
 *   id, exchange, account_type, api_key (masked), status,
 *   balance, unrealized_pnl, total_pnl,
 *   assigned_strategies, active_positions, open_orders, running_executions
 *
 * TODO(security): When real API exists, api_key must NEVER be returned in full.
 * Backend should always return masked form only.
 */

// TODO(security): API keys shown here are already masked — only last 4 chars visible.
export const WALLETS = [
  {
    id: 'wallet-001',
    exchange: 'Binance',
    account_type: 'Spot',
    // NOTE: Always masked — last 4 chars only. Full key never stored client-side.
    api_key: '****************************4f2a',
    status: 'connected',
    balance: 42850.60,
    unrealized_pnl: 1240.30,
    total_pnl: 7430.80,
    currency: 'USDT',
    assigned_strategies: [
      { strategy_id: 1, strategy_name: 'BTC_EMA_Cross_4H', symbol: 'BTCUSDT' },
      { strategy_id: 4, strategy_name: 'BNB_VWAP_Mean_Rev_1H', symbol: 'BNBUSDT' },
      { strategy_id: 6, strategy_name: 'XRP_Bollinger_Squeeze_4H', symbol: 'XRPUSDT' },
    ],
    active_positions: [
      {
        position_id: 'pos-001',
        strategy_id: 1,
        symbol: 'BTCUSDT',
        side: 'long',
        entry_price: 61240.50,
        current_price: 63480.20,
        size: 0.162,
        unrealized_pnl: 362.45,
        tp: 64000.00,
        sl: 59800.00,
        opened_at: '2025-07-01T04:00:00Z',
      },
    ],
    open_orders: [
      {
        order_id: 'ord-001',
        symbol: 'BTCUSDT',
        side: 'buy',
        type: 'limit',
        price: 61000.00,
        quantity: 0.1,
        filled: 0,
        status: 'open',
        created_at: '2025-07-01T06:30:00Z',
      },
    ],
    running_executions: [
      { execution_id: 'exec-001', strategy_name: 'BTC_EMA_Cross_4H', status: 'active', started_at: '2025-06-15T00:00:00Z', current_pnl: 1240.30 },
      { execution_id: 'exec-002', strategy_name: 'BNB_VWAP_Mean_Rev_1H', status: 'active', started_at: '2025-06-20T00:00:00Z', current_pnl: 284.10 },
    ],
  },
  {
    id: 'wallet-002',
    exchange: 'Bybit',
    account_type: 'Unified',
    api_key: '****************************9c3e',
    status: 'connected',
    balance: 18340.20,
    unrealized_pnl: -320.15,
    total_pnl: 2140.50,
    currency: 'USDT',
    assigned_strategies: [
      { strategy_id: 2, strategy_name: 'ETH_RSI_Divergence_1H', symbol: 'ETHUSDT' },
      { strategy_id: 5, strategy_name: 'AVAX_Triple_MA_2H', symbol: 'AVAXUSDT' },
    ],
    active_positions: [
      {
        position_id: 'pos-002',
        strategy_id: 2,
        symbol: 'ETHUSDT',
        side: 'short',
        entry_price: 3480.00,
        current_price: 3574.20,
        size: 3.4,
        unrealized_pnl: -320.15,
        tp: 3200.00,
        sl: 3600.00,
        opened_at: '2025-07-01T06:00:00Z',
      },
    ],
    open_orders: [],
    running_executions: [
      { execution_id: 'exec-003', strategy_name: 'ETH_RSI_Divergence_1H', status: 'active', started_at: '2025-06-10T00:00:00Z', current_pnl: -320.15 },
    ],
  },
  {
    id: 'wallet-003',
    exchange: 'Binance',
    account_type: 'Futures',
    api_key: '****************************1a7b',
    status: 'error',
    balance: 5200.00,
    unrealized_pnl: 0,
    total_pnl: -340.20,
    currency: 'USDT',
    assigned_strategies: [
      { strategy_id: 3, strategy_name: 'SOL_Momentum_15M', symbol: 'SOLUSDT' },
    ],
    active_positions: [],
    open_orders: [],
    running_executions: [],
    error_message: 'API key permission error: Futures trading not enabled.',
  },
  {
    id: 'wallet-004',
    exchange: 'Bybit',
    account_type: 'Spot',
    api_key: '****************************e81f',
    status: 'disabled',
    balance: 12000.00,
    unrealized_pnl: 0,
    total_pnl: 0,
    currency: 'USDT',
    assigned_strategies: [],
    active_positions: [],
    open_orders: [],
    running_executions: [],
  },
];
