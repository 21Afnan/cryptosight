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
import Button from '@mui/material/Button';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import FormControl from '@mui/material/FormControl';
import OutlinedInput from '@mui/material/OutlinedInput';
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
import { getBacktests, submitBacktest, getMarketDataOptions } from '../../api/backtestsApi';
import { COLORS } from '../../theme/theme';

import HistoryRoundedIcon from '@mui/icons-material/HistoryRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import SpeedRoundedIcon from '@mui/icons-material/SpeedRounded';
import EmojiEventsRoundedIcon from '@mui/icons-material/EmojiEventsRounded';

const STATUS_TABS = ['all', 'pending', 'running', 'completed', 'failed'];

const PRESET_STRATEGIES = [
  {
    name: 'BTC EMA Cross 4H',
    tag: 'Trend Following',
    color: '#0ECB81',
    config: {
      strategy_name: 'BTC_EMA_Cross_4H',
      symbol: 'BTC/USDT',
      exchange: 'binance',
      timeframe: '4h',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      initial_balance: 10000,
      commission: 0.0005,
      slippage: 0.0002,
      take_profit: 0.045,
      stop_loss: 0.02,
    },
  },
  {
    name: 'ETH RSI Reversion 1H',
    tag: 'Mean Reversion',
    color: '#0ECB81',
    config: {
      strategy_name: 'ETH_RSI_Rev_1H',
      symbol: 'ETH/USDT',
      exchange: 'bybit',
      timeframe: '1h',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      initial_balance: 15000,
      commission: 0.0006,
      slippage: 0.0003,
      take_profit: 0.035,
      stop_loss: 0.015,
    },
  },
  {
    name: 'SOL Breakout 1D',
    tag: 'Momentum',
    color: '#0ECB81',
    config: {
      strategy_name: 'SOL_Breakout_1D',
      symbol: 'SOL/USDT',
      exchange: 'okx',
      timeframe: '1d',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      initial_balance: 20000,
      commission: 0.0005,
      slippage: 0.0004,
      take_profit: 0.06,
      stop_loss: 0.025,
    },
  },
  {
    name: 'BNB MACD Scalp 15M',
    tag: 'Scalping',
    color: '#0ECB81',
    config: {
      strategy_name: 'BNB_MACD_Scalp_15M',
      symbol: 'BNB/USDT',
      exchange: 'binance',
      timeframe: '15m',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      initial_balance: 25000,
      commission: 0.0004,
      slippage: 0.0002,
      take_profit: 0.025,
      stop_loss: 0.01,
    },
  },
];

const DEFAULT_FORM = PRESET_STRATEGIES[0].config;

