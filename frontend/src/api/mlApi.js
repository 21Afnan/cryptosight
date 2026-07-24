/**
 * mlApi.js
 * Mirrors: GET /models, GET /models/:id
 */
import { ML_MODELS } from '../mock/mlMock';
import { findMockById } from '../utils/findMockById';

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

function applyFilters(data, { search = '', filter = {}, sort = {} } = {}) {
  let result = [...data];
  if (search) {
    const q = search.toLowerCase();
    result = result.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.symbol.toLowerCase().includes(q) ||
        m.type.toLowerCase().includes(q),
    );
  }
  if (filter.type) result = result.filter((m) => m.type === filter.type);
  if (filter.status) result = result.filter((m) => m.status === filter.status);
  if (filter.symbol) result = result.filter((m) => m.symbol === filter.symbol);
  if (sort.field) {
    const dir = sort.dir === 'desc' ? -1 : 1;
    result.sort((a, b) => (a[sort.field] < b[sort.field] ? -1 : 1) * dir);
  }
  return result;
}

/** GET /models */
export async function getModels({ search, filter, sort, page = 1, pageSize = 50 } = {}) {
  await delay(350 + Math.random() * 200);
  const filtered = applyFilters(ML_MODELS, { search, filter, sort });
  const start = (page - 1) * pageSize;
  return {
    data: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  };
}

/** GET /models/:id */
export async function getModelById(id) {
  await delay(300 + Math.random() * 150);
  const model = findMockById(ML_MODELS, id, ['model_id']);
  if (!model) throw new Error(`Model "${id}" not found`);
  return { ...model };
}
