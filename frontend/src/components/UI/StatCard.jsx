import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { ResponsiveContainer, AreaChart, Area } from 'recharts';

/**
 * StatCard — Premium glassmorphism KPI widget with gradient icon,
 * animated sparkline, and hover glow effect.
 */
const StatCard = ({
  title,
  value,
  icon,
  gradient,
  trend,
  trendColor = '#7C3AED',
}) => {
  const valueStr = String(value);
  const valueColor =
    valueStr.startsWith('+') ? '#34D399' :
      valueStr.startsWith('-') ? '#FB7185' :
        'text.primary';

  // Unique gradient ID per card (avoids SVG id clashes)
  const gradientId = `spark-${title.replace(/[^a-zA-Z0-9]/g, '-')}`;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.2,
        height: '100%',
        borderRadius: '16px', // Unique neat square/rectangle shape, not oval
        position: 'relative',
        overflow: 'hidden',
        cursor: 'default',
        border: (t) => `1px solid ${t.palette.divider}`,
        transition: 'all 0.3s cubic-bezier(.4,0,.2,1)',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: (t) => t.palette.mode === 'dark'
            ? '0 12px 28px rgba(124,58,237,0.22), 0 0 0 1px rgba(124,58,237,0.3)'
            : '0 12px 28px rgba(109,40,217,0.12), 0 0 0 1px rgba(109,40,217,0.2)',
        },
        /* subtle gradient glow behind the card */
        '&::before': {
          content: '""',
          position: 'absolute',
          top: -1,
          left: -1,
          right: -1,
          height: 3,
          background: gradient || 'linear-gradient(90deg, #7C3AED, #22D3EE)',
          opacity: 0.8,
          borderRadius: '16px 16px 0 0',
        },
      }}
    >
      {/* Top row: icon + value */}
      <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={1}>
        {/* Icon bubble with gradient */}
        <Box
          sx={{
            width: 46,
            height: 46,
            borderRadius: 3,
            background: gradient || 'linear-gradient(135deg, #7C3AED, #A78BFA)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 24,
            flexShrink: 0,
            boxShadow: `0 4px 16px rgba(0,0,0,0.2)`,
            transition: 'transform 0.3s ease',
            '&:hover': { transform: 'rotate(-8deg) scale(1.08)' },
          }}
        >
          {icon}
        </Box>

        {/* Value */}
        <Box textAlign="right">
          <Typography
            variant="h5"
            fontWeight={800}
            sx={{
              color: valueColor,
              lineHeight: 1.1,
              fontSize: '1.45rem',
              letterSpacing: '-0.02em',
            }}
          >
            {value}
          </Typography>
        </Box>
      </Box>

      {/* Title */}
      <Typography
        variant="caption"
        color="text.secondary"
        fontWeight={600}
        sx={{
          display: 'block',
          letterSpacing: '0.04em',
          fontSize: '0.72rem',
          textTransform: 'uppercase',
        }}
      >
        {title}
      </Typography>

      {/* Sparkline chart */}
      {trend && (
        <Box sx={{ mt: 1.5, height: 44, mx: -0.5 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trend} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={trendColor} stopOpacity={0.35} />
                  <stop offset="50%" stopColor={trendColor} stopOpacity={0.15} />
                  <stop offset="100%" stopColor={trendColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="v"
                stroke={trendColor}
                strokeWidth={2.5}
                fill={`url(#${gradientId})`}
                dot={false}
                animationDuration={1200}
                animationEasing="ease-out"
                style={{
                  filter: `drop-shadow(0px 3px 6px ${trendColor}88)`,
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Paper>
  );
};

export default StatCard;
