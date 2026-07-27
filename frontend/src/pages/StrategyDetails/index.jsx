import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import TablePagination from '@mui/material/TablePagination';
import Button from '@mui/material/Button';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import EquityCurveChart from '../../components/charts/EquityCurveChart';
import DrawdownChart from '../../components/charts/DrawdownChart';
import MonthlyReturnsChart from '../../components/charts/MonthlyReturnsChart';
import DistributionChart from '../../components/charts/DistributionChart';
import LedgerFilterBar, { filterLedgerRows } from '../../components/ui/LedgerFilterBar';
import StrategyFilterBar, { filterStrategies } from '../../components/ui/StrategyFilterBar';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getStrategies, getStrategyById, getStrategyTrades } from '../../api/strategiesApi';
import { COLORS } from '../../theme/theme';

import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import ShieldRoundedIcon from '@mui/icons-material/ShieldRounded';
import LocalAtmRoundedIcon from '@mui/icons-material/LocalAtmRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import SpeedRoundedIcon from '@mui/icons-material/SpeedRounded';
import TuneRoundedIcon from '@mui/icons-material/TuneRounded';
import SecurityRoundedIcon from '@mui/icons-material/SecurityRounded';
import ScheduleRoundedIcon from '@mui/icons-material/ScheduleRounded';

function formatTs(ts) {
  if (!ts) return '—';
  let s = String(ts).replace('T', ' ');
  if (s.includes('+00:00')) s = s.replace('+00:00', '');
  else if (s.includes('+00') && s.endsWith(':00')) s = s.split('+')[0];
  return s.trim();
}

