// ─── Dashboard API Layer ───────────────────────────────────────────────────────
// Currently returns mock data.
// To connect real backend: replace each return with an axios.get() call.
// Example: const res = await axios.get('/api/dashboard/kpis'); return res.data;

import { kpiData, strategiesData, sparklineData } from '../mock/dashboardmock';

export const getKPIs = async () => {
    return kpiData;
};

export const getStrategies = async () => {
    return strategiesData;
};

export const getSparkline = async () => {
    return sparklineData;
};
