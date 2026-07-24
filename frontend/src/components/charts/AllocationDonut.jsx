import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * AllocationDonut — soft-styled recharts donut chart.
 * Used on Dashboard (portfolio by exchange), Wallets, ML page (model types),
 * Sentiment page (bullish/bearish/neutral distribution).
 *
 * Palette: first 5 entries use the secondary accent family; overrideable.
 *
 * @param {Array}     data        - [{ name: string, value: number, color?: string }]
 * @param {string}    centerLabel - Top label in the hole (e.g. "Total")
 * @param {string}    centerValue - Main value shown in the hole
 * @param {number}    size        - ResponsiveContainer height
 * @param {boolean}   showLegend  - Show inline legend below chart
 */

const DEFAULT_COLORS = [
  COLORS.accent,       // sage green
  COLORS.secondaryA,   // soft coral
  COLORS.secondaryB,   // soft lavender
  COLORS.secondaryC,   // soft amber
  COLORS.secondaryD,   // soft sky
  COLORS.secondaryE,   // soft mint
  COLORS.pnlGreen,
  COLORS.warning,
];

export default function AllocationDonut({
  data = [],
  centerLabel = 'Total',
  centerValue,
  size = 200,
  showLegend = true,
}) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const colored = data.map((d, i) => ({
    ...d,
    fill: d.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length],
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const entry = payload[0].payload;
    return (
      <Box
        sx={{
          background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
          borderRadius: '12px',
          p: 1.5,
          boxShadow: isDark
            ? '0 4px 20px rgba(0,0,0,0.4)'
            : '0 4px 20px rgba(15,40,25,0.1)',
          fontSize: 12,
          fontFamily: '"Inter", sans-serif',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: entry.fill, flexShrink: 0 }} />
          <Typography variant="body2" sx={{ fontWeight: 600 }}>{entry.name}</Typography>
        </Box>
        <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mt: 0.25, fontVariantNumeric: 'tabular-nums' }}>
          {typeof entry.value === 'number' && entry.value < 2 ? `${(entry.value * 100).toFixed(1)}%` : entry.value?.toLocaleString()}
        </Typography>
      </Box>
    );
  };

  return (
    <Box>
      <Box sx={{ position: 'relative', height: size }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={colored}
              cx="50%"
              cy="50%"
              innerRadius={size * 0.27}
              outerRadius={size * 0.44}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
              isAnimationActive
              animationDuration={600}
            >
              {colored.map((entry, idx) => (
                <Cell key={idx} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>

        {/* Center label */}
        {centerValue && (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none',
            }}
          >
            <Typography
              sx={{
                fontSize: '0.6rem',
                fontWeight: 700,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: theme.palette.text.secondary,
                lineHeight: 1,
              }}
            >
              {centerLabel}
            </Typography>
            <Typography
              sx={{
                fontSize: '1.125rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                color: theme.palette.text.primary,
                fontVariantNumeric: 'tabular-nums',
                lineHeight: 1.2,
                mt: 0.25,
              }}
            >
              {centerValue}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Legend */}
      {showLegend && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'center', mt: 1 }}>
          {colored.map((entry) => (
            <Box key={entry.name} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: entry.fill, flexShrink: 0 }} />
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, textTransform: 'none', letterSpacing: 0, fontSize: '0.6875rem', fontWeight: 500 }}>
                {entry.name}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
