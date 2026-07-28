import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export async function getDashboardSummary() {
  const res = await axios.get(`${API_BASE_URL}/dashboard/summary`, { timeout: 10000 });
  return res.data;
}
