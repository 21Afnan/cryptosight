import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

/**
 * EmptyState — shown when a table/list has no data.
 * Never shows a blank box. Always has an icon + message.
 */
export default function EmptyState({
  icon: Icon,
  title = 'No data found',
  description = 'Try adjusting your search or filter criteria.',
  action,
  sx = {},
}) {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        px: 3,
        textAlign: 'center',
        ...sx,
      }}
    >
      {Icon && (
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '16px',
            background:
              theme.palette.mode === 'dark'
                ? 'rgba(255,255,255,0.04)'
                : 'rgba(0,0,0,0.04)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2.5,
            color: theme.palette.text.disabled,
          }}
        >
          <Icon sx={{ fontSize: 32 }} />
        </Box>
      )}
      <Typography
        variant="h5"
        sx={{ color: theme.palette.text.primary, mb: 0.75, fontWeight: 600 }}
      >
        {title}
      </Typography>
      <Typography
        variant="body2"
        sx={{ color: theme.palette.text.secondary, maxWidth: 360, lineHeight: 1.6 }}
      >
        {description}
      </Typography>
      {action && <Box sx={{ mt: 3 }}>{action}</Box>}
    </Box>
  );
}