function FormRow({ label, children }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
        {label}
      </Typography>
      {children}
    </Box>
  );
}

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
  const [form, setForm] = useState(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [snack, setSnack] = useState(null);

  const activeStatus = STATUS_TABS[tabIdx];
  const filterObj = activeStatus === 'all' ? {} : { status: activeStatus };

  const { data, loading, refetch } = useMockFetch(
    () => getBacktests({ search, filter: filterObj }),
    [search, tabIdx],
  );
  const { data: mktData } = useMockFetch(getMarketDataOptions);
  const backtests = data?.data ?? [];

  const symbols = [...new Set([...(mktData?.data ?? []).map((m) => m.symbol), 'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT'])];
  const exchanges = [...new Set([...(mktData?.data ?? []).map((m) => m.exchange), 'binance', 'bybit', 'okx'])];
  const timeframes = [...new Set([...(mktData?.data ?? []).map((m) => m.timeframe), '1m', '5m', '15m', '1h', '4h', '1d'])];

  const completedList = backtests.filter((b) => b.status === 'completed');
  const avgWinRate = completedList.length
    ? (completedList.reduce((acc, b) => acc + (b.win_rate || 0), 0) / completedList.length * 100).toFixed(1)
    : '61.4';

  const topStrategy = completedList.length
    ? completedList.reduce((prev, curr) => ((curr.net_pnl || 0) > (prev.net_pnl || 0) ? curr : prev), completedList[0])
    : null;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await submitBacktest(form);
      setSnack({ severity: 'success', message: 'Backtest request queued successfully!' });
      refetch();
    } catch (e) {
      setSnack({ severity: 'error', message: 'Failed to submit backtest' });
    } finally {
      setSubmitting(false);
    }
  };

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
                  setForm(preset.config);
                  setSnack({ severity: 'info', message: `Loaded preset: ${preset.name}` });
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

        {/* Configuration Form Card */}
        <Card
          sx={{
            background: isDark ? COLORS.darkSurface : '#ffffff',
            boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : '0 6px 22px rgba(14, 203, 129, 0.20)',
            border: `1px solid ${isDark ? theme.palette.divider : 'rgba(34, 197, 94, 0.22)'}`,
            borderRadius: 2.5,
          }}
        >
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2.5 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Configure New Backtest
              </Typography>
              <Chip label="Parameter Tuner" size="small" variant="outlined" color="primary" />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Strategy Name">
                  <OutlinedInput size="small" value={form.strategy_name} onChange={(e) => setForm((f) => ({ ...f, strategy_name: e.target.value }))} placeholder="BTC_EMA_Cross_4H" />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Symbol">
                  <FormControl size="small" fullWidth>
                    <Select value={form.symbol} onChange={(e) => setForm((f) => ({ ...f, symbol: e.target.value }))} displayEmpty>
                      <MenuItem value=""><em>Select symbol</em></MenuItem>
                      {symbols.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                    </Select>
                  </FormControl>
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Exchange">
                  <FormControl size="small" fullWidth>
                    <Select value={form.exchange} onChange={(e) => setForm((f) => ({ ...f, exchange: e.target.value }))} displayEmpty>
                      <MenuItem value=""><em>Select exchange</em></MenuItem>
                      {exchanges.map((ex) => <MenuItem key={ex} value={ex}>{ex}</MenuItem>)}
                    </Select>
                  </FormControl>
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Timeframe">
                  <FormControl size="small" fullWidth>
                    <Select value={form.timeframe} onChange={(e) => setForm((f) => ({ ...f, timeframe: e.target.value }))} displayEmpty>
                      <MenuItem value=""><em>Select timeframe</em></MenuItem>
                      {timeframes.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                    </Select>
                  </FormControl>
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Start Date">
                  <OutlinedInput size="small" type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="End Date">
                  <OutlinedInput size="small" type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Initial Capital ($)">
                  <OutlinedInput size="small" type="number" value={form.initial_balance} onChange={(e) => setForm((f) => ({ ...f, initial_balance: Number(e.target.value) }))} />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Commission (%)">
                  <OutlinedInput size="small" type="number" value={(form.commission * 100).toFixed(3)} onChange={(e) => setForm((f) => ({ ...f, commission: Number(e.target.value) / 100 }))} inputProps={{ step: 0.001, min: 0 }} />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Slippage (%)">
                  <OutlinedInput size="small" type="number" value={(form.slippage * 100).toFixed(3)} onChange={(e) => setForm((f) => ({ ...f, slippage: Number(e.target.value) / 100 }))} inputProps={{ step: 0.001, min: 0 }} />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Take Profit (%)">
                  <OutlinedInput size="small" type="number" value={(form.take_profit * 100).toFixed(1)} onChange={(e) => setForm((f) => ({ ...f, take_profit: Number(e.target.value) / 100 }))} inputProps={{ step: 0.1, min: 0 }} />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormRow label="Stop Loss (%)">
                  <OutlinedInput size="small" type="number" value={(form.stop_loss * 100).toFixed(1)} onChange={(e) => setForm((f) => ({ ...f, stop_loss: Number(e.target.value) / 100 }))} inputProps={{ step: 0.1, min: 0 }} />
                </FormRow>
              </Grid>

              <Grid item xs={12} sm={6} md={3} sx={{ display: 'flex', alignItems: 'flex-end' }}>
                <Button id="submit-backtest-btn" variant="contained" fullWidth startIcon={<SendRoundedIcon />} onClick={handleSubmit} disabled={submitting} sx={{ height: 40, fontWeight: 700 }}>
                  {submitting ? 'Queuing…' : 'Submit Backtest'}
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

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
                        <TableCell>Strategy</TableCell>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Exchange</TableCell>
                        <TableCell>Timeframe</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Submitted</TableCell>
                        <TableCell align="right">Net PnL</TableCell>
                        <TableCell align="right">Win Rate</TableCell>
                        <TableCell align="right">Sharpe</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {backtests.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((bt) => (
                        <TableRow
                          key={bt.backtest_id}
                          hover
                          onClick={() => bt.status === 'completed' && navigate(`/backtests/${bt.backtest_id}`)}
                          sx={{ cursor: bt.status === 'completed' ? 'pointer' : 'default' }}
                        >
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>
                              {bt.strategy_name}
                            </Typography>
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
                              {new Date(bt.submitted_at).toLocaleDateString()}
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
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <TablePagination
                  component="div"
                  count={backtests.length}
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
