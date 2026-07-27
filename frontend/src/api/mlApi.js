/**
 * mlApi.js
 * Dual-Mode FastAPI Backend & Offline Fallback API Client for Machine Learning Engine (/api/v1/ml).
 * 
 * 1. Live Mode: Directly queries FastAPI + PostgreSQL database.
 * 2. Inactive/Offline Mode: Invokes separate fallback functions when DB backend is unreachable.
 */

import { ML_MODELS } from '../mock/mlMock';
import { findMockById } from '../utils/findMockById';

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

// ─────────────────────────────────────────────────────────────────────────────
// SEPARATE OFFLINE FALLBACK FUNCTIONS (TRIGGERED ONLY WHEN DB IS INACTIVE)
// ─────────────────────────────────────────────────────────────────────────────

function getOfflineMockModelsFallback({ search = '', filter = {}, sort = {}, page = 1, pageSize = 50 } = {}) {
  const filtered = applyClientFilters(ML_MODELS, { search, filter, sort });
  const start = (page - 1) * pageSize;
  const classificationCount = ML_MODELS.filter(m => m.type?.toLowerCase() === 'classification').length;
  const regressionCount = ML_MODELS.filter(m => m.type?.toLowerCase() === 'regression').length;
  const topModel = ML_MODELS.reduce((max, m) => (m.score > (max?.score ?? 0) ? m : max), ML_MODELS[0]);

  return {
    data: filtered.slice(start, start + pageSize),
    total: filtered.length,
    kpis: {
      total_models: ML_MODELS.length,
      classification_models: classificationCount,
      regression_models: regressionCount,
      top_performer: topModel?.name || 'N/A',
    },
    page,
    pageSize,
    isFallback: true,
  };
}

function getOfflineMockModelByIdFallback(id) {
  const model = findMockById(ML_MODELS, id, ['model_id', 'id']);
  if (!model) return null;
  return { ...model, isFallback: true };
}

function getOfflineMockLedgerFallback(id, limit = 50, offset = 0) {
  const model = findMockById(ML_MODELS, id, ['model_id', 'id']);
  const trades = model?.backtest_ledger || [];
  return {
    total_trades: trades.length,
    trades: trades.slice(offset, offset + limit),
    limit,
    offset,
    isFallback: true,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN EXPORTED API CLIENT FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

/** GET /api/v1/ml/models — Primary Live Query with Automatic Offline Fallback */
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
    console.warn('Backend DB is inactive/unreachable. Activating separate offline fallback mode:', err.message);
    return getOfflineMockModelsFallback({ search, filter, sort, page, pageSize });
  }
}

/** GET /api/v1/ml/models/:id — Primary Live Query with Automatic Offline Fallback */
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
    console.warn(`Backend DB inactive for model ${id}. Activating separate offline fallback mode:`, err.message);
    return getOfflineMockModelByIdFallback(id);
  }
}

/** GET /api/v1/ml/models/:id/ledger — Primary Live Query with Automatic Offline Fallback */
export async function getModelLedger(id, limit = 50, offset = 0) {
  try {
    const res = await fetch(`${BASE_URL}/models/${id}/ledger?limit=${limit}&offset=${offset}`);
    if (!res.ok) {
      throw new Error(`FastAPI Server returned status ${res.status}`);
    }
    const json = await res.json();
    return { ...json?.data, isFallback: false };
  } catch (err) {
    console.warn(`Backend DB inactive for ledger ${id}. Activating separate offline fallback mode:`, err.message);
    return getOfflineMockLedgerFallback(id, limit, offset);
  }
}
