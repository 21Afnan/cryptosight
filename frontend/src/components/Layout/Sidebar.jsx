import React from 'react';
import {
  Box, Drawer, List, ListItem, ListItemButton,
  ListItemIcon, ListItemText, Typography, Divider,
  Tooltip, IconButton,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

import DashboardRoundedIcon          from '@mui/icons-material/DashboardRounded';
import ShowChartRoundedIcon          from '@mui/icons-material/ShowChartRounded';
import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';
import RocketLaunchRoundedIcon       from '@mui/icons-material/RocketLaunchRounded';
import HistoryRoundedIcon            from '@mui/icons-material/HistoryRounded';
import PsychologyRoundedIcon         from '@mui/icons-material/PsychologyRounded';
import InsightsRoundedIcon           from '@mui/icons-material/InsightsRounded';
import ChevronLeftRoundedIcon        from '@mui/icons-material/ChevronLeftRounded';
import ChevronRightRoundedIcon       from '@mui/icons-material/ChevronRightRounded';
import TrendingUpRoundedIcon         from '@mui/icons-material/TrendingUpRounded';

import { SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED, COLORS } from '../../theme/theme';

const NAV_ITEMS = [
  { label: 'Dashboard',         path: '/',           icon: <DashboardRoundedIcon /> },
  { label: 'Strategies',        path: '/strategies', icon: <ShowChartRoundedIcon /> },
  { label: 'Wallets',           path: '/wallets',    icon: <AccountBalanceWalletRoundedIcon /> },
  { label: 'Live Deployment',   path: '/deployment', icon: <RocketLaunchRoundedIcon /> },
  { label: 'Backtests',         path: '/backtests',  icon: <HistoryRoundedIcon /> },
  { label: 'Machine Learning',  path: '/ml',         icon: <PsychologyRoundedIcon /> },
  { label: 'NLP & Sentiment',   path: '/sentiment',  icon: <InsightsRoundedIcon /> },
];

const Sidebar = ({ collapsed, onToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const width = collapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED;

  const isActive = (path) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  return (
    <Drawer
      variant="permanent"
      sx={{
        width,
        flexShrink: 0,
        transition: 'width 0.3s cubic-bezier(.4,0,.2,1)',
        '& .MuiDrawer-paper': {
          width,
          overflow: 'hidden',
          transition: 'width 0.3s cubic-bezier(.4,0,.2,1)',
          boxSizing: 'border-box',
          background: (t) => t.palette.custom?.sidebarBg || '#0C0D1A',
          borderRight: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      {/* ── Logo area ── */}
      <Box
        sx={{
          px: collapsed ? 1.5 : 2.5,
          py: 2.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          justifyContent: collapsed ? 'center' : 'flex-start',
          minHeight: 64,
          transition: 'all 0.3s ease',
        }}
      >
        {/* Animated logo mark */}
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2.5,
            background: `linear-gradient(135deg, ${COLORS.purple} 0%, ${COLORS.cyan} 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 4px 20px rgba(124,58,237,0.35)`,
            flexShrink: 0,
            transition: 'transform 0.3s ease',
            animation: 'logoFloat 3s ease-in-out infinite',
            '@keyframes logoFloat': {
              '0%, 100%': { transform: 'translateY(0px)' },
              '50%':       { transform: 'translateY(-3px)' },
            },
          }}
        >
          <TrendingUpRoundedIcon sx={{ color: '#fff', fontSize: 22 }} />
        </Box>

        {!collapsed && (
          <Box sx={{ opacity: collapsed ? 0 : 1, transition: 'opacity 0.2s ease 0.1s' }}>
            <Typography
              fontWeight={800}
              fontSize="1.05rem"
              lineHeight={1.1}
              sx={{
                background: `linear-gradient(90deg, ${COLORS.purple}, ${COLORS.cyan})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              CryptoSight
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              fontWeight={500}
              fontSize="0.65rem"
            >
              Quant Dashboard
            </Typography>
          </Box>
        )}
      </Box>

      <Divider sx={{ mx: collapsed ? 1 : 2, opacity: 0.5 }} />

      {/* ── Navigation ── */}
      <List sx={{ px: 1, py: 1.5, flexGrow: 1 }}>
        {NAV_ITEMS.map(({ label, path, icon }) => {
          const active = isActive(path);

          const button = (
            <ListItemButton
              onClick={() => navigate(path)}
              sx={{
                borderRadius: 3,
                py: 1.2,
                px: collapsed ? 1.5 : 2,
                mb: 0.4,
                justifyContent: collapsed ? 'center' : 'flex-start',
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.2s ease',
                ...(active && {
                  background: (t) =>
                    t.palette.mode === 'dark'
                      ? `linear-gradient(90deg, rgba(124,58,237,0.18) 0%, rgba(124,58,237,0.04) 100%)`
                      : `linear-gradient(90deg, rgba(109,40,217,0.12) 0%, rgba(109,40,217,0.02) 100%)`,
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    left: 0,
                    top: '20%',
                    bottom: '20%',
                    width: 3,
                    borderRadius: 4,
                    background: `linear-gradient(180deg, ${COLORS.purple}, ${COLORS.cyan})`,
                    boxShadow: `0 0 8px ${COLORS.purple}`,
                  },
                }),
                '&:hover': {
                  background: (t) =>
                    t.palette.mode === 'dark'
                      ? 'rgba(124,58,237,0.1)'
                      : 'rgba(109,40,217,0.06)',
                  transform: collapsed ? 'scale(1.05)' : 'translateX(4px)',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: collapsed ? 0 : 40,
                  mr: collapsed ? 0 : 1.5,
                  color: active ? COLORS.purple : 'text.secondary',
                  transition: 'color 0.2s',
                  '& .MuiSvgIcon-root': { fontSize: 22 },
                }}
              >
                {icon}
              </ListItemIcon>

              {!collapsed && (
                <ListItemText
                  primary={label}
                  primaryTypographyProps={{
                    fontSize: '0.84rem',
                    fontWeight: active ? 700 : 500,
                    color: active ? 'primary.main' : 'text.primary',
                    whiteSpace: 'nowrap',
                  }}
                />
              )}

              {/* Active glow dot */}
              {active && !collapsed && (
                <Box
                  sx={{
                    width: 7,
                    height: 7,
                    borderRadius: '50%',
                    background: COLORS.purple,
                    boxShadow: `0 0 8px ${COLORS.purple}, 0 0 16px ${COLORS.purple}`,
                    animation: 'glowPulse 2s ease-in-out infinite',
                    '@keyframes glowPulse': {
                      '0%, 100%': { boxShadow: `0 0 6px ${COLORS.purple}` },
                      '50%':       { boxShadow: `0 0 14px ${COLORS.purple}, 0 0 24px ${COLORS.violet}` },
                    },
                  }}
                />
              )}
            </ListItemButton>
          );

          return (
            <ListItem key={path} disablePadding>
              {collapsed ? (
                <Tooltip title={label} placement="right" arrow>
                  {button}
                </Tooltip>
              ) : (
                button
              )}
            </ListItem>
          );
        })}
      </List>

      <Divider sx={{ mx: collapsed ? 1 : 2, opacity: 0.5 }} />

      {/* ── Toggle button ── */}
      <Box
        sx={{
          p: 1.5,
          display: 'flex',
          justifyContent: collapsed ? 'center' : 'flex-end',
        }}
      >
        <Tooltip title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} placement="right">
          <IconButton
            onClick={onToggle}
            size="small"
            sx={{
              background: (t) =>
                t.palette.mode === 'dark'
                  ? 'rgba(124,58,237,0.12)'
                  : 'rgba(109,40,217,0.08)',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(124,58,237,0.22)',
                transform: 'scale(1.1)',
              },
            }}
          >
            {collapsed
              ? <ChevronRightRoundedIcon fontSize="small" sx={{ color: COLORS.purple }} />
              : <ChevronLeftRoundedIcon  fontSize="small" sx={{ color: COLORS.purple }} />
            }
          </IconButton>
        </Tooltip>
      </Box>

      {/* ── Footer ── */}
      {!collapsed && (
        <Box px={2.5} py={1.5}>
          <Typography variant="caption" color="text.secondary" fontSize="0.65rem">
            © 2026 CryptoSight
          </Typography>
        </Box>
      )}
    </Drawer>
  );
};

export default Sidebar;