function HeroKpiCard({ icon, label, value, subtext, color, glowColor }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const activeColor = color || '#0ECB81';
  const activeGlow = glowColor || activeColor;

  const cardBg = isDark ? COLORS.darkSurface : '#ffffff';

  // Border: NONE, pure dynamic glowing drop shadow (Green for profit/good, Red for loss/bad)
  const cardShadow = isDark
    ? `0 6px 22px ${activeGlow ? activeGlow + '30' : 'rgba(0,0,0,0.4)'}`
    : `0 8px 26px ${activeGlow ? activeGlow + '35' : 'rgba(14, 203, 129, 0.28)'}`;

  const hoverShadow = isDark
    ? `0 10px 32px ${activeGlow ? activeGlow + '45' : 'rgba(0,0,0,0.6)'}`
    : `0 14px 36px ${activeGlow ? activeGlow + '50' : 'rgba(14, 203, 129, 0.40)'}`;

  return (
    <Card
      sx={{
        background: cardBg,
        border: 'none',
        borderRadius: 2.5,
        boxShadow: cardShadow,
        width: '100%',
        height: '115px',
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-3px)',
          boxShadow: hoverShadow,
        },
      }}
    >
      <CardContent sx={{ p: '16px 20px !important', width: '100%', boxSizing: 'border-box' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.75, width: '100%' }}>
          <Box
            sx={{
              width: 46,
              height: 46,
              borderRadius: 2,
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: activeGlow ? `${activeGlow}18` : 'rgba(140, 150, 170, 0.12)',
              color: activeColor,
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {label}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: activeColor, lineHeight: 1.15, fontSize: '1.45rem', my: 0.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {value}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: 11, fontWeight: 500, display: 'block', height: 16, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {subtext || ' '}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, children, height }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  return (
    <Card
      sx={{
        background: isDark ? COLORS.darkSurface : '#ffffff',
        border: 'none',
        boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : '0 8px 26px rgba(14, 203, 129, 0.24)',
        borderRadius: 2.5,
      }}
    >
      <CardContent sx={{ p: '20px !important' }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>{title}</Typography>
        <Box sx={{ height }}>{children}</Box>
      </CardContent>
    </Card>
  );
}

// Strategy list view (when no ID in params)
function StrategyList() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const [filters, setFilters] = useState({ search: '', exchange: 'all', status: 'all', timeframe: 'all', pnl: 'all' });
  const [sortField, setSortField] = useState('net_pnl');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { data, loading, error } = useMockFetch(getStrategies);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const rawStrategies = data?.data ?? [];
  const filteredList = React.useMemo(() => {
    const list = filterStrategies(rawStrategies, filters);
    if (sortField) {
      list.sort((a, b) => {
        let valA = a[sortField] ?? a.target_timeframe ?? 0;
        let valB = b[sortField] ?? b.target_timeframe ?? 0;
        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();
        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return list;
  }, [rawStrategies, filters, sortField, sortOrder]);

  return (
    <PageContainer title="Strategies">
      <Box sx={{ pt: 4 }}>
        {error && <EmptyState icon={ErrorOutlineRoundedIcon} title="Failed to load strategies" description={error} />}
        {loading ? <LoadingSkeleton variant="table" /> : (
          <Card
            sx={{
              background: isDark ? COLORS.darkSurface : '#ffffff',
              border: 'none',
              boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : '0 8px 26px rgba(14, 203, 129, 0.24)',
              borderRadius: 2.5,
            }}
          >
            <CardContent sx={{ p: '20px !important' }}>
              <StrategyFilterBar onChange={setFilters} />
              {!filteredList.length ? (
                <EmptyState icon={ShowChartRoundedIcon} title="No strategies match" description="No strategies match your filter criteria." />
              ) : (
                <>
                  <TableContainer>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>
                            <TableSortLabel active={sortField === 'strategy_name'} direction={sortField === 'strategy_name' ? sortOrder : 'asc'} onClick={() => handleSort('strategy_name')}>
                              Strategy
                            </TableSortLabel>
                          </TableCell>
                          <TableCell>
                            <TableSortLabel active={sortField === 'symbol'} direction={sortField === 'symbol' ? sortOrder : 'asc'} onClick={() => handleSort('symbol')}>
                              Symbol
                            </TableSortLabel>
                          </TableCell>
                          <TableCell>
                            <TableSortLabel active={sortField === 'exchange'} direction={sortField === 'exchange' ? sortOrder : 'asc'} onClick={() => handleSort('exchange')}>
                              Exchange
                            </TableSortLabel>
                          </TableCell>
                          <TableCell>
                            <TableSortLabel active={sortField === 'target_timeframe'} direction={sortField === 'target_timeframe' ? sortOrder : 'asc'} onClick={() => handleSort('target_timeframe')}>
                              Timeframe
                            </TableSortLabel>
                          </TableCell>
                          <TableCell>
                            <TableSortLabel active={sortField === 'status'} direction={sortField === 'status' ? sortOrder : 'asc'} onClick={() => handleSort('status')}>
                              Status
                            </TableSortLabel>
                          </TableCell>
                          <TableCell align="right">
                            <TableSortLabel active={sortField === 'net_pnl'} direction={sortField === 'net_pnl' ? sortOrder : 'desc'} onClick={() => handleSort('net_pnl')}>
                              Net PnL
                            </TableSortLabel>
                          </TableCell>
                          <TableCell align="right">
                            <TableSortLabel active={sortField === 'win_rate'} direction={sortField === 'win_rate' ? sortOrder : 'desc'} onClick={() => handleSort('win_rate')}>
                              Win Rate
                            </TableSortLabel>
                          </TableCell>
                          <TableCell align="right">
                            <TableSortLabel active={sortField === 'sharpe'} direction={sortField === 'sharpe' ? sortOrder : 'desc'} onClick={() => handleSort('sharpe')}>
                              Sharpe
                            </TableSortLabel>
                          </TableCell>
                          <TableCell align="right">
                            <TableSortLabel active={sortField === 'total_trades'} direction={sortField === 'total_trades' ? sortOrder : 'desc'} onClick={() => handleSort('total_trades')}>
                              Total Trades
                            </TableSortLabel>
                          </TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {filteredList.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((s) => (
                          <TableRow key={s.strategy_id} hover onClick={() => navigate(`/strategies/${s.strategy_id}`)} sx={{ cursor: 'pointer' }}>
                            <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{s.strategy_name}</Typography></TableCell>
                            <TableCell><Typography variant="body2" sx={{ color: COLORS.accent, fontWeight: 500 }}>{s.symbol}</Typography></TableCell>
                            <TableCell>{s.exchange}</TableCell>
                            <TableCell><Chip label={s.target_timeframe} size="small" sx={{ height: 20, fontSize: 11 }} /></TableCell>
                            <TableCell><StatusChip status={s.status} /></TableCell>
                            <TableCell align="right"><Typography variant="body2" sx={{ color: s.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>${s.net_pnl?.toFixed(0) ?? '—'}</Typography></TableCell>
                            <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{s.win_rate != null ? `${(s.win_rate * 100).toFixed(1)}%` : '—'}</Typography></TableCell>
                            <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{typeof s.sharpe === 'number' ? s.sharpe.toFixed(2) : (s.sharpe ?? '—')}</Typography></TableCell>
                            <TableCell align="right"><Typography variant="body2" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{s.total_trades != null ? s.total_trades.toLocaleString() : '0'}</Typography></TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  <TablePagination
                    component="div"
                    count={filteredList.length}
                    page={page}
                    onPageChange={(_, p) => setPage(p)}
                    rowsPerPage={rowsPerPage}
                    onRowsPerPageChange={(e) => { setRowsPerPage(+e.target.value); setPage(0); }}
                    rowsPerPageOptions={[5, 10, 25]}
                  />
                </>
              )}
            </CardContent>
          </Card>
        )}
      </Box>
    </PageContainer>
  );
}

// Strategy Detail view (backend integrated)
function StrategyDetailView({ id }) {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const [ledgerFilters, setLedgerFilters] = useState({ startDate: '', endDate: '', side: 'all', symbol: '' });

  const { data: strategy, loading, error } = useMockFetch(() => getStrategyById(id), [id]);
  const { data: tradesRes, loading: tradesLoading } = useMockFetch(() => getStrategyTrades(id), [id]);

  const rawTrades = tradesRes?.data ?? [];
  const filteredTrades = filterLedgerRows(rawTrades, ledgerFilters);

  if (loading) return <PageContainer title="Strategy Details"><Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box></PageContainer>;
  if (error || !strategy) return (
    <PageContainer title="Strategy Details">
      <EmptyState icon={ErrorOutlineRoundedIcon} title="Strategy not found" description={error || 'The requested strategy does not exist.'} action={<Button onClick={() => navigate('/strategies')}>Back to Strategies</Button>} />
    </PageContainer>
  );

  const perf = strategy.performance || {};
  const cfg = strategy.configuration || {};
  const rm = strategy.risk_management || {};
  const sc = strategy.strategy_config || {};
  const bc = strategy.backtest_config || {};

  const netPnl = perf.net_pnl ?? strategy.net_pnl ?? 0;
  const winRate = perf.win_rate ?? strategy.win_rate;
  const sharpe = perf.sharpe ?? strategy.sharpe;
  const sortino = perf.sortino ?? strategy.sortino;
  const calmar = perf.calmar ?? strategy.calmar;
  const maxDd = perf.max_drawdown ?? strategy.max_drawdown;
  const cagr = perf.cagr ?? strategy.cagr;
  const totalTrades = perf.total_trades ?? strategy.total_trades ?? 0;

  // Dynamic Value-Based Colors (Green = Profit/Good, Red = Loss/Bad)
  const pnlColor = netPnl >= 0 ? '#0ECB81' : '#F6465D';
  const cagrColor = (cagr ?? 0) >= 0 ? '#0ECB81' : '#F6465D';
  const winRateColor = (winRate ?? 0) >= 0.5 ? '#0ECB81' : '#F6465D';
  const tradesColor = '#0ECB81';
  const sharpeColor = (sharpe ?? 0) >= 1.0 ? '#0ECB81' : '#F6465D';
  const sortinoColor = (sortino ?? 0) >= 1.0 ? '#0ECB81' : '#F6465D';
  const calmarColor = (calmar ?? 0) >= 1.0 ? '#0ECB81' : '#F6465D';
  const ddColor = '#F6465D';

  const cardLightShadow = '0 8px 26px rgba(14, 203, 129, 0.24)';

  // Calculate Long vs Short Signal Bias
  const longSigs = parseInt(cfg.long_signals ?? strategy.long_signals ?? 28);
  const shortSigs = parseInt(cfg.short_signals ?? strategy.short_signals ?? 13);
  const totalSigs = longSigs + shortSigs;
  const longPct = totalSigs > 0 ? Math.round((longSigs / totalSigs) * 100) : 68;

  // Real Last Signal timestamp directly from backend (No mock fallback)
  const rawLastSignal = cfg.last_signal || strategy.last_signal_time || strategy.last_signal;
  const formattedLastSignal = rawLastSignal
    ? (typeof rawLastSignal === 'string'
      ? rawLastSignal.replace('T', ' ').split('+')[0]
      : new Date(rawLastSignal).toLocaleString())
    : '—';

  return (
    <PageContainer title={strategy.strategy_name} breadcrumbs="Strategies">
      <Box sx={{ pt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>

        {/* Navigation & Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/strategies')} variant="outlined" size="small" sx={{ borderRadius: 2 }}>
              Back
            </Button>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h5" sx={{ fontWeight: 800 }}>{strategy.strategy_name}</Typography>
                <StatusChip status={strategy.status} size="small" />
                <Chip label={strategy.symbol} size="small" color="primary" sx={{ fontWeight: 700 }} />
                <Chip label={strategy.exchange} size="small" variant="outlined" sx={{ fontWeight: 600 }} />
                <Chip label={strategy.target_timeframe} size="small" variant="outlined" sx={{ fontWeight: 600 }} />
              </Box>
            </Box>
          </Box>
        </Box>

        {/* 8 Equal-Sized Dynamic Flashcards (CSS Grid repeat(4, 1fr), Border NONE, Pure Red/Green Glow Shadow) */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 2,
            width: '100%',
          }}
        >
          <HeroKpiCard
            icon={<LocalAtmRoundedIcon />}
            label="Net PnL"
            value={`${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)}`}
            subtext="Total Strategy Return"
            color={pnlColor}
            glowColor={pnlColor}
          />
          <HeroKpiCard
            icon={<TrendingUpRoundedIcon />}
            label="CAGR"
            value={cagr != null ? `${(cagr * 100).toFixed(1)}%` : '—'}
            subtext="Annualized Compound Growth"
            color={cagrColor}
            glowColor={cagrColor}
          />
          <HeroKpiCard
            icon={<SpeedRoundedIcon />}
            label="Win Rate"
            value={winRate != null ? `${(winRate * 100).toFixed(1)}%` : '—'}
            subtext={`Profit Factor: ${perf.profit_factor?.toFixed(2) ?? '—'}`}
            color={winRateColor}
            glowColor={winRateColor}
          />
          <HeroKpiCard
            icon={<BarChartRoundedIcon />}
            label="Total Trades"
            value={totalTrades}
            subtext="Executed Signals"
            color={tradesColor}
            glowColor={tradesColor}
          />
          <HeroKpiCard
            icon={<ShowChartRoundedIcon />}
            label="Sharpe Ratio"
            value={typeof sharpe === 'number' ? sharpe.toFixed(2) : '—'}
            subtext="Excess Risk-Adjusted Return"
            color={sharpeColor}
            glowColor={sharpeColor}
          />
          <HeroKpiCard
            icon={<ShowChartRoundedIcon />}
            label="Sortino Ratio"
            value={typeof sortino === 'number' ? sortino.toFixed(2) : '—'}
            subtext="Downside Risk Adjusted"
            color={sortinoColor}
            glowColor={sortinoColor}
          />
          <HeroKpiCard
            icon={<ShowChartRoundedIcon />}
            label="Calmar Ratio"
            value={typeof calmar === 'number' ? calmar.toFixed(2) : '—'}
            subtext="CAGR / Max Drawdown Ratio"
            color={calmarColor}
            glowColor={calmarColor}
          />
          <HeroKpiCard
            icon={<ShieldRoundedIcon />}
            label="Max Drawdown"
            value={typeof maxDd === 'number' ? `${(maxDd * 100).toFixed(1)}%` : '—'}
            subtext="Peak-to-Trough Decline"
            color={ddColor}
            glowColor={ddColor}
          />
        </Box>

        {/* Configuration & Risk Management Panels (Border NONE, Pure Glow Shadow) */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, width: '100%' }}>
          {/* Strategy Execution Specs Matrix */}
          <Card
            sx={{
              background: isDark ? COLORS.darkSurface : '#ffffff',
              border: 'none',
              boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : cardLightShadow,
              borderRadius: 2.5,
              height: '100%',
              width: '100%',
              boxSizing: 'border-box',
              overflow: 'hidden',
            }}
          >
            <CardContent sx={{ p: '20px !important', boxSizing: 'border-box', width: '100%', display: 'flex', flexDirection: 'column', height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TuneRoundedIcon sx={{ color: COLORS.pnlGreen }} />
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>
                    Execution Configuration
                  </Typography>
                </Box>
                <Chip label={`${longPct}% Long Bias`} size="small" sx={{ height: 22, fontSize: 11, fontWeight: 700, background: 'rgba(14, 203, 129, 0.15)', color: '#0ECB81' }} />
              </Box>

              {/* 7 Clean Parameter Boxes in 3/4 Column Responsive Grid */}
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', lg: 'repeat(4, 1fr)' },
                  gap: 1.25,
                  mb: 2,
                  width: '100%',
                  boxSizing: 'border-box',
                }}
              >
                {[
                  ['Exchange', cfg.exchange || strategy.exchange],
                  ['Symbol', cfg.symbol || strategy.symbol],
                  ['Target Timeframe', cfg.target_timeframe || strategy.target_timeframe],
                  ['Base Timeframe', cfg.base_timeframe || strategy.timeframe || '—'],
                  ['Long Signals', cfg.long_signals ?? strategy.long_signals ?? '—'],
                  ['Short Signals', cfg.short_signals ?? strategy.short_signals ?? '—'],
                  ['Total Rows', cfg.total_rows != null ? cfg.total_rows.toLocaleString() : (strategy.total_rows ? strategy.total_rows.toLocaleString() : '—')],
                ].map(([label, value]) => (
                  <Box
                    key={label}
                    sx={{
                      p: '10px 12px',
                      height: '60px',
                      width: '100%',
                      boxSizing: 'border-box',
                      borderRadius: '12px',
                      background: isDark ? 'rgba(38, 46, 37, 0.7)' : '#ffffff',
                      border: 'none',
                      boxShadow: isDark ? '0 2px 8px rgba(0, 0, 0, 0.3)' : '0 6px 18px rgba(14, 203, 129, 0.20)',
                      transition: 'all 0.2s ease',
                      overflow: 'hidden',
                      '&:hover': {
                        boxShadow: '0 10px 24px rgba(14, 203, 129, 0.32)',
                        transform: 'translateY(-2px)',
                      },
                    }}
                  >
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.4, fontSize: 10, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {label}
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', mt: 0.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {value ?? '—'}
                    </Typography>
                  </Box>
                ))}
              </Box>

              {/* Signal Balance Progress Bar */}
              <Box sx={{ mt: 'auto', pt: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="caption" sx={{ fontSize: 11, fontWeight: 600, color: '#0ECB81' }}>
                    Long: {longSigs} ({longPct}%)
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: 11, fontWeight: 600, color: '#F6465D' }}>
                    Short: {shortSigs} ({100 - longPct}%)
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={longPct}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: '#F6465D',
                    '& .MuiLinearProgress-bar': { backgroundColor: '#0ECB81', borderRadius: 3 },
                  }}
                />

                {/* Dedicated Full-Width Real Last Signal Timestamp Banner */}
                <Box
                  sx={{
                    mt: 1.75,
                    p: '10px 16px',
                    borderRadius: '12px',
                    background: isDark ? 'rgba(38, 46, 37, 0.7)' : '#ffffff',
                    border: 'none',
                    boxShadow: isDark ? '0 2px 8px rgba(0, 0, 0, 0.3)' : '0 6px 18px rgba(14, 203, 129, 0.20)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 1.5,
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ScheduleRoundedIcon sx={{ fontSize: 16, color: COLORS.pnlGreen }} />
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 10 }}>
                      LAST SIGNAL TIMESTAMP
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: COLORS.pnlGreen, fontSize: '0.85rem' }}>
                    {formattedLastSignal}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Risk Management Panel */}
          <Card
            sx={{
              background: isDark ? COLORS.darkSurface : '#ffffff',
              border: 'none',
              boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : cardLightShadow,
              borderRadius: 2.5,
              height: '100%',
              width: '100%',
              boxSizing: 'border-box',
              overflow: 'hidden',
            }}
          >
            <CardContent sx={{ p: '20px !important', boxSizing: 'border-box', width: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SecurityRoundedIcon sx={{ color: COLORS.pnlGreen }} />
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>
                    Risk Management
                  </Typography>
                </Box>
              </Box>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
                  gap: 1.5,
                  width: '100%',
                  boxSizing: 'border-box',
                }}
              >
                {[
                  ['Take Profit', rm.take_profit || (sc.take_profit != null ? `${(sc.take_profit * 100).toFixed(1)}%` : '1.2%'), '#0ECB81'],
                  ['Stop Loss', rm.stop_loss || (sc.stop_loss != null ? `${(sc.stop_loss * 100).toFixed(1)}%` : '0.6%'), '#F6465D'],
                  ['Position Size', rm.position_size || (sc.position_size != null ? `${(sc.position_size * 100).toFixed(0)}%` : '10.0%'), '#0ECB81'],
                  ['Commission', rm.commission || (bc.commission != null ? `${(bc.commission * 100).toFixed(3)}%` : '0.050%'), theme.palette.text.primary],
                  ['Slippage', rm.slippage || (bc.slippage != null ? `${(bc.slippage * 100).toFixed(3)}%` : '0.020%'), theme.palette.text.primary],
                ].map(([label, value, accentColor]) => (
                  <Box
                    key={label}
                    sx={{
                      p: '10px 12px',
                      height: '60px',
                      width: '100%',
                      boxSizing: 'border-box',
                      borderRadius: '12px',
                      background: isDark ? 'rgba(38, 46, 37, 0.7)' : '#ffffff',
                      border: 'none',
                      boxShadow: isDark ? '0 2px 8px rgba(0, 0, 0, 0.3)' : `0 6px 18px ${accentColor === '#F6465D' ? 'rgba(246, 70, 93, 0.25)' : 'rgba(14, 203, 129, 0.20)'}`,
                      transition: 'all 0.2s ease',
                      overflow: 'hidden',
                      '&:hover': {
                        boxShadow: `0 10px 24px ${accentColor === '#F6465D' ? 'rgba(246, 70, 93, 0.38)' : 'rgba(14, 203, 129, 0.32)'}`,
                        transform: 'translateY(-2px)',
                      },
                    }}
                  >
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.4, fontSize: 10, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {label}
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', mt: 0.25, color: accentColor, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* 4 Performance Charts: 2 per row (2 in row 1, 2 in row 2) */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
          <ChartCard title="Equity Curve" height={300}>
            <EquityCurveChart data={strategy.charts?.returns?.raw_values?.length ? strategy.charts.returns.raw_values : (strategy.equity_curve ?? [])} height={300} />
          </ChartCard>
          <ChartCard title="Drawdown" height={300}>
            <DrawdownChart data={strategy.charts?.drawdown?.raw_values?.length ? strategy.charts.drawdown.raw_values : (strategy.drawdown_curve ?? [])} height={300} />
          </ChartCard>
          <ChartCard title="Monthly Returns" height={270}>
            <MonthlyReturnsChart data={strategy.monthly_returns ?? []} height={270} />
          </ChartCard>
          <ChartCard title="Trade PnL Distribution" height={270}>
            <DistributionChart data={strategy.trade_distribution ?? []} height={270} />
          </ChartCard>
        </Box>

        {/* Recent Trades */}
        <Card
          sx={{
            background: isDark ? COLORS.darkSurface : '#ffffff',
            border: 'none',
            boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : cardLightShadow,
            borderRadius: 2.5,
            width: '100%',
          }}
        >
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Recent Trades</Typography>
            <LedgerFilterBar onChange={setLedgerFilters} />
            {tradesLoading ? <LoadingSkeleton variant="table" rows={10} columns={7} /> : !filteredTrades.length ? (
              <EmptyState icon={ShowChartRoundedIcon} title="No trades found" description="No trade ledgers recorded for this strategy yet." />
            ) : (
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>#</TableCell>
                      <TableCell>Entry Time</TableCell>
                      <TableCell>Exit Time</TableCell>
                      <TableCell>Side</TableCell>
                      <TableCell align="right">Entry Price</TableCell>
                      <TableCell align="right">Exit Price</TableCell>
                      <TableCell align="right">Net PnL</TableCell>
                      <TableCell align="right">Return %</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredTrades.map((trade, idx) => (
                      <TableRow key={trade.trade_id || idx} hover>
                        <TableCell><Typography variant="body2" sx={{ fontWeight: 600, color: theme.palette.text.secondary }}>{idx + 1}</Typography></TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontSize: 12 }}>{formatTs(trade.entry_time)}</Typography></TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontSize: 12 }}>{formatTs(trade.exit_time)}</Typography></TableCell>
                        <TableCell><StatusChip status={trade.side || trade.direction} /></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${trade.entry_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${trade.exit_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: (trade.net_pnl ?? trade.gross_pnl ?? 0) >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{(trade.net_pnl ?? trade.gross_pnl ?? 0) >= 0 ? '+' : ''}${(trade.net_pnl ?? trade.gross_pnl ?? 0).toFixed(2)}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: (trade.return_pct ?? 0) >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{(trade.return_pct ?? 0) >= 0 ? '+' : ''}{((trade.return_pct ?? 0) * 100).toFixed(2)}%</Typography></TableCell>
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

export default function StrategyDetails() {
  const { id } = useParams();
  if (!id) return <StrategyList />;
  return <StrategyDetailView id={id} />;
}
