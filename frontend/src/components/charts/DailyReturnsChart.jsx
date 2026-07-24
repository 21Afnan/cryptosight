import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * DailyReturnsChart — daily P&L bar chart with green/red bars.
 * Used in Execution Details page.
 *
 * @param {Array}  data   - [{ date: 'YYYY-MM-DD', value: number }]
 * @param {number} height
 */
export default function DailyReturnsChart({ data = [], height = 200 }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const formatVal = (v) => `$${v >= 0 ? '+' : ''}${v.toFixed(0)}`;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const val = payload[0].value;
    return (
      <div style={{
        background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
        borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: '"Inter", sans-serif',
      }}>
        <div style={{ color: isDark ? COLORS.darkTextSecondary : '#6B7280', marginBottom: 2 }}>{label}</div>
        <div style={{ color: val >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
          {val >= 0 ? '+' : ''}${Math.abs(val).toFixed(2)}
        </div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }} barSize={8}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={(v) => `$${v}`} tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} width={52} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="value" radius={[2, 2, 0, 0]}>
          {data.map((entry, idx) => (
            <Cell key={idx} fill={entry.value >= 0 ? COLORS.pnlGreen : COLORS.pnlRed} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
