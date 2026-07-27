import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * PositionSizeChart — position size per trade over time.
 * Used in Execution Details page.
 *
 * @param {Array}  data   - [{ trade: number|string, size: number, side: 'long'|'short' }]
 * @param {number} height
 */
export default function PositionSizeChart({ data = [], height = 200 }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  if (!Array.isArray(data) || !data.length) {
    return null;
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const entry = payload[0].payload;
    return (
      <div style={{
        background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
        borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: '"Inter", sans-serif',
      }}>
        <div style={{ color: isDark ? COLORS.darkTextSecondary : '#6B7280', marginBottom: 2 }}>Trade #{label}</div>
        <div style={{ color: isDark ? COLORS.darkTextPrimary : '#111827', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
          Size: ${Number(entry.size).toLocaleString()}
        </div>
        <div style={{ color: entry.side === 'long' ? COLORS.pnlGreen : COLORS.pnlRed, fontSize: 11, marginTop: 2 }}>
          {entry.side?.toUpperCase()}
        </div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }} barSize={12}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} vertical={false} />
        <XAxis dataKey="trade" tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={(v) => `$${v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}`} tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} width={48} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="size" radius={[3, 3, 0, 0]}>
          {data.map((entry, idx) => (
            <Cell key={idx} fill={entry.side === 'long' ? COLORS.pnlGreen : COLORS.pnlRed} fillOpacity={0.75} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
