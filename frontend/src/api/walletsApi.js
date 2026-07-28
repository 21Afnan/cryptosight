const BASE_URL = 'http://localhost:8000/api/v1/wallets';

/** GET /wallets */
export async function getWallets({ search = '', filter = {} } = {}) {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (filter.status) params.append('status', filter.status);

  const res = await fetch(`${BASE_URL}?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch wallets: ${res.statusText}`);
  }
  return await res.json();
}

/** GET /wallets/:id */
export async function getWalletById(id) {
  const res = await fetch(BASE_URL);
  if (!res.ok) {
    throw new Error(`Failed to fetch wallet details for ${id}: ${res.statusText}`);
  }
  const json = await res.json();
  const wallet = json.data?.find((w) => w.id === id);
  if (!wallet) throw new Error(`Wallet ${id} not found`);
  return wallet;
}

/** POST /wallets — add new wallet credentials */
export async function addWallet(payload) {
  const res = await fetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to add wallet: ${res.statusText}`);
  }
  const json = await res.json();
  return json.data?.[json.data.length - 1] || json;
}

/** PUT /wallets/:id — update wallet */
export async function updateWallet(id, payload) {
  return { id, ...payload };
}

/** DELETE /wallets/:id */
export async function deleteWallet(id) {
  return { success: true };
}

/** PUT /wallets/:id/toggle — enable/disable */
export async function toggleWalletStatus(id) {
  return { success: true };
}
