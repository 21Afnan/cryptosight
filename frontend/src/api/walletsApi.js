import { WALLETS } from '../mock/walletsMock';

const BASE_URL = 'http://localhost:8000/api/v1/wallets';
let walletStore = [...WALLETS];

/** GET /wallets */
export async function getWallets({ search = '', filter = {} } = {}) {
  try {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (filter.status) params.append('status', filter.status);

    const res = await fetch(`${BASE_URL}?${params.toString()}`);
    if (res.ok) {
      const json = await res.json();
      if (json && Array.isArray(json.data) && json.data.length > 0) {
        walletStore = json.data;
        return json;
      }
    }
  } catch (err) {
    console.warn('Backend REST API wallet fetch failed; using local state:', err);
  }

  // Fallback to local memory store
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
  return { data: result, total: result.length, page: 1, pageSize: result.length };
}

/** GET /wallets/:id */
export async function getWalletById(id) {
  const wallet = walletStore.find((w) => w.id === id);
  if (!wallet) throw new Error(`Wallet ${id} not found`);
  return { ...wallet };
}

/** POST /wallets — add new wallet credentials */
export async function addWallet(payload) {
  try {
    const res = await fetch(BASE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      const json = await res.json();
      if (json && Array.isArray(json.data)) {
        walletStore = json.data;
        return json.data[json.data.length - 1];
      }
    }
  } catch (err) {
    console.warn('Backend REST API wallet POST failed; using local store fallback:', err);
  }

  const newWallet = {
    ...payload,
    id: `wallet-${Date.now()}`,
    status: 'connected',
    balance: 165929.65,
    available_balance: 49992.45,
    unrealized_pnl: 1.95,
    total_pnl: 12450.80,
    assigned_strategies: [],
    active_positions: [],
    open_orders: [],
    equity_curve: [],
  };
  walletStore = [...walletStore, newWallet];
  return { ...newWallet };
}

/** PUT /wallets/:id — update wallet */
export async function updateWallet(id, payload) {
  walletStore = walletStore.map((w) => (w.id === id ? { ...w, ...payload } : w));
  const updated = walletStore.find((w) => w.id === id);
  if (!updated) throw new Error(`Wallet ${id} not found`);
  return { ...updated };
}

/** DELETE /wallets/:id */
export async function deleteWallet(id) {
  walletStore = walletStore.filter((w) => w.id !== id);
  return { success: true };
}

/** PUT /wallets/:id/toggle — enable/disable */
export async function toggleWalletStatus(id) {
  walletStore = walletStore.map((w) => {
    if (w.id !== id) return w;
    const next = w.status === 'disabled' ? 'connected' : 'disabled';
    return { ...w, status: next };
  });
  return walletStore.find((w) => w.id === id);
}
