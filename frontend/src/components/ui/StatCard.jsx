import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import SparklineChart from '../charts/SparklineChart';
import { COLORS, ICON_BUBBLE_COLORS } from '../../theme/theme';

/**
 * StatCard — KPI card with colored icon bubble, value, delta, sparkline, and soft fintech hover effects.
 *
 * @param {string}    title
 * @param {string}    value
 * @param {string}    delta
 * @param {string}    deltaType    - 'positive' | 'negative' | 'neutral'
 * @param {ReactNode} icon
 * @param {Array}     sparkData
 * @param {string}    color
 * @param {number}    colorIndex   - slot for ICON_BUBBLE_COLORS
 */
export default function StatCard({
  title,
  value,
  delta,
  deltaType = 'neutral',
  icon,
  sparkData,
  color,
  colorIndex = 0,
}) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const bubble = ICON_BUBBLE_COLORS[colorIndex % ICON_BUBBLE_COLORS.length];

  const deltaColor =
    deltaType === 'positive'
      ? COLORS.pnlGreen
      : deltaType === 'negative'
      ? COLORS.pnlRed
      : theme.palette.text.secondary;

  const deltaPrefix =
    deltaType === 'positive' ? '↑ ' : deltaType === 'negative' ? '↓ ' : '';

  const lineColor = color ?? (deltaType === 'positive' ? COLORS.pnlGreen : deltaType === 'negative' ? COLORS.pnlRed : COLORS.accent);

  return (
    <Card
      sx={{
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer',
        transition: 'all 240ms cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: isDark
            ? '0 16px 36px rgba(0,0,0,0.5), 0 0 0 1px rgba(94,139,110,0.25)'
            : '0 16px 36px rgba(94,139,110,0.18), 0 0 0 1px rgba(94,139,110,0.25)',
          '& .stat-icon-bubble': {
            transform: 'scale(1.08) rotate(4deg)',
            boxShadow: `0 6px 16px ${bubble.icon}35`,
          },
        },
      }}
    >
      {/* Tinted top-right corner decoration */}
      <Box
        sx={{
          position: 'absolute',
          top: -20,
          right: -20,
          width: 80,
          height: 80,
          borderRadius: '50%',
          background: isDark
            ? `${bubble.bg.replace('rgba', 'rgba').replace(/,\s*[\d.]+\)/, ', 0.06)')}`
            : bubble.bg,
          pointerEvents: 'none',
        }}
      />

      <CardContent
        sx={{
          p: '20px !important',
          display: 'flex',
          flexDirection: 'column',
          justify: 'space-between',
          gap: 1.5,
          height: '100%',
        }}
      >
        {/* Top row: title + icon bubble */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flexGrow: 1, minWidth: 0, pr: 1 }}>
            <Typography
              variant="caption"
              sx={{
                color: theme.palette.text.secondary,
                display: 'block',
                mb: 0.75,
                fontSize: '0.6875rem',
                fontWeight: 600,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              {title}
            </Typography>
            <Typography
              sx={{
                fontVariantNumeric: 'tabular-nums',
                fontWeight: 700,
                fontSize: '1.4rem',
                lineHeight: 1.2,
                color: theme.palette.text.primary,
                letterSpacing: '-0.02em',
                wordBreak: 'break-word',
              }}
            >
              {value}
            </Typography>
          </Box>

          {/* Icon bubble */}
          {icon && (
            <Box
              className="stat-icon-bubble"
              sx={{
                width: 44,
                height: 44,
                borderRadius: '14px',
                background: bubble.bg,
                color: bubble.icon,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 200ms ease',
                '& svg': { fontSize: 22 },
              }}
            >
              {icon}
            </Box>
          )}
        </Box>

        {/* Bottom row: delta text + sparkline */}
        <Box sx={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', mt: 'auto' }}>
          {delta && (
            <Typography
              variant="body2"
              sx={{
                color: deltaColor,
                fontWeight: 600,
                fontSize: '0.75rem',
                lineHeight: 1.2,
              }}
            >
              {deltaPrefix}{delta}
            </Typography>
          )}

          {/* Optional inline sparkline */}
          {sparkData && sparkData.length > 0 && (
            <Box sx={{ width: 68, height: 28, flexShrink: 0, ml: 'auto' }}>
              <SparklineChart data={sparkData} color={lineColor} height={28} />
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
