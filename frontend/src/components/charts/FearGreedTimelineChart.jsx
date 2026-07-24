import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * FearGreedTimelineChart — Area chart plotting Fear & Greed Index (0–100) over 90 days.
 *
 * @param {Array}  data   - [{ date: 'YYYY-MM-DD', value: number }]
 * @param {number} height
 */
export default function FearGreedTimelineChart({ data = [], height = 240 }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const val = payload[0].value;
    let labelText = 'Neutral';
    let color = COLORS.warning;

    if (val <= 20) { labelText = 'Extreme Fear'; color = COLORS.pnlRed; }
    else if (val <= 40) { labelText = 'Fear'; color = '#F97316'; }
    else if (val <= 60) { labelText = 'Neutral'; color = COLORS.warning; }
    else if (val <= 80) { labelText = 'Greed'; color = '#84CC16'; }
    else { labelText = 'Extreme Greed'; color = COLORS.pnlGreen; }

    return (
      <div style={{
        background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
        borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: '"Inter", sans-serif',
      }}>
        <div style={{ color: isDark ? COLORS.darkTextSecondary : '#6B7280', marginBottom: 4 }}>{label}</div>
        <div style={{ color, fontWeight: 700 }}>
          Index: {val} ({labelText})
        </div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, bottom: 4, left: -20 }}>
        <defs>
          <linearGradient id="fearGreedGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={COLORS.accent} stopOpacity={0.4} />
            <stop offset="95%" stopColor={COLORS.accent} stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          ticks={[0, 25, 50, 75, 100]}
          tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={50} stroke={isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} strokeDasharray="3 3" />
        <Area
          type="monotone"
          dataKey="value"
          stroke={COLORS.accent}
          strokeWidth={2}
          fill="url(#fearGreedGrad)"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
