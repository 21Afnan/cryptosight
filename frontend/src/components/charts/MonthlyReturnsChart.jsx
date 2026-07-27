import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * MonthlyReturnsChart — bar chart where green bars = positive months, red = negative.
 *
 * @param {Array}  data   - [{ month: 'Jan 24', value: 0.042 }]  (value as decimal)
 * @param {number} height
 */
export default function MonthlyReturnsChart({ data = [], height = 220 }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  if (!Array.isArray(data) || !data.length) {
    return null;
  }

  const formatPct = (v) => `${(v * 100).toFixed(1)}%`;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const val = payload[0].value;
    return (
      <div style={{
        background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: 12,
        fontFamily: '"Inter", sans-serif',
      }}>
        <div style={{ color: isDark ? COLORS.darkTextSecondary : '#6B7280', marginBottom: 2 }}>{label}</div>
        <div style={{
          color: val >= 0 ? COLORS.pnlGreen : COLORS.pnlRed,
          fontWeight: 700,
          fontVariantNumeric: 'tabular-nums',
        }}>
          {val >= 0 ? '+' : ''}{formatPct(val)}
        </div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }} barSize={14}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight}
          vertical={false}
        />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280', fontFamily: '"Inter", sans-serif' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={formatPct}
          tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280', fontFamily: '"Inter", sans-serif' }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="value" radius={[3, 3, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.value >= 0 ? COLORS.pnlGreen : COLORS.pnlRed}
              fillOpacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
