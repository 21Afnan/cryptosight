/**
 * deploymentApi.js
 * Mirrors: GET /executions, GET /executions/:id
 * TODO(security): When real API is wired, validate execution IDs server-side.
 */
import { DEPLOYMENTS } from '../mock/deploymentMock';
import { findMockById } from '../utils/findMockById';

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

function applyFilters(data, { search = '', filter = {} } = {}) {
  let result = [...data];
  if (search) {
    const q = search.toLowerCase();
    result = result.filter(
      (d) =>
        d.strategy_name.toLowerCase().includes(q) ||
        d.symbol.toLowerCase().includes(q) ||
        d.exchange.toLowerCase().includes(q),
    );
  }
  if (filter.status) result = result.filter((d) => d.status === filter.status);
  if (filter.exchange) result = result.filter((d) => d.exchange === filter.exchange);
  return result;
}

/** GET /executions */
export async function getDeployments({ search, filter, page = 1, pageSize = 50 } = {}) {
  await delay(350 + Math.random() * 200);
  const filtered = applyFilters(DEPLOYMENTS, { search, filter });
  const start = (page - 1) * pageSize;
  return {
    data: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  };
}

/** GET /executions/:id */
export async function getDeploymentById(id) {
  await delay(300 + Math.random() * 150);
  const deployment = findMockById(DEPLOYMENTS, id, ['execution_id']);
  if (!deployment) throw new Error(`Execution "${id}" not found`);
  return { ...deployment };
}

/** PUT /executions/:id/pause — mock pause */
export async function pauseExecution(id) {
  await delay(400);
  return { success: true, execution_id: id, status: 'paused' };
}

/** PUT /executions/:id/stop — mock stop */
export async function stopExecution(id) {
  await delay(400);
  return { success: true, execution_id: id, status: 'stopped' };
}
