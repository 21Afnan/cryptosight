import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * SentimentTimelineChart — stacked area showing bullish/bearish/neutral over time.
 *
 * @param {Array}  data   - [{ date, bullish, bearish, neutral }] (values 0–100)
 * @param {number} height
 */
export default function SentimentTimelineChart({ data = [], height = 220 }) {
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
        {payload.reverse().map((p) => (
          <div key={p.name} style={{ color: p.fill, fontWeight: 600, marginBottom: 2 }}>
            {p.name.charAt(0).toUpperCase() + p.name.slice(1)}: {Number(p.value).toFixed(1)}%
          </div>
        ))}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }} stackOffset="expand">
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} width={40} />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="bullish" stackId="1" stroke={COLORS.pnlGreen} fill={`${COLORS.pnlGreen}60`} strokeWidth={1.5} isAnimationActive={false} />
        <Area type="monotone" dataKey="neutral"  stackId="1" stroke={COLORS.warning}  fill={`${COLORS.warning}50`}  strokeWidth={1.5} isAnimationActive={false} />
        <Area type="monotone" dataKey="bearish"  stackId="1" stroke={COLORS.pnlRed}   fill={`${COLORS.pnlRed}55`}   strokeWidth={1.5} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
