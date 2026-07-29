import React, { useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import InputBase from '@mui/material/InputBase';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';
import { ThemeContext } from '../../App';
import { useSidebar } from '../../context/SidebarContext';
import { useSearch } from '../../context/SearchContext';

import DarkModeRoundedIcon from '@mui/icons-material/DarkModeRounded';
import LightModeRoundedIcon from '@mui/icons-material/LightModeRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/strategies': 'Strategy List',
  '/wallets': 'Wallet Management',
  '/deployment': 'Active Executions',
  '/backtests': 'Backtest Requests',
  '/ml': 'Machine Learning Models',
  '/sentiment': 'Sentiment Analysis',
};

function getRouteTitle(pathname, passedTitle) {
  if (passedTitle) return passedTitle;
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];

  if (pathname.startsWith('/strategies/')) return 'Strategy Details';
  if (pathname.startsWith('/deployment/')) return 'Execution Details';
  if (pathname.startsWith('/backtests/')) return 'Backtest Details';
  if (pathname.startsWith('/ml/')) return 'Model Details';

  return 'Trading Terminal';
}

/**
 * Topbar — Sage Green Crystal Glass Navbar with Real PostgreSQL DB Connection Health Status Sign (Active / Inactive)
 */
export default function Topbar({ title }) {
  const theme = useTheme();
  const location = useLocation();
  const { toggleTheme } = useContext(ThemeContext);
  const { sidebarWidth } = useSidebar();
  const { query, setQuery } = useSearch();
  const isDark = theme.palette.mode === 'dark';

  const pageTitle = getRouteTitle(location.pathname, title);



  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        left: sidebarWidth,
        width: `calc(100% - ${sidebarWidth}px)`,
        background: isDark
          ? 'rgba(30, 48, 38, 0.82)'
          : 'rgba(235, 243, 237, 0.88)',
        backdropFilter: 'blur(24px) saturate(190%)',
        borderBottom: 'none',
        borderTop: isDark
          ? '1px solid rgba(255, 255, 255, 0.12)'
          : '1px solid rgba(255, 255, 255, 0.7)',
        boxShadow: isDark
          ? '0 10px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
          : '0 10px 32px rgba(15, 40, 25, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.8)',
        zIndex: 1100,
        transition: 'left 220ms cubic-bezier(0.4, 0, 0.2, 1), width 220ms cubic-bezier(0.4, 0, 0.2, 1), background 240ms ease',
      }}
    >
      <Toolbar sx={{ minHeight: '64px !important', px: 3, gap: 2 }}>
        {/* Page Title — Rendered directly on glass topbar with text-shadow hover feedback */}
        <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}>
          <Typography
            variant="h4"
            component="h1"
            sx={{
              color: COLORS.accent,
              textShadow: `0 4px 16px ${COLORS.accent}60`,
              fontWeight: 800,
              fontSize: '1.25rem',
              lineHeight: 1.2,
              letterSpacing: '-0.02em',
              cursor: 'default',
              transition: 'all 200ms ease',
            }}
          >
            {pageTitle}
          </Typography>
        </Box>



        {/* Global Search Bar */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: isDark
              ? 'rgba(255, 255, 255, 0.08)'
              : 'rgba(255, 255, 255, 0.9)',
            borderTop: isDark
              ? '1px solid rgba(255, 255, 255, 0.15)'
              : '1px solid rgba(255, 255, 255, 0.8)',
            borderRadius: '999px',
            px: 2.2,
            py: 0.75,
            boxShadow: isDark
              ? '0 4px 16px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.1)'
              : '0 4px 16px rgba(15,40,25,0.08), inset 0 1px 0 rgba(255,255,255,0.9)',
            width: 240,
            transition: 'all 240ms cubic-bezier(0.4, 0, 0.2, 1)',
            '&:focus-within': {
              boxShadow: `0 8px 24px rgba(94, 139, 110, 0.3), 0 0 0 2px ${COLORS.accent}`,
              width: 280,
            },
          }}
        >
          <InputBase
            placeholder="Search…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            sx={{
              fontSize: '0.8125rem',
              color: theme.palette.text.primary,
              '& input::placeholder': { color: theme.palette.text.secondary, opacity: 0.9 },
              flex: 1,
            }}
            inputProps={{ 'aria-label': 'Search' }}
          />
          <SearchRoundedIcon
            sx={{
              fontSize: 18,
              color: isDark ? COLORS.darkTextSecondary : COLORS.accent,
              flexShrink: 0,
              ml: 1,
            }}
          />
        </Box>

        {/* Theme toggle */}
        <Tooltip title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}>
          <IconButton
            id="theme-toggle-btn"
            onClick={toggleTheme}
            size="small"
            aria-label="Toggle theme"
            sx={{
              color: theme.palette.text.secondary,
              background: isDark ? 'rgba(255,255,255,0.08)' : '#FFFFFF',
              borderRadius: '999px',
              width: 40,
              height: 40,
              boxShadow: isDark
                ? '0 4px 14px rgba(0,0,0,0.25)'
                : '0 4px 14px rgba(15,40,25,0.08)',
              transition: 'all 200ms ease',
              '&:hover': {
                color: COLORS.accent,
                transform: 'scale(1.05)',
                background: isDark ? 'rgba(94,139,110,0.2)' : COLORS.accentSurface,
              },
            }}
          >
            {isDark ? (
              <LightModeRoundedIcon sx={{ fontSize: 18 }} />
            ) : (
              <DarkModeRoundedIcon sx={{ fontSize: 18 }} />
            )}
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
