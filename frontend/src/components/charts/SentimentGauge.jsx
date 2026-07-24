import React from 'react';
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { COLORS } from '../../theme/theme';

/**
 * SentimentGauge — circular score gauge widget matching Image 2 with green gradient arc,
 * central bold score display, soft radial green glow, and smooth hover scale effect.
 *
 * @param {number} value   - 0–100 score value
 * @param {number} size    - Widget size in px
 * @param {string} label   - Sub-label under main score (e.g. "PREDICTED")
 * @param {string} actual  - Bottom note text (e.g. "Actual: 68")
 */
export default function SentimentGauge({
  value = 68,
  size = 240,
  label = 'PREDICTED',
  actual,
}) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const radius = (size - 32) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(100, Math.max(0, value)) / 100;
  const strokeDashoffset = circumference * (1 - pct);

  // Soft fintech green palette
  const gaugeGreen = COLORS.accent; // #5E8B6E
  const brightGreen = COLORS.pnlGreen; // #22C55E
  const trackColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(94,139,110,0.12)';

  let moodLabel = 'Greed';
  if (value <= 20) moodLabel = 'Extreme Fear';
  else if (value <= 40) moodLabel = 'Fear';
  else if (value <= 60) moodLabel = 'Neutral';
  else if (value <= 80) moodLabel = 'Greed';
  else moodLabel = 'Extreme Greed';

  const actualText = actual ?? `Actual: ${value}`;

  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: '50%',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        mx: 'auto',
        my: 1,
        // Requirement from Image 2: Soft radial green glow background
        background: isDark
          ? `radial-gradient(circle, rgba(94, 139, 110, 0.25) 0%, rgba(24, 28, 26, 0.8) 70%)`
          : `radial-gradient(circle, rgba(94, 139, 110, 0.18) 0%, rgba(255, 255, 255, 0.9) 70%)`,
        boxShadow: isDark
          ? '0 12px 40px rgba(0, 0, 0, 0.4), inset 0 0 20px rgba(94, 139, 110, 0.15)'
          : '0 12px 40px rgba(94, 139, 110, 0.22), inset 0 0 20px rgba(255, 255, 255, 0.8)',
        transition: 'all 280ms cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: 'pointer',
        // Requirement from Image 2: Hover scale bigger with green glow shadow
        '&:hover': {
          transform: 'scale(1.08)',
          boxShadow: isDark
            ? `0 20px 50px rgba(94, 139, 110, 0.45), 0 0 0 2px ${COLORS.accent}`
            : `0 20px 50px rgba(94, 139, 110, 0.38), 0 0 0 2px ${COLORS.accent}`,
          '& .gauge-score-value': {
            color: brightGreen,
            transform: 'scale(1.05)',
          },
        },
      }}
    >
      <svg
        width={size}
        height={size}
        style={{ position: 'absolute', top: 0, left: 0, transform: 'rotate(-90deg)' }}
      >
        <defs>
          <linearGradient id="gaugeGreenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={COLORS.accent} />
            <stop offset="100%" stopColor={brightGreen} />
          </linearGradient>
        </defs>
        {/* Background track circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={trackColor}
          strokeWidth={14}
          fill="none"
        />
        {/* Value arc fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#gaugeGreenGrad)"
          strokeWidth={14}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 800ms ease' }}
        />
      </svg>

      {/* Central Value Content (Matching Image 2) */}
      <Box
        sx={{
          textAlign: 'center',
          zIndex: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        <Typography
          className="gauge-score-value"
          sx={{
            fontSize: '3.2rem',
            fontWeight: 900,
            lineHeight: 1,
            color: gaugeGreen,
            letterSpacing: '-0.03em',
            fontVariantNumeric: 'tabular-nums',
            transition: 'all 240ms ease',
          }}
        >
          {value}
        </Typography>

        <Typography
          variant="caption"
          sx={{
            fontSize: '0.6875rem',
            fontWeight: 800,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: isDark ? COLORS.darkTextSecondary : COLORS.accent,
            mt: 0.5,
          }}
        >
          {label}
        </Typography>

        <Typography
          variant="body2"
          sx={{
            fontSize: '0.78125rem',
            fontWeight: 700,
            color: theme.palette.text.secondary,
            mt: 0.25,
          }}
        >
          {actualText} ({moodLabel})
        </Typography>
      </Box>
    </Box>
  );
}
