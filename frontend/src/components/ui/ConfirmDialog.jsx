import React from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import Box from '@mui/material/Box';
import { COLORS } from '../../theme/theme';

/**
 * ConfirmDialog — required before every destructive action.
 * Never use native browser confirm() — this is the safe, framework-native alternative.
 *
 * Props:
 *   open        {boolean}
 *   onClose     {Function} — called on cancel or backdrop click
 *   onConfirm   {Function} — called on confirm click
 *   title       {string}
 *   description {string}
 *   confirmLabel {string} — defaults to 'Confirm'
 *   danger      {boolean} — renders confirm button in error/red style
 */
export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  description = 'Are you sure you want to proceed? This action cannot be undone.',
  confirmLabel = 'Confirm',
  danger = true,
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xs"
      fullWidth
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <DialogTitle id="confirm-dialog-title">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: '8px',
              background: danger ? 'rgba(234,57,67,0.12)' : 'rgba(240,185,11,0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: danger ? COLORS.pnlRed : COLORS.warning,
              flexShrink: 0,
            }}
          >
            <WarningAmberRoundedIcon sx={{ fontSize: 20 }} />
          </Box>
          {title}
        </Box>
      </DialogTitle>
      <DialogContent>
        <DialogContentText id="confirm-dialog-description" sx={{ fontSize: '0.875rem' }}>
          {description}
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2.5, gap: 1 }}>
        <Button
          id="confirm-dialog-cancel-btn"
          onClick={onClose}
          variant="outlined"
          size="small"
          sx={{ flex: 1 }}
        >
          Cancel
        </Button>
        <Button
          id="confirm-dialog-confirm-btn"
          onClick={onConfirm}
          variant="contained"
          size="small"
          sx={{
            flex: 1,
            ...(danger && {
              background: COLORS.pnlRed,
              '&:hover': { background: '#c62828', filter: 'none' },
            }),
          }}
        >
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
