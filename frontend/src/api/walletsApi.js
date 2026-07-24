/**
 * walletsApi.js
 * Mirrors: GET /wallets, GET /wallets/:id, POST /wallets, PUT /wallets/:id, DELETE /wallets/:id
 * TODO(security): All mutations are mocked — when real API is wired, add CSRF tokens
 * and ensure API keys are NEVER returned in full from the backend.
 */
import { WALLETS } from '../mock/walletsMock';

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

// In-memory mutable store (simulates server state for add/edit/remove)
let walletStore = [...WALLETS];

/** GET /wallets */
export async function getWallets({ search = '', filter = {} } = {}) {
  await delay(350 + Math.random() * 200);
  let result = [...walletStore];
  if (search) {
    const q = search.toLowerCase();
    result = result.filter(
      (w) =>
        w.exchange.toLowerCase().includes(q) ||
        w.account_type.toLowerCase().includes(q) ||
        w.api_key.toLowerCase().includes(q),
    );
  }
  if (filter.status) result = result.filter((w) => w.status === filter.status);
  if (filter.exchange) result = result.filter((w) => w.exchange === filter.exchange);
  return { data: result, total: result.length, page: 1, pageSize: result.length };
}

/** GET /wallets/:id */
export async function getWalletById(id) {
  await delay(250 + Math.random() * 100);
  const wallet = walletStore.find((w) => w.id === id);
  if (!wallet) throw new Error(`Wallet ${id} not found`);
  return { ...wallet };
}

/** POST /wallets — add new wallet (mock: push to store) */
export async function addWallet(payload) {
  await delay(500 + Math.random() * 200);
  const newWallet = {
    ...payload,
    id: `wallet-${Date.now()}`,
    status: 'connected',
    balance: 0,
    unrealized_pnl: 0,
    total_pnl: 0,
    assigned_strategies: [],
    active_positions: [],
    open_orders: [],
    running_executions: [],
  };
  walletStore = [...walletStore, newWallet];
  return { ...newWallet };
}

/** PUT /wallets/:id — update wallet (mock: merge fields) */
export async function updateWallet(id, payload) {
  await delay(400 + Math.random() * 150);
  walletStore = walletStore.map((w) => (w.id === id ? { ...w, ...payload } : w));
  const updated = walletStore.find((w) => w.id === id);
  if (!updated) throw new Error(`Wallet ${id} not found`);
  return { ...updated };
}

/** DELETE /wallets/:id */
export async function deleteWallet(id) {
  await delay(400 + Math.random() * 150);
  walletStore = walletStore.filter((w) => w.id !== id);
  return { success: true };
}

/** PUT /wallets/:id/toggle — enable/disable */
export async function toggleWalletStatus(id) {
  await delay(300 + Math.random() * 100);
  walletStore = walletStore.map((w) => {
    if (w.id !== id) return w;
    const next = w.status === 'disabled' ? 'connected' : 'disabled';
    return { ...w, status: next };
  });
  return walletStore.find((w) => w.id === id);
}
