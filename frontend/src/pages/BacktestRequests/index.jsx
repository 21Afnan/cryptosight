import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import TableSortLabel from '@mui/material/TableSortLabel';
import Button from '@mui/material/Button';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import FormControl from '@mui/material/FormControl';
import Divider from '@mui/material/Divider';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';
import Chip from '@mui/material/Chip';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import SearchBar from '../../components/ui/SearchBar';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getBacktests } from '../../api/backtestsApi';
import { COLORS } from '../../theme/theme';

import HistoryRoundedIcon from '@mui/icons-material/HistoryRounded';

import SpeedRoundedIcon from '@mui/icons-material/SpeedRounded';
import EmojiEventsRoundedIcon from '@mui/icons-material/EmojiEventsRounded';

const STATUS_TABS = ['all', 'pending', 'running', 'completed', 'failed'];

const PRESET_STRATEGIES = [
  {
    name: 'BTC Trend Rider 4H',
    tag: 'Trend Following',
    color: '#0ECB81',
    config: {
      strategy_name: 'BTC Trend Rider 4H',
      symbol: 'BTC/USDT',
      exchange: 'bybit',
      timeframe: '4h',
      start_date: '2026-01-01',
      end_date: '2026-07-27',
      initial_balance: 10000,
      position_size: { type: 'fixed_percentage', value: 10.0 },
      commission: 0.0005,
      slippage: 0.0002,
      allow_long: true,
      allow_short: true,
      max_open_positions: 1,
      take_profit: { type: 'percentage', value: 2.0 },
      stop_loss: { type: 'percentage', value: 1.0 },
      entry_price: 'next_open',
      exit_price: 'next_open',
      indicators: {
        RSI: { enabled: true, period: 14 },
        EMA: { enabled: true, fast_period: 20, slow_period: 50 },
        MACD: { enabled: false },
        BB: { enabled: false },
      },
      patterns: {
        ENGULFING: { enabled: true },
        DOJI: { enabled: false },
        HAMMER: { enabled: false },
      },
    },
  },
  {
    name: 'ETH Mean Reversion 1H',
    tag: 'Mean Reversion',
    color: '#F6465D',
    config: {
      strategy_name: 'ETH Mean Reversion 1H',
      symbol: 'ETH/USDT',
      exchange: 'bybit',
      timeframe: '1h',
      start_date: '2026-01-01',
      end_date: '2026-07-27',
      initial_balance: 15000,
      position_size: { type: 'fixed_percentage', value: 15.0 },
      commission: 0.0005,
      slippage: 0.0003,
      allow_long: true,
      allow_short: false,
      max_open_positions: 1,
      take_profit: { type: 'percentage', value: 3.0 },
      stop_loss: { type: 'percentage', value: 1.5 },
      entry_price: 'next_open',
      exit_price: 'next_open',
      indicators: {
        RSI: { enabled: true, period: 14 },
        EMA: { enabled: false },
        MACD: { enabled: false },
        BB: { enabled: true, period: 20 },
      },
      patterns: {
        ENGULFING: { enabled: false },
        DOJI: { enabled: true },
        HAMMER: { enabled: false },
      },
    },
  },
  {
    name: 'SOL Momentum Breakout 1D',
    tag: 'Momentum',
    color: '#F0B90B',
    config: {
      strategy_name: 'SOL Momentum Breakout 1D',
      symbol: 'SOL/USDT',
      exchange: 'bybit',
      timeframe: '1d',
      start_date: '2026-01-01',
      end_date: '2026-07-27',
      initial_balance: 20000,
      position_size: { type: 'fixed_percentage', value: 20.0 },
      commission: 0.0005,
      slippage: 0.0004,
      allow_long: true,
      allow_short: true,
      max_open_positions: 2,
      take_profit: { type: 'percentage', value: 5.0 },
      stop_loss: { type: 'percentage', value: 2.0 },
      entry_price: 'next_open',
      exit_price: 'next_open',
      indicators: {
        RSI: { enabled: true, period: 14 },
        EMA: { enabled: true, fast_period: 10, slow_period: 30 },
        MACD: { enabled: true },
        BB: { enabled: false },
      },
      patterns: {
        ENGULFING: { enabled: true },
        DOJI: { enabled: false },
        HAMMER: { enabled: true },
      },
    },
  },
  {
    name: 'DOGE Scalp 15M',
    tag: 'Scalping',
    color: '#858CA2',
    config: {
      strategy_name: 'DOGE Scalp 15M',
      symbol: 'DOGE/USDT',
      exchange: 'bybit',
      timeframe: '15m',
      start_date: '2026-06-01',
      end_date: '2026-07-27',
      initial_balance: 5000,
      position_size: { type: 'fixed_percentage', value: 25.0 },
      commission: 0.0005,
      slippage: 0.0003,
      allow_long: true,
      allow_short: true,
      max_open_positions: 1,
      take_profit: { type: 'percentage', value: 1.5 },
      stop_loss: { type: 'percentage', value: 0.8 },
      entry_price: 'next_open',
      exit_price: 'next_open',
      indicators: {
        RSI: { enabled: true, period: 14 },
        EMA: { enabled: true, fast_period: 9, slow_period: 21 },
        MACD: { enabled: false },
        BB: { enabled: false },
      },
      patterns: {
        ENGULFING: { enabled: true },
        DOJI: { enabled: false },
        HAMMER: { enabled: false },
      },
    },
  },
];



