import React, { useEffect, useState } from 'react';
import {
  Box, Typography, CircularProgress, Paper,
} from '@mui/material';

// Icons for KPI cards
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import FlashOnRoundedIcon from '@mui/icons-material/FlashOnRounded';
import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';
import ScienceRoundedIcon from '@mui/icons-material/ScienceRounded';
import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import AssignmentRoundedIcon from '@mui/icons-material/AssignmentRounded';
import AttachMoneyRoundedIcon from '@mui/icons-material/AttachMoneyRounded';
import AccountBalanceRoundedIcon from '@mui/icons-material/AccountBalanceRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import AutoGraphRoundedIcon from '@mui/icons-material/AutoGraphRounded';

import StatCard from '../components/UI/StatCard';
import StrategiesTable from '../components/Tables/StrategiesTable';
import { getKPIs, getStrategies, getSparkline } from '../api/DashboardApi';
import { COLORS, GRADIENTS } from '../theme/theme';

// ─── KPI config ───────────────────────────────────────────────────────────────
const buildKPICards = (kpi, spark) => [
  {
    title: 'Total Strategies', value: kpi.totalStrategies,
    icon: <BarChartRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.purple, trendColor: COLORS.purple, trend: spark,
  },
  {
    title: 'Active Strategies', value: kpi.activeStrategies,
    icon: <FlashOnRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.cyan, trendColor: COLORS.cyan, trend: spark,
  },
  {
    title: 'Running Executions', value: kpi.runningExecutions,
    icon: <RocketLaunchRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.green, trendColor: COLORS.green, trend: spark,
  },
  {
    title: 'Running Simulations', value: kpi.runningSimulations,
    icon: <ScienceRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.amber, trendColor: COLORS.amber, trend: spark,
  },
  {
    title: 'Connected Accounts', value: kpi.connectedAccounts,
    icon: <AccountBalanceWalletRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.pink, trendColor: COLORS.pink, trend: spark,
  },
  {
    title: 'Trained ML Models', value: kpi.trainedModels,
    icon: <PsychologyRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.indigo, trendColor: COLORS.indigo, trend: spark,
  },
  {
    title: 'Total Backtests', value: kpi.totalBacktests,
    icon: <AssignmentRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.ocean, trendColor: COLORS.blue, trend: spark,
  },
  {
    title: "Today's PnL", value: kpi.todayPnL,
    icon: <AttachMoneyRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.green, trendColor: COLORS.green, trend: spark,
  },
  {
    title: 'Portfolio Value', value: kpi.portfolioValue,
    icon: <AccountBalanceRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.purpleCyan, trendColor: COLORS.purple, trend: spark,
  },
  {
    title: 'Total Return', value: kpi.totalReturn,
    icon: <TrendingUpRoundedIcon fontSize="inherit" />,
    gradient: GRADIENTS.sunset, trendColor: COLORS.pink, trend: spark,
  },
];

