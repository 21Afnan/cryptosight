import React from 'react';
import Chip from '@mui/material/Chip';
import Box from '@mui/material/Box';
import { COLORS } from '../../theme/theme';

/**
 * StatusChip — soft filled pill for all status/side/signal displays.
 * Design: no border, filled background at low opacity, vivid text color.
 * Full pill shape (999px radius) consistent with the new button style.
 *
 * Supported statuses: active, paused, stopped, connected, error, disabled,
 * pending, running, completed, failed, long, short, neutral, open, closed,
 * filled, cancelled, buy, sell, trained, stale
 */

const STATUS_MAP = {
  active:    { color: COLORS.pnlGreen,    label: 'Active' },
  paused:    { color: COLORS.warning,     label: 'Paused' },
  stopped:   { color: COLORS.pnlRed,      label: 'Stopped' },
  connected: { color: COLORS.pnlGreen,    label: 'Connected' },
  error:     { color: COLORS.pnlRed,      label: 'Error' },
  disabled:  { color: COLORS.darkTextSecondary, label: 'Disabled' },
  pending:   { color: COLORS.warning,     label: 'Pending' },
  running:   { color: COLORS.accentLight, label: 'Running' },
  completed: { color: COLORS.pnlGreen,    label: 'Completed' },
  failed:    { color: COLORS.pnlRed,      label: 'Failed' },
  long:      { color: COLORS.pnlGreen,    label: 'Long' },
  short:     { color: COLORS.pnlRed,      label: 'Short' },
  flat:      { color: COLORS.warning,     label: 'Flat' },
  neutral:   { color: COLORS.warning,     label: 'Neutral' },
  open:      { color: COLORS.accentLight, label: 'Open' },
  closed:    { color: COLORS.darkTextSecondary, label: 'Closed' },
  filled:    { color: COLORS.pnlGreen,    label: 'Filled' },
  cancelled: { color: COLORS.pnlRed,      label: 'Cancelled' },
  buy:       { color: COLORS.pnlGreen,    label: 'Buy' },
  sell:      { color: COLORS.pnlRed,      label: 'Sell' },
  trained:   { color: COLORS.pnlGreen,    label: 'Trained' },
  stale:     { color: COLORS.warning,     label: 'Stale' },
};

export default function StatusChip({ status, label, size = 'small' }) {
  const key = status?.toLowerCase();
  const cfg = STATUS_MAP[key] ?? {
    color: '#8B93A7',
    label: status ?? '—',
  };
  const displayLabel = label ?? cfg.label;

  // Derive a very soft background from the semantic color
  const bgAlpha = key === 'disabled' || key === 'closed' ? '0.10' : '0.12';

  return (
    <Box
      component="span"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        px: '10px',
        py: '3px',
        borderRadius: '999px',
        fontSize: size === 'medium' ? '0.75rem' : '0.6875rem',
        fontWeight: 700,
        letterSpacing: '0.03em',
        lineHeight: 1.6,
        color: cfg.color,
        background: `${cfg.color}1E`,  // ~12% opacity hex
        whiteSpace: 'nowrap',
        userSelect: 'none',
      }}
    >
      {/* Dot indicator */}
      <Box
        component="span"
        sx={{
          width: 5,
          height: 5,
          borderRadius: '50%',
          background: cfg.color,
          flexShrink: 0,
          display: 'inline-block',
        }}
      />
      {displayLabel}
    </Box>
  );
}
