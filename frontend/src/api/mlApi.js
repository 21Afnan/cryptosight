/**
 * mlApi.js
 * Pure Live FastAPI Backend API Client for Machine Learning Engine (/api/v1/ml).
 * Queries FastAPI + PostgreSQL database directly without any mock fallback data.
 */

const BASE_URL = 'http://localhost:8000/api/v1/ml';

function applyClientFilters(data, { search = '', filter = {}, sort = {} } = {}) {
  let result = [...data];
  if (search) {
    const q = search.toLowerCase();
    result = result.filter(
      (m) =>
        (m.name && m.name.toLowerCase().includes(q)) ||
        (m.symbol && m.symbol.toLowerCase().includes(q)) ||
        (m.type && m.type.toLowerCase().includes(q)) ||
        (m.model_id && m.model_id.toLowerCase().includes(q))
    );
  }
  if (filter.type) result = result.filter((m) => m.type.toLowerCase() === filter.type.toLowerCase());
  if (filter.status) result = result.filter((m) => m.status.toLowerCase() === filter.status.toLowerCase());
  if (filter.symbol) result = result.filter((m) => m.symbol.toUpperCase() === filter.symbol.toUpperCase());

  if (sort.field) {
    const dir = sort.dir === 'desc' ? -1 : 1;
    result.sort((a, b) => {
      const valA = a[sort.field] ?? 0;
      const valB = b[sort.field] ?? 0;
      return (valA < valB ? -1 : valA > valB ? 1 : 0) * dir;
    });
  }
  return result;
}

/** GET /api/v1/ml/models — Primary Live Query */
export async function getModels({ search = '', filter = {}, sort = {}, page = 1, pageSize = 50 } = {}) {
  try {
    const params = new URLSearchParams();
    if (filter.type && filter.type.toUpperCase() !== 'ALL') {
      params.append('task_type', filter.type);
    }
    if (filter.symbol && filter.symbol.toUpperCase() !== 'ALL') {
      params.append('symbol', filter.symbol);
    }

    const queryStr = params.toString();
    const fetchUrl = queryStr ? `${BASE_URL}/models?${queryStr}` : `${BASE_URL}/models`;

    const res = await fetch(fetchUrl);
    if (!res.ok) {
      throw new Error(`FastAPI Server returned status ${res.status}`);
    }
    const json = await res.json();
    const serverData = json?.data || {};
    const rawModels = serverData?.models || [];
    const kpis = serverData?.kpis || {};

    const filtered = applyClientFilters(rawModels, { search, filter, sort });
    const start = (page - 1) * pageSize;

    return {
      data: filtered.slice(start, start + pageSize),
      total: filtered.length,
      kpis,
      page,
      pageSize,
      isFallback: false,
    };
  } catch (err) {
    console.error('Error fetching live ML models from backend:', err.message);
    return {
      data: [],
      total: 0,
      kpis: { total_models: 0, classification_models: 0, regression_models: 0, top_performer: 'N/A' },
      page,
      pageSize,
      isFallback: false,
      error: err.message,
    };
  }
}

/** GET /api/v1/ml/models/:id — Primary Live Query */
export async function getModelById(id) {
  try {
    const res = await fetch(`${BASE_URL}/models/${id}`);
    if (!res.ok) {
      throw new Error(`FastAPI Server returned status ${res.status}`);
    }
    const json = await res.json();
    if (!json?.data) {
      throw new Error(`Model data null for ID ${id}`);
    }
    return { ...json.data, isFallback: false };
  } catch (err) {
    console.error(`Error fetching live ML model details for ${id}:`, err.message);
    return null;
  }
}

/** GET /api/v1/ml/models/:id/ledger — Primary Live Query */
export async function getModelLedger(id, limit = 50, offset = 0) {
  try {
    const res = await fetch(`${BASE_URL}/models/${id}/ledger?limit=${limit}&offset=${offset}`);
    if (!res.ok) {
      throw new Error(`FastAPI Server returned status ${res.status}`);
    }
    const json = await res.json();
    return { ...json?.data, isFallback: false };
  } catch (err) {
    console.error(`Error fetching live ML ledger for ${id}:`, err.message);
    return {
      total_trades: 0,
      trades: [],
      limit,
      offset,
      isFallback: false,
    };
  }
}
