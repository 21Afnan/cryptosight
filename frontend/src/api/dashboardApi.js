/**
 * dashboardApi.js
 * API functions for the Dashboard page.
 * Fetches real aggregate metrics from FastAPI (http://127.0.0.1:8000/api/v1/dashboard/summary).
 * Includes seamless fallback to mock dataset if backend is offline.
 */
import axios from 'axios';
import { DASHBOARD_SUMMARY } from '../mock/dashboardMock';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export async function getDashboardSummary() {
  try {
    const res = await axios.get(`${API_BASE_URL}/dashboard/summary`, { timeout: 3000 });
    if (res.data) {
      return res.data;
    }
  } catch (err) {
    console.warn('Dashboard API unreachable, using fallback dataset:', err.message);
  }
  return { ...DASHBOARD_SUMMARY };
}
