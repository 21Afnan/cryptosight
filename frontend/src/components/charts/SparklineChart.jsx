import React from 'react';
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts';
import { useTheme } from '@mui/material/styles';

/**
 * SparklineChart — tiny inline line chart for StatCards.
 * No axes, no labels — pure visual trend indicator.
 *
 * @param {Array}  data   - [{ value: number }]
 * @param {string} color  - Line color
 * @param {number} height - Default 44
 */
export default function SparklineChart({ data = [], color, height = 44 }) {
  const theme = useTheme();
  const lineColor = color ?? theme.palette.primary.main;

  if (!data || data.length < 2) return null;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={lineColor}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
        <Tooltip
          contentStyle={{ display: 'none' }}
          cursor={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
