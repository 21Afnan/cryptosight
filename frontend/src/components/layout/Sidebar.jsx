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

const NAV_ITEMS = [
  { label: 'Dashboard',        path: '/',           icon: DashboardRoundedIcon },
  { label: 'Strategies',       path: '/strategies', icon: ShowChartRoundedIcon },
  { label: 'Wallets',          path: '/wallets',    icon: AccountBalanceWalletRoundedIcon },
  { label: 'Deployment',       path: '/deployment', icon: RocketLaunchRoundedIcon },
  { label: 'Backtests',        path: '/backtests',  icon: HistoryRoundedIcon },
  { label: 'Machine Learning', path: '/ml',         icon: PsychologyRoundedIcon },
  { label: 'Sentiment',        path: '/sentiment',  icon: SentimentSatisfiedAltRoundedIcon },
];

export { SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH };

export default function Sidebar() {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const location = useLocation();
  const { collapsed, toggleSidebar, sidebarWidth } = useSidebar();

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
        sx={{
          px: collapsed ? 1.5 : 2.5,
          py: 2.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          mb: 0.5,
          justifyContent: collapsed ? 'center' : 'flex-start',
        }}
      >
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: '12px',
            background: 'rgba(255,255,255,0.22)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            border: '1px solid rgba(255,255,255,0.2)',
          }}
        >
          <ShowChartRoundedIcon sx={{ color: '#FFFFFF', fontSize: 20 }} />
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