function SummaryKpiCard({ icon, label, value, subtext, color }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  return (
    <Card
      sx={{
        background: isDark ? COLORS.darkSurface : '#ffffff',
        border: isDark
          ? `1px solid ${color ? color + '40' : 'rgba(255,255,255,0.08)'}`
          : `1px solid ${color ? color + '30' : 'rgba(34, 197, 94, 0.22)'}`,
        borderRadius: 2.5,
        boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : '0 6px 22px rgba(14, 203, 129, 0.20)',
        height: '100%',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-3px)',
          boxShadow: isDark ? '0 8px 25px rgba(0,0,0,0.6)' : '0 12px 30px rgba(14, 203, 129, 0.35)',
        },
      }}
    >
      <CardContent sx={{ p: '18px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: color ? `${color}18` : 'rgba(140, 150, 170, 0.12)',
              color: color || 'text.primary',
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
              {label}
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', lineHeight: 1.2, color: color || 'text.primary' }}>
              {value}
            </Typography>
            {subtext && (
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: 11 }}>
                {subtext}
              </Typography>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function BacktestRequests() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const [tabIdx, setTabIdx] = useState(0);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [snack, setSnack] = useState(null);
  const [sortBy, setSortBy] = useState('net_pnl');
  const [sortDir, setSortDir] = useState('desc');

  const activeStatus = STATUS_TABS[tabIdx];
  const filterObj = activeStatus === 'all' ? {} : { status: activeStatus };

  const { data, loading } = useMockFetch(
    () => getBacktests({ search, filter: filterObj }),
    [search, tabIdx],
  );
  const backtests = data?.data ?? [];

  const completedList = backtests.filter((b) => b.status === 'completed');
  const avgWinRate = completedList.length
    ? (completedList.reduce((acc, b) => acc + (b.win_rate || 0), 0) / completedList.length * 100).toFixed(1)
    : '—';

  const topStrategy = completedList.length
    ? completedList.reduce((prev, curr) => ((curr.net_pnl || 0) > (prev.net_pnl || 0) ? curr : prev), completedList[0])
    : null;

  const handleSort = (col) => {
    if (sortBy === col) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(col);
      setSortDir('desc');
    }
    setPage(0);
  };

  const sortedBacktests = [...backtests].sort((a, b) => {
    const aVal = a[sortBy] ?? -Infinity;
    const bVal = b[sortBy] ?? -Infinity;
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
  });

  return (
    <PageContainer title="Backtest Requests">
      <Box sx={{ pt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>

        {/* 3 Equal Metric Summary Cards Top Banner */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
            gap: 2,
            width: '100%',
          }}
        >
          <SummaryKpiCard
            icon={<HistoryRoundedIcon />}
            label="Total Backtests"
            value={data?.total ?? backtests.length}
            subtext={`${completedList.length} completed runs`}
            color="#0ECB81"
          />
          <SummaryKpiCard
            icon={<SpeedRoundedIcon />}
            label="Avg Win Rate"
            value={`${avgWinRate}%`}
            subtext="Across completed backtests"
            color="#0ECB81"
          />
          <SummaryKpiCard
            icon={<EmojiEventsRoundedIcon />}
            label="Top Strategy"
            value={topStrategy ? topStrategy.strategy_name : 'BTC_EMA_Cross_4H'}
            subtext={topStrategy ? `+$${topStrategy.net_pnl?.toFixed(0)} Net PnL` : '+$4,820 Net PnL'}
            color="#F59E0B"
          />
        </Box>

        {/* Quick Strategy Presets Section (4 Standalone Equal 25% Grid Cards, Less Oval, No White Card Container) */}
        <Box sx={{ width: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, letterSpacing: 0.5 }}>
              QUICK STRATEGY PRESETS
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Click any card to auto-fill configuration
            </Typography>
          </Box>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
              gap: 2,
              width: '100%',
            }}
          >
            {PRESET_STRATEGIES.map((preset) => (
              <Card
                key={preset.name}
                onClick={() => {
                  setSnack({ severity: 'info', message: `Preset: ${preset.name}` });
                }}
                sx={{
                  p: '14px 18px',
                  height: '84px',
                  boxSizing: 'border-box',
                  borderRadius: '14px',
                  cursor: 'pointer',
                  background: isDark ? COLORS.darkSurface : '#ffffff',
                  border: `1px solid ${isDark ? 'rgba(34, 197, 94, 0.25)' : 'rgba(34, 197, 94, 0.22)'}`,
                  boxShadow: isDark ? '0 4px 18px rgba(34, 197, 94, 0.15)' : '0 6px 20px rgba(14, 203, 129, 0.20)',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    borderColor: COLORS.pnlGreen,
                    transform: 'translateY(-3px)',
                    boxShadow: '0 10px 25px rgba(14, 203, 129, 0.32)',
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 800, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {preset.name}
                  </Typography>
                  <Chip label={preset.tag} size="small" sx={{ height: 20, fontSize: 10, background: `${preset.color}20`, color: preset.color, fontWeight: 700 }} />
                </Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {preset.config.symbol} · {preset.config.exchange} · {preset.config.timeframe} · ${preset.config.initial_balance.toLocaleString()}
                </Typography>
              </Card>
            ))}
          </Box>
        </Box>

        {/* Tabbed Catalog List Card */}
        <Card
          sx={{
            background: isDark ? COLORS.darkSurface : '#ffffff',
            boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : '0 6px 22px rgba(14, 203, 129, 0.20)',
            border: `1px solid ${isDark ? theme.palette.divider : 'rgba(34, 197, 94, 0.22)'}`,
            borderRadius: 2.5,
          }}
        >
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
              <Tabs value={tabIdx} onChange={(_, v) => setTabIdx(v)} sx={{ minHeight: '36px' }}>
                {STATUS_TABS.map((s) => <Tab key={s} label={s.charAt(0).toUpperCase() + s.slice(1)} sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />)}
              </Tabs>
              <SearchBar onSearch={setSearch} placeholder="Search strategy or symbol…" />
            </Box>

            {loading ? <LoadingSkeleton variant="table" /> : backtests.length === 0 ? (
              <EmptyState icon={HistoryRoundedIcon} title="No backtests found" description={`No ${activeStatus === 'all' ? '' : activeStatus} backtests match your search.`} />
            ) : (
              <>
                <TableContainer>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>Strategy</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>Symbol</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>Exchange</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>Timeframe</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>Status</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>Submitted</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>
                          <TableSortLabel
                            active={sortBy === 'net_pnl'}
                            direction={sortBy === 'net_pnl' ? sortDir : 'desc'}
                            onClick={() => handleSort('net_pnl')}
                            sx={{
                              '& .MuiTableSortLabel-icon': { opacity: sortBy === 'net_pnl' ? 1 : 0.3 },
                              color: sortBy === 'net_pnl' ? '#0ECB81 !important' : 'inherit',
                              '&.Mui-active': { color: '#0ECB81' },
                            }}
                          >
                            Net PnL
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>
                          <TableSortLabel
                            active={sortBy === 'win_rate'}
                            direction={sortBy === 'win_rate' ? sortDir : 'desc'}
                            onClick={() => handleSort('win_rate')}
                            sx={{
                              '& .MuiTableSortLabel-icon': { opacity: sortBy === 'win_rate' ? 1 : 0.3 },
                              color: sortBy === 'win_rate' ? '#0ECB81 !important' : 'inherit',
                              '&.Mui-active': { color: '#0ECB81' },
                            }}
                          >
                            Win Rate
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>
                          <TableSortLabel
                            active={sortBy === 'sharpe'}
                            direction={sortBy === 'sharpe' ? sortDir : 'desc'}
                            onClick={() => handleSort('sharpe')}
                            sx={{
                              '& .MuiTableSortLabel-icon': { opacity: sortBy === 'sharpe' ? 1 : 0.3 },
                              color: sortBy === 'sharpe' ? '#0ECB81 !important' : 'inherit',
                              '&.Mui-active': { color: '#0ECB81' },
                            }}
                          >
                            Sharpe
                          </TableSortLabel>
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sortedBacktests.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((bt) => {
                        const targetId = bt.id || bt.strategy_id || bt.backtest_id;
                        return (
                          <TableRow
                            key={targetId}
                            hover
                            onClick={() => bt.status === 'completed' && navigate(`/backtests/${targetId}`)}
                            sx={{ cursor: bt.status === 'completed' ? 'pointer' : 'default' }}
                          >
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 700 }}>
                                {bt.strategy_name}
                              </Typography>
                              {bt.status === 'failed' && bt.error_message && (
                                <Typography variant="caption" sx={{ color: COLORS.pnlRed, display: 'block', fontSize: 11 }}>
                                  {bt.error_message}
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Chip label={bt.symbol} size="small" sx={{ height: 22, fontSize: 11, fontWeight: 600, background: `${COLORS.accent}15`, color: COLORS.accent }} />
                            </TableCell>
                            <TableCell>{bt.exchange}</TableCell>
                            <TableCell>{bt.timeframe}</TableCell>
                            <TableCell>
                              <Box>
                                <StatusChip status={bt.status} />
                                {bt.status === 'running' && bt.progress != null && (
                                  <LinearProgress variant="determinate" value={bt.progress * 100} sx={{ mt: 0.5, height: 3, borderRadius: 2 }} />
                                )}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                {bt.submitted_at ? new Date(bt.submitted_at).toLocaleDateString() : '—'}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" sx={{ color: bt.net_pnl != null ? (bt.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed) : 'inherit', fontVariantNumeric: 'tabular-nums', fontWeight: 700 }}>
                                {bt.net_pnl != null ? `${bt.net_pnl >= 0 ? '+' : ''}$${bt.net_pnl?.toFixed(0)}` : '—'}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                                {bt.win_rate != null ? `${(bt.win_rate * 100).toFixed(1)}%` : '—'}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                                {bt.sharpe?.toFixed(2) ?? '—'}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
                <TablePagination
                  component="div"
                  count={sortedBacktests.length}
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
      </Box>

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity={snack?.severity} onClose={() => setSnack(null)} sx={{ width: '100%' }}>{snack?.message}</Alert>
      </Snackbar>
    </PageContainer>
  );
}
