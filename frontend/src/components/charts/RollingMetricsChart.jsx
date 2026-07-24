import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

const METRIC_COLORS = {
  sharpe: COLORS.accent,
  sortino: COLORS.pnlGreen,
  calmar: COLORS.warning,
};

/**
 * RollingMetricsChart — multi-line recharts for rolling Sharpe/Sortino/Calmar.
 * Used in Backtest Details page.
 *
 * @param {Array}  data    - [{ date, sharpe, sortino, calmar }]
 * @param {number} height
 */
export default function RollingMetricsChart({ data = [], height = 250 }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{
        background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
        borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: '"Inter", sans-serif',
      }}>
        <div style={{ color: isDark ? COLORS.darkTextSecondary : '#6B7280', marginBottom: 4 }}>{label}</div>
        {payload.map((p) => (
          <div key={p.name} style={{ color: p.color, fontWeight: 600, fontVariantNumeric: 'tabular-nums', marginBottom: 2 }}>
            {p.name.charAt(0).toUpperCase() + p.name.slice(1)}: {Number(p.value).toFixed(2)}
          </div>
        ))}
      </div>
    );
  };

  const renderLegend = (props) => {
    const { payload } = props;
    return (
      <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 8 }}>
        {payload.map((entry) => (
          <span key={entry.value} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: isDark ? COLORS.darkTextSecondary : '#6B7280' }}>
            <span style={{ width: 12, height: 2, background: entry.color, display: 'inline-block', borderRadius: 1 }} />
            {entry.value.charAt(0).toUpperCase() + entry.value.slice(1)}
          </span>
        ))}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} width={36} />
        <Tooltip content={<CustomTooltip />} />
        <Legend content={renderLegend} />
        {Object.entries(METRIC_COLORS).map(([key, color]) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
