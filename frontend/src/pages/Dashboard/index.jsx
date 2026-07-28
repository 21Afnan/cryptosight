import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatCard from '../../components/ui/StatCard';
import StatusChip from '../../components/ui/StatusChip';
import LoadingSkeleton, { TableSkeleton } from '../../components/ui/LoadingSkeleton';
import EmptyState from '../../components/ui/EmptyState';
import AllocationDonut from '../../components/charts/AllocationDonut';
import StrategyFilterBar, { filterStrategies } from '../../components/ui/StrategyFilterBar';
import { useSearch } from '../../context/SearchContext';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getDashboardSummary } from '../../api/dashboardApi';
import { COLORS, GRADIENTS, ICON_BUBBLE_COLORS } from '../../theme/theme';

// MUI icons
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';
import HistoryRoundedIcon from '@mui/icons-material/HistoryRounded';
import AttachMoneyRoundedIcon from '@mui/icons-material/AttachMoneyRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded';

function fmt(n, decimals = 2) {
  if (n == null) return '—';
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtPct(n) {
  if (n == null) return '—';
  const sign = n >= 0 ? '+' : '';
  return `${sign}${(n * 100).toFixed(2)}%`;
}

function fmtCurrency(n) {
  if (n == null) return '—';
  const sign = n < 0 ? '-' : (n > 0 ? '+' : '');
  return `${sign}$${Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// ─── Hero Banner ──────────────────────────────────────────────────────────────
function HeroBanner({ data }) {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  return (
    <Card
      sx={{
        mb: 3,
        background: isDark ? GRADIENTS.heroDark : GRADIENTS.hero,
        borderRadius: '24px',
        overflow: 'hidden',
        position: 'relative',
        minHeight: 180,
        display: 'flex',
        alignItems: 'stretch',
        // Override hover transform for the hero to be subtler
        '&:hover': { transform: 'translateY(-1px)' },
      }}
    >
      {/* Decorative gradient blobs — purely geometric/abstract */}
      <Box
        sx={{
          position: 'absolute',
          top: -60,
          right: -40,
          width: 280,
          height: 280,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.08)',
          pointerEvents: 'none',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: -80,
          right: 80,
          width: 220,
          height: 220,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.06)',
          pointerEvents: 'none',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: 20,
          right: 160,
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.05)',
          pointerEvents: 'none',
        }}
      />
      {/* Small accent dot accents */}
      <Box sx={{ position: 'absolute', top: 32, right: 280, width: 16, height: 16, borderRadius: '50%', background: 'rgba(255,255,255,0.18)', pointerEvents: 'none' }} />
      <Box sx={{ position: 'absolute', bottom: 40, right: 240, width: 10, height: 10, borderRadius: '50%', background: 'rgba(255,255,255,0.15)', pointerEvents: 'none' }} />

      <CardContent sx={{ p: '32px !important', zIndex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', maxWidth: 520 }}>
        <Typography
          sx={{
            fontSize: '0.6875rem',
            fontWeight: 700,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'rgba(255,255,255,0.65)',
            mb: 1,
          }}
        >
          Quantitative Trading Platform
        </Typography>
        <Typography
          variant="h1"
          sx={{
            color: '#FFFFFF',
            fontWeight: 800,
            fontSize: '1.875rem',
            lineHeight: 1.2,
            letterSpacing: '-0.025em',
            mb: 3,
          }}
        >
          Welcome to CryptoSight
        </Typography>
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
          <Button
            id="hero-view-strategies-btn"
            variant="contained"
            endIcon={<ArrowForwardRoundedIcon />}
            onClick={() => navigate('/strategies')}
            sx={{
              background: 'rgba(255,255,255,0.95)',
              color: COLORS.accent,
              fontWeight: 700,
              '&:hover': {
                background: '#FFFFFF',
                boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
              },
            }}
          >
            View Strategies
          </Button>
          <Button
            id="hero-backtest-btn"
            variant="contained"
            onClick={() => navigate('/backtests')}
            sx={{
              background: 'rgba(255,255,255,0.15)',
              color: '#FFFFFF',
              backdropFilter: 'blur(8px)',
              fontWeight: 600,
              border: '1px solid rgba(255,255,255,0.2)',
              '&:hover': {
                background: 'rgba(255,255,255,0.25)',
                boxShadow: 'none',
              },
            }}
          >
            Run Backtest
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { data, loading, error } = useMockFetch(getDashboardSummary);
  const navigate = useNavigate();
  const theme = useTheme();
  const { query: globalSearch } = useSearch();
  const [strategyFilters, setStrategyFilters] = React.useState({ search: '', exchange: 'all', status: 'all', timeframe: 'all', pnl: 'all', minReturn: '' });
  const [sortField, setSortField] = React.useState('latest_return');
  const [sortOrder, setSortOrder] = React.useState('desc');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const filteredStrategiesList = useMemo(() => {
    const combinedFilters = {
      ...strategyFilters,
      search: globalSearch || strategyFilters.search,
    };
    const list = filterStrategies(data?.strategies_summary ?? [], combinedFilters);

    if (sortField) {
      list.sort((a, b) => {
        let valA = a[sortField] ?? 0;
        let valB = b[sortField] ?? 0;
        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return list;
  }, [data?.strategies_summary, strategyFilters, globalSearch, sortField, sortOrder]);

  const kpiCards = useMemo(() => {
    if (!data) return [];
    const s = data;
    return [
      { title: 'Portfolio Value', value: `$${fmt(s.portfolio_value)}`, delta: fmtPct(s.portfolio_change_pct), deltaType: s.portfolio_change_pct >= 0 ? 'positive' : 'negative', icon: <AccountBalanceWalletRoundedIcon />, colorIndex: 0 },
      { title: "Today's PnL", value: fmtCurrency(s.todays_pnl), delta: fmtPct(s.todays_pnl_pct), deltaType: s.todays_pnl >= 0 ? 'positive' : 'negative', icon: <AttachMoneyRoundedIcon />, colorIndex: 1 },
      { title: 'Total Return', value: fmtPct(s.total_return), delta: `$${fmt(s.total_return_usd)}`, deltaType: s.total_return >= 0 ? 'positive' : 'negative', icon: <TrendingUpRoundedIcon />, colorIndex: 2 },
      { title: 'Active Strategies', value: s.active_strategies, delta: `of ${s.total_strategies} total`, deltaType: 'neutral', icon: <ShowChartRoundedIcon />, colorIndex: 3 },
      { title: 'Live Executions', value: s.running_executions, delta: null, deltaType: 'neutral', icon: <RocketLaunchRoundedIcon />, colorIndex: 4 },
      { title: 'Running Simulations', value: s.running_simulations, delta: null, deltaType: 'neutral', icon: <BarChartRoundedIcon />, colorIndex: 3 },
      { title: 'Connected Accounts', value: s.connected_accounts, delta: null, deltaType: 'neutral', icon: <AccountBalanceWalletRoundedIcon />, colorIndex: 0 },
      { title: 'Trained ML Models', value: s.trained_ml_models, delta: null, deltaType: 'neutral', icon: <PsychologyRoundedIcon />, colorIndex: 1 },
      { title: 'Total Backtests', value: s.total_backtests, delta: null, deltaType: 'neutral', icon: <HistoryRoundedIcon />, colorIndex: 2 },
      { title: 'Total Return (USD)', value: `$${fmt(s.total_return_usd)}`, delta: fmtPct(s.total_return), deltaType: s.total_return >= 0 ? 'positive' : 'negative', icon: <DashboardRoundedIcon />, colorIndex: 4 },
    ];
  }, [data]);

  return (
    <PageContainer title="Dashboard">
      <Box sx={{ pt: 2 }}>
        {error && <EmptyState icon={ErrorOutlineRoundedIcon} title="Failed to load dashboard" description={error} />}

        {/* Hero banner */}
        <HeroBanner data={data} />

        {/* KPI cards grid — 5 equal columns on large screens */}
        {loading ? (
          <LoadingSkeleton variant="stats" count={10} />
        ) : (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(3, 1fr)',
                lg: 'repeat(5, 1fr)',
              },
              gap: 2,
              mb: 3,
            }}
          >
            {kpiCards.map((card, idx) => (
              <StatCard key={card.title} {...card} colorIndex={idx} />
            ))}
          </Box>
        )}

        {/* Strategies Overview Table (Full width 12 columns for max horizontal space) */}
        <Card>
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                Strategies Overview (Top 5)
              </Typography>
              <Button
                id="view-all-strategies-btn"
                size="small"
                endIcon={<ArrowForwardRoundedIcon />}
                onClick={() => navigate('/strategies')}
              >
                View all
              </Button>
            </Box>

            <StrategyFilterBar onChange={setStrategyFilters} />

            {loading ? (
              <TableSkeleton rows={8} columns={7} />
            ) : !filteredStrategiesList.length ? (
              <EmptyState icon={ShowChartRoundedIcon} title="No strategies match" description="No strategies match your filter criteria." />
            ) : (
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Strategy</TableCell>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Exchange</TableCell>
                      <TableCell>TF</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'latest_return'}
                          direction={sortField === 'latest_return' ? sortOrder : 'desc'}
                          onClick={() => handleSort('latest_return')}
                        >
                          Return
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'sharpe'}
                          direction={sortField === 'sharpe' ? sortOrder : 'desc'}
                          onClick={() => handleSort('sharpe')}
                        >
                          Sharpe
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'win_rate'}
                          direction={sortField === 'win_rate' ? sortOrder : 'desc'}
                          onClick={() => handleSort('win_rate')}
                        >
                          Win Rate
                        </TableSortLabel>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredStrategiesList.slice(0, 5).map((row) => (
                      <TableRow
                        key={row.strategy_id}
                        hover
                        onClick={() => navigate(`/strategies/${row.strategy_id}`)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {row.strategy_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: COLORS.accent, fontWeight: 600 }}>
                            {row.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell>{row.exchange}</TableCell>
                        <TableCell>
                          <Box
                            component="span"
                            sx={{
                              fontSize: 11,
                              fontWeight: 600,
                              px: 1,
                              py: 0.25,
                              borderRadius: '999px',
                              background: theme.palette.mode === 'dark' ? COLORS.accentSurfaceDark : COLORS.accentSurface,
                              color: theme.palette.mode === 'dark' ? COLORS.accentLight : COLORS.accent,
                            }}
                          >
                            {row.timeframe}
                          </Box>
                        </TableCell>
                        <TableCell><StatusChip status={row.status} /></TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            sx={{
                              color: row.latest_return >= 0 ? COLORS.pnlGreen : COLORS.pnlRed,
                              fontWeight: 700,
                              fontVariantNumeric: 'tabular-nums',
                            }}
                          >
                            {fmtPct(row.latest_return)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            sx={{
                              color: typeof row.sharpe === 'number' ? (row.sharpe >= 0 ? COLORS.pnlGreen : COLORS.pnlRed) : 'inherit',
                              fontWeight: 700,
                              fontVariantNumeric: 'tabular-nums',
                            }}
                          >
                            {typeof row.sharpe === 'number' ? row.sharpe.toFixed(2) : (row.sharpe ?? '—')}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            sx={{
                              color: row.win_rate != null ? (row.win_rate >= 0.5 ? COLORS.pnlGreen : COLORS.pnlRed) : 'inherit',
                              fontWeight: 700,
                              fontVariantNumeric: 'tabular-nums',
                            }}
                          >
                            {row.win_rate != null ? `${(row.win_rate * 100).toFixed(1)}%` : '—'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Box>
    </PageContainer>
  );
}
