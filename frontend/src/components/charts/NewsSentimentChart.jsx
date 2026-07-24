import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * NewsSentimentChart — grouped bars for bullish/bearish/neutral per day.
 * Separate from NewsVolumeChart per spec.
 *
 * @param {Array}  data   - [{ date, bullish, bearish, neutral }] (counts)
 * @param {number} height
 */
export default function NewsSentimentChart({ data = [], height = 220 }) {
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
          <div key={p.name} style={{ color: p.fill, fontWeight: 600, marginBottom: 2 }}>
            {p.name.charAt(0).toUpperCase() + p.name.slice(1)}: {p.value}
          </div>
        ))}
      </div>
    );
  };

  const renderLegend = ({ payload }) => (
    <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 6 }}>
      {payload.map((entry) => (
        <span key={entry.value} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: isDark ? COLORS.darkTextSecondary : '#6B7280' }}>
          <span style={{ width: 10, height: 10, background: entry.color, borderRadius: 2, display: 'inline-block' }} />
          {entry.value.charAt(0).toUpperCase() + entry.value.slice(1)}
        </span>
      ))}
    </div>
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }} barSize={8} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} width={36} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }} />
        <Legend content={renderLegend} />
        <Bar dataKey="bullish" fill={`${COLORS.pnlGreen}90`} radius={[2, 2, 0, 0]} />
        <Bar dataKey="neutral"  fill={`${COLORS.warning}80`}  radius={[2, 2, 0, 0]} />
        <Bar dataKey="bearish"  fill={`${COLORS.pnlRed}80`}   radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