// ─── Animated hero banner component ──────────────────────────────────────────
const HeroBanner = () => (
  <Paper
    elevation={0}
    sx={{
      px: { xs: 1.5, md: 5 },
      py: { xs: 6, md: 7 },     // tighter top/bottom → ~30% shorter
      mb: 7,
      borderRadius: '14px',
      width: '100%',               // full content width
      maxWidth: '700px',
      position: 'relative',
      overflow: 'hidden',
      cursor: 'default',

      // ── Background ──────────────────────────────────────
      background: (t) =>
        t.palette.mode === 'dark'
          ? 'linear-gradient(135deg, rgba(124,58,237,0.14) 0%, rgba(34,211,238,0.07) 50%, rgba(99,102,241,0.11) 100%)'
          : 'linear-gradient(135deg, rgba(109,40,217,0.07) 0%, rgba(34,211,238,0.05) 50%, rgba(99,102,241,0.05) 100%)',

      // ── Border ──────────────────────────────────────────
      border: (t) =>
        t.palette.mode === 'dark'
          ? '1px solid rgba(124,58,237,0.15)'
          : '1px solid rgba(109,40,217,0.1)',

      // ── Base shadow ─────────────────────────────────────
      boxShadow: (t) =>
        t.palette.mode === 'dark'
          ? '0 4px 24px rgba(0,0,0,0.3)'
          : '0 4px 20px rgba(109,40,217,0.06)',

      // ── All transitions 300ms ease-out ──────────────────
      transition: 'all 300ms ease-out',

      // ── Hover: lift + scale + glow + border brightens ───
      '&:hover': {
        transform: 'translateY(-4px) scale(1.01)',
        border: (t) =>
          t.palette.mode === 'dark'
            ? '1px solid rgba(124,58,237,0.5)'
            : '1px solid rgba(109,40,217,0.4)',
        boxShadow: (t) =>
          t.palette.mode === 'dark'
            ? '0 16px 48px rgba(124,58,237,0.25), 0 4px 16px rgba(34,211,238,0.1), 0 0 0 1px rgba(124,58,237,0.3)'
            : '0 16px 40px rgba(109,40,217,0.16), 0 4px 16px rgba(109,40,217,0.08)',
      },
    }}
  >
    {/* Floating orb 1 */}
    <Box
      sx={{
        position: 'absolute', top: -50, right: -10,
        width: 150, height: 150, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)',
        animation: 'orbFloat 6s ease-in-out infinite',
        '@keyframes orbFloat': {
          '0%,100%': { transform: 'translate(0,0) scale(1)' },
          '33%': { transform: 'translate(-12px,8px) scale(1.05)' },
          '66%': { transform: 'translate(8px,-6px) scale(0.97)' },
        },
      }}
    />
    {/* Floating orb 2 */}
    <Box
      sx={{
        position: 'absolute', bottom: -30, right: 90,
        width: 100, height: 100, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(34,211,238,0.1) 0%, transparent 70%)',
        animation: 'orbFloat2 8s ease-in-out infinite',
        '@keyframes orbFloat2': {
          '0%,100%': { transform: 'translate(0,0)' },
          '50%': { transform: 'translate(10px,-12px)' },
        },
      }}
    />

    {/* Content row */}
    <Box
      display="flex"
      alignItems="center"
      justifyContent="space-between"
      position="relative"
      zIndex={1}
    >
      {/* Left: text */}
      <Box>
        <Typography
          variant="h6"
          fontWeight={800}
          sx={{
            lineHeight: 1.2,
            mb: 0.6,
            background: (t) =>
              t.palette.mode === 'dark'
                ? `linear-gradient(90deg, #EEF2FF 0%, ${COLORS.violet} 100%)`
                : `linear-gradient(90deg, #1E1B4B 0%, ${COLORS.purple} 100%)`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Welcome to CryptoSight
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ fontSize: '0.8rem', lineHeight: 1.55, maxWidth: 420 }}
        >
          Monitor quantitative strategies, live executions, ML models &amp; your
          portfolio — all in one intelligent dashboard.
        </Typography>
      </Box>

      {/* Right: animated bars illustration */}
      <Box
        sx={{
          display: { xs: 'none', md: 'flex' },
          alignItems: 'flex-end',
          gap: 0.7,
          mr: 1.5,
        }}
      >
        {[28, 44, 24, 52, 36, 42, 28].map((h, i) => (
          <Box
            key={i}
            sx={{
              width: 9, height: h, borderRadius: 1.5,
              background: `linear-gradient(180deg, ${COLORS.purple} 0%, ${COLORS.cyan} 100%)`,
              opacity: 0.55 + i * 0.05,
              animation: `barBounce 1.5s ease-in-out ${i * 0.12}s infinite alternate`,
              '@keyframes barBounce': {
                '0%': { transform: 'scaleY(0.55)', opacity: 0.35 },
                '100%': { transform: 'scaleY(1)', opacity: 0.9 },
              },
              transformOrigin: 'bottom',
            }}
          />
        ))}

        <AutoGraphRoundedIcon
          sx={{
            fontSize: 36, ml: 1.2,
            color: COLORS.purple, opacity: 0.22,
            animation: 'iconPulse 3s ease-in-out infinite',
            '@keyframes iconPulse': {
              '0%,100%': { transform: 'scale(1)', opacity: 0.18 },
              '50%': { transform: 'scale(1.1)', opacity: 0.3 },
            },
          }}
        />
      </Box>
    </Box>
  </Paper>
);

// ─── Dashboard Page ───────────────────────────────────────────────────────────
const Dashboard = () => {
  const [kpi, setKpi] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [sparkline, setSparkline] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [kpiRes, stratRes, sparkRes] = await Promise.all([
          getKPIs(),
          getStrategies(),
          getSparkline(),
        ]);
        setKpi(kpiRes);
        setStrategies(stratRes);
        setSparkline(sparkRes);
      } catch {
        // TODO(security): generic error logging only
        console.error('Dashboard data load failed');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" height="60vh" gap={2}>
        <CircularProgress
          size={48}
          thickness={3}
          sx={{
            color: COLORS.purple,
            '& .MuiCircularProgress-circle': {
              strokeLinecap: 'round',
            },
          }}
        />
        <Typography variant="body2" color="text.secondary" fontWeight={500}>
          Loading dashboard…
        </Typography>
      </Box>
    );
  }

  const kpiCards = buildKPICards(kpi, sparkline);

  return (
    <Box>
      {/* ── Hero Banner ── */}
      <HeroBanner />

      {/* ── KPI Grid (5 per row on large, 3 on medium, 2 on small) ── */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(3, 1fr)',
            lg: 'repeat(5, 1fr)',
          },
          gap: 2.5,
          mb: 4,
        }}
      >
        {kpiCards.map((card) => (
          <StatCard
            key={card.title}
            title={card.title}
            value={card.value}
            icon={card.icon}
            gradient={card.gradient}
            trend={card.trend}
            trendColor={card.trendColor}
          />
        ))}
      </Box>

      {/* ── Strategies Table ── */}
      <StrategiesTable data={strategies} />
    </Box>
  );
};

export default Dashboard;
