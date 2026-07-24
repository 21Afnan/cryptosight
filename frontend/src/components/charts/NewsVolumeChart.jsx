import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * NewsVolumeChart — daily news/post volume bar chart.
 *
 * @param {Array}  data   - [{ date, posts: number }]
 * @param {number} height
 */
export default function NewsVolumeChart({ data = [], height = 200 }) {
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
        <div style={{ color: isDark ? COLORS.darkTextSecondary : '#6B7280', marginBottom: 2 }}>{label}</div>
        <div style={{ color: COLORS.accent, fontWeight: 600 }}>{payload[0].value} posts</div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }} barSize={12}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} width={36} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="posts" fill={`${COLORS.accent}80`} radius={[3, 3, 0, 0]} stroke={COLORS.accent} strokeWidth={1} />
      </BarChart>
    </ResponsiveContainer>
  );
}
