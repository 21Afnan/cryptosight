import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import { useTheme } from '@mui/material/styles';
import { COLORS, GRADIENTS } from '../../theme/theme';
import { useSidebar, SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH } from '../../context/SidebarContext';

// MUI Icons
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';
import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';
import HistoryRoundedIcon from '@mui/icons-material/HistoryRounded';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import SentimentSatisfiedAltRoundedIcon from '@mui/icons-material/SentimentSatisfiedAltRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import MenuOpenRoundedIcon from '@mui/icons-material/MenuOpenRounded';
import MenuRoundedIcon from '@mui/icons-material/MenuRounded';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import TuneRoundedIcon from '@mui/icons-material/TuneRounded';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: DashboardRoundedIcon },
  { label: 'Strategies', path: '/strategies', icon: ShowChartRoundedIcon },
  { label: 'Wallets', path: '/wallets', icon: AccountBalanceWalletRoundedIcon },
  { label: 'Execution', path: '/deployment', icon: PlayArrowRoundedIcon },
  { label: 'Backtests', path: '/backtests', icon: HistoryRoundedIcon },
  { label: 'Strategy Builder', path: '/strategy-builder', icon: TuneRoundedIcon },
  { label: 'Machine Learning', path: '/ml', icon: PsychologyRoundedIcon },
  { label: 'Sentiment', path: '/sentiment', icon: SentimentSatisfiedAltRoundedIcon },
];

export { SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH };

export default function Sidebar() {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const location = useLocation();
  const { collapsed, toggleSidebar, sidebarWidth } = useSidebar();

  const handleLogoClick = (e) => {
    if (location.pathname === '/') {
      e.preventDefault();
      window.location.reload();
    }
  };

  const sidebarBg = isDark ? GRADIENTS.sidebarDark : GRADIENTS.sidebar;

  return (
    <Box
      component="nav"
      aria-label="Main navigation"
      sx={{
        width: sidebarWidth,
        flexShrink: 0,
        height: '100vh',
        position: 'fixed',
        top: 0,
        left: 0,
        display: 'flex',
        flexDirection: 'column',
        background: sidebarBg,
        boxShadow: isDark
          ? '4px 0 24px rgba(0,0,0,0.3)'
          : '4px 0 24px rgba(15,40,25,0.12)',
        zIndex: 1200,
        overflowY: 'auto',
        overflowX: 'hidden',
        transition: 'width 220ms cubic-bezier(0.4, 0, 0.2, 1), background 200ms ease',
      }}
    >
      {/* Logo area */}
      <Box
        component={NavLink}
        to="/"
        onClick={handleLogoClick}
        sx={{
          px: collapsed ? 1.5 : 2.5,
          py: 2.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          mb: 0.5,
          justifyContent: collapsed ? 'center' : 'flex-start',
          textDecoration: 'none',
          cursor: 'pointer',
          transition: 'opacity 150ms ease',
          '&:hover': {
            opacity: 0.85,
          }
        }}
      >
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.06) 100%)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            border: '1px solid rgba(255,255,255,0.25)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Hexagonal blockchain eye shell */}
            <path d="M2 12L6.5 6H17.5L22 12L17.5 18H6.5L2 12Z" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="1.5" strokeLinejoin="round" />
            
            {/* Glowing iris lens */}
            <circle cx="12" cy="12" r="5.5" fill="rgba(94, 139, 110, 0.38)" stroke="#FFFFFF" strokeWidth="1.5" />
            
            {/* Upward trend line representing sight analytics */}
            <path d="M9.5 13.5L11.5 11.5L13.2 13.2L15.5 9.5" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M13.5 9.5H15.5V11.5" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Box>
        {!collapsed && (
          <Box sx={{ minWidth: 0 }}>
            <Typography
              sx={{
                fontWeight: 800,
                fontSize: '1rem',
                letterSpacing: '-0.02em',
                color: '#FFFFFF',
                lineHeight: 1.2,
                whiteSpace: 'nowrap',
              }}
            >
              CryptoSight
            </Typography>
            <Typography
              sx={{
                color: 'rgba(255,255,255,0.6)',
                fontSize: '0.625rem',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              Quant Platform
            </Typography>
          </Box>
        )}
      </Box>

      {/* Nav section label */}
      {!collapsed && (
        <Typography
          sx={{
            px: 2.5,
            py: 0.75,
            color: 'rgba(255,255,255,0.45)',
            fontSize: '0.6rem',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            fontWeight: 700,
            mb: 0.5,
          }}
        >
          Navigation
        </Typography>
      )}

      {/* Nav items */}
      <Box sx={{ px: 1.5, flexGrow: 1, mt: collapsed ? 1 : 0 }}>
        {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
          const isActive =
            path === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(path);

          const navContent = (
            <Box
              component={NavLink}
              to={path}
              id={`nav-${label.toLowerCase().replace(/\s+/g, '-')}`}
              aria-label={label}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'flex-start',
                gap: 1.25,
                px: collapsed ? 1 : 1.5,
                py: 1.1,
                mb: 0.5,
                borderRadius: '12px',
                textDecoration: 'none',
                transition: 'all 160ms ease',
                ...(isActive
                  ? {
                    background: 'rgba(255,255,255,0.95)',
                    color: COLORS.accent,
                    boxShadow: '0 2px 12px rgba(0,0,0,0.12)',
                  }
                  : {
                    color: 'rgba(255,255,255,0.75)',
                    '&:hover': {
                      background: 'rgba(255,255,255,0.12)',
                      color: '#FFFFFF',
                    },
                  }),
              }}
            >
              <Icon
                sx={{
                  fontSize: 20,
                  flexShrink: 0,
                  color: isActive ? COLORS.accent : 'inherit',
                }}
              />
              {!collapsed && (
                <Typography
                  sx={{
                    fontSize: '0.8125rem',
                    fontWeight: isActive ? 700 : 500,
                    lineHeight: 1,
                    color: 'inherit',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {label}
                </Typography>
              )}
            </Box>
          );

          if (collapsed) {
            return (
              <Tooltip key={path} title={label} placement="right" arrow>
                {navContent}
              </Tooltip>
            );
          }

          return <React.Fragment key={path}>{navContent}</React.Fragment>;
        })}
      </Box>

      {/* Collapse/expand toggle button */}
      <Box
        sx={{
          px: collapsed ? 1.5 : 2,
          py: 2,
          borderTop: '1px solid rgba(255,255,255,0.12)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
        }}
      >
        {!collapsed && (
          <Typography
            sx={{
              color: 'rgba(255,255,255,0.4)',
              fontSize: '0.625rem',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              fontWeight: 600,
            }}
          >
            v1.0.0
          </Typography>
        )}
        <Tooltip title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          <IconButton
            id="sidebar-toggle-btn"
            onClick={toggleSidebar}
            size="small"
            sx={{
              color: '#FFFFFF',
              background: 'rgba(255,255,255,0.15)',
              borderRadius: '999px',
              width: 32,
              height: 32,
              '&:hover': { background: 'rgba(255,255,255,0.28)' },
            }}
          >
            {collapsed ? <MenuRoundedIcon sx={{ fontSize: 18 }} /> : <MenuOpenRoundedIcon sx={{ fontSize: 18 }} />}
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}
