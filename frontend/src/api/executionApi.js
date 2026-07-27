/**
 * executionApi.js
 * FastAPI Backend integrated API client for /api/v1/execution.
 * Communicates directly with http://localhost:8000/api/v1/execution
 * Strict zero-mock governance policy. No fake mock rows returned.
 */

const BASE_URL = 'http://localhost:8000/api/v1/execution';

/** GET /api/v1/execution/health — Check execution PostgreSQL DB schema health */
export async function getExecutionDbHealth() {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    return { status: 'inactive', connected: false, error: err.message };
  }
}

/** GET /api/v1/execution — Fetch active execution strategy list */
export async function getDeployments({ search = '', filter = {}, page = 1, pageSize = 50 } = {}) {
  try {
    const queryParams = new URLSearchParams();
    if (search) queryParams.append('search', search);
    if (filter.status) queryParams.append('status', filter.status);

    const res = await fetch(`${BASE_URL}?${queryParams.toString()}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch executions from backend: ${res.statusText}`);
    }
    const json = await res.json();
    return {
      data: json.data || [],
      total: json.count || json.data?.length || 0,
      page,
      pageSize,
    };
  } catch (err) {
    return {
      data: [],
      total: 0,
      page,
      pageSize,
      error: err.message,
    };
  }
}

/** GET /api/v1/execution/:id — Fetch detailed execution run */
export async function getDeploymentById(id) {
  const res = await fetch(`${BASE_URL}/${id}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch execution details for "${id}" from backend: ${res.statusText}`);
  }
  const json = await res.json();
  return json.data;
}

/** PUT /api/v1/execution/:id/pause */
export async function pauseExecution(id) {
  const res = await fetch(`${BASE_URL}/${id}/pause`, { method: 'PUT' });
  if (!res.ok) throw new Error(`Failed to pause execution run "${id}"`);
  const json = await res.json();
  return json.data;
}

/** PUT /api/v1/execution/:id/stop */
export async function stopExecution(id) {
  const res = await fetch(`${BASE_URL}/${id}/stop`, { method: 'PUT' });
  if (!res.ok) throw new Error(`Failed to stop execution run "${id}"`);
  const json = await res.json();
  return json.data;
}
