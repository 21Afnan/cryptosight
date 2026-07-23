import React from 'react';
import {
  AppBar, Toolbar, Typography, Box, IconButton,
  TextField, InputAdornment, Tooltip, Avatar, Chip,
  Badge,
} from '@mui/material';
import SearchRoundedIcon       from '@mui/icons-material/SearchRounded';
import LightModeRoundedIcon    from '@mui/icons-material/LightModeRounded';
import DarkModeRoundedIcon     from '@mui/icons-material/DarkModeRounded';
import NotificationsNoneRoundedIcon from '@mui/icons-material/NotificationsNoneRounded';
import { useLocation }         from 'react-router-dom';
import { COLORS, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED } from '../../theme/theme';

const PAGE_TITLES = {
  '/':           'Dashboard',
  '/strategies': 'Strategies',
  '/wallets':    'Wallet Management',
  '/deployment': 'Live Deployment',
  '/backtests':  'Backtests',
  '/ml':         'Machine Learning',
  '/sentiment':  'NLP & Sentiment',
};

const Topbar = ({ mode, onToggleMode, sidebarCollapsed }) => {
  const location = useLocation();
  const sidebarW = sidebarCollapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED;

  const getTitle = () => {
    for (const [key, val] of Object.entries(PAGE_TITLES)) {
      if (key === '/' ? location.pathname === '/' : location.pathname.startsWith(key)) {
        return val;
      }
    }
    return 'CryptoSight';
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        width: `calc(100% - ${sidebarW}px)`,
        ml: `${sidebarW}px`,
        transition: 'all 0.3s cubic-bezier(.4,0,.2,1)',
        background: (t) =>
          t.palette.mode === 'dark'
            ? 'rgba(6,7,14,0.8)'
            : 'rgba(245,243,255,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid',
        borderColor: 'divider',
        color: 'text.primary',
      }}
    >
      <Toolbar sx={{ gap: 2, minHeight: '64px !important' }}>
        {/* Page Title */}
        <Box flexGrow={1}>
          <Typography variant="h6" fontWeight={800} lineHeight={1.1}>
            {getTitle()}
          </Typography>
          <Typography variant="caption" color="text.secondary" fontWeight={500} fontSize="0.7rem">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
            })}
          </Typography>
        </Box>


        {/* Live pulse badge */}
        <Chip
          label="● LIVE"
          size="small"
          sx={{
            background: 'rgba(52,211,153,0.12)',
            color: COLORS.green,
            fontWeight: 800,
            fontSize: '0.68rem',
            letterSpacing: '0.06em',
            border: `1px solid rgba(52,211,153,0.25)`,
            animation: 'livePulse 2.5s ease-in-out infinite',
            '@keyframes livePulse': {
              '0%, 100%': { boxShadow: `0 0 0 0 rgba(52,211,153,0.2)` },
              '50%':       { boxShadow: `0 0 0 6px rgba(52,211,153,0)` },
            },
          }}
        />

        {/* Notifications */}
        <Tooltip title="Notifications">
          <IconButton
            size="small"
            sx={{
              transition: 'transform 0.2s',
              '&:hover': { transform: 'scale(1.1)' },
            }}
          >
            <Badge badgeContent={3} color="error" variant="dot">
              <NotificationsNoneRoundedIcon fontSize="small" />
            </Badge>
          </IconButton>
        </Tooltip>

        {/* Dark / Light toggle */}
        <Tooltip title={mode === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
          <IconButton
            onClick={onToggleMode}
            size="small"
            sx={{
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'rotate(30deg) scale(1.1)',
                background: mode === 'dark'
                  ? 'rgba(251,191,36,0.12)'
                  : 'rgba(124,58,237,0.1)',
              },
            }}
          >
            {mode === 'dark'
              ? <LightModeRoundedIcon fontSize="small" sx={{ color: COLORS.amber }} />
              : <DarkModeRoundedIcon  fontSize="small" sx={{ color: COLORS.purple }} />
            }
          </IconButton>
        </Tooltip>

        {/* User Avatar */}
        <Tooltip title="Profile">
          <Avatar
            sx={{
              width: 36,
              height: 36,
              background: `linear-gradient(135deg, ${COLORS.purple}, ${COLORS.cyan})`,
              fontSize: '0.8rem',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: `0 2px 12px rgba(124,58,237,0.3)`,
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'scale(1.08)',
                boxShadow: `0 4px 20px rgba(124,58,237,0.4)`,
              },
            }}
          >
            CS
          </Avatar>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
};

export default Topbar;
