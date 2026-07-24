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
import InputLabel from '@mui/material/InputLabel';
import OutlinedInput from '@mui/material/OutlinedInput';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';
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
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

const STATUS_TABS = ['all', 'pending', 'running', 'completed', 'failed'];

const DEFAULT_FORM = {
  strategy_name: '',
  symbol: '',
  exchange: '',
  timeframe: '',
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  initial_balance: 10000,
  commission: 0.0005,
  slippage: 0.0002,
  take_profit: 0.04,
  stop_loss: 0.02,
};

function FormRow({ label, children }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>{label}</Typography>
      {children}
    </Box>
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

  const { data, loading, error, refetch } = useMockFetch(
    () => getBacktests({ search, filter: filterObj }),
    [search, tabIdx],
  );
  const { data: mktData } = useMockFetch(getMarketDataOptions);
  const backtests = data?.data ?? [];

  const symbols = [...new Set((mktData?.data ?? []).map((m) => m.symbol))];
  const exchanges = [...new Set((mktData?.data ?? []).map((m) => m.exchange))];
  const timeframes = [...new Set((mktData?.data ?? []).map((m) => m.timeframe))];

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await submitBacktest(form);
      setSnack({ severity: 'success', message: 'Backtest queued successfully' });
      refetch();
      setForm(DEFAULT_FORM);
    } catch (e) {
      setSnack({ severity: 'error', message: 'Failed to submit backtest' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageContainer title="Backtest Requests">
      <Box sx={{ pt: 3 }}>
        {/* Config form */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2.5, fontWeight: 700 }}>New Backtest Request</Typography>
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
                <Button id="submit-backtest-btn" variant="contained" fullWidth startIcon={<SendRoundedIcon />} onClick={handleSubmit} disabled={submitting}>
                  {submitting ? 'Queuing…' : 'Submit Backtest'}
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Tabbed list */}
        <Card>
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Tabs value={tabIdx} onChange={(_, v) => setTabIdx(v)} sx={{ minHeight: '36px' }}>
                {STATUS_TABS.map((s) => <Tab key={s} label={s.charAt(0).toUpperCase() + s.slice(1)} sx={{ minHeight: '36px', py: 0 }} />)}
              </Tabs>
              <SearchBar onSearch={setSearch} placeholder="Search backtests…" />
            </Box>

            {loading ? <LoadingSkeleton variant="table" /> : backtests.length === 0 ? (
              <EmptyState icon={HistoryRoundedIcon} title="No backtests" description={`No ${activeStatus === 'all' ? '' : activeStatus} backtests found.`} />
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
                          <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{bt.strategy_name}</Typography></TableCell>
                          <TableCell><Typography variant="body2" sx={{ color: COLORS.accent, fontWeight: 500 }}>{bt.symbol}</Typography></TableCell>
                          <TableCell>{bt.exchange}</TableCell>
                          <TableCell>{bt.timeframe}</TableCell>
                          <TableCell>
                            <Box>
                              <StatusChip status={bt.status} />
                              {bt.status === 'running' && bt.progress != null && (
                                <LinearProgress variant="determinate" value={bt.progress * 100} sx={{ mt: 0.5, height: 3, borderRadius: 2 }} />
                              )}
                              {bt.error_message && (
                                <Typography variant="caption" sx={{ color: COLORS.pnlRed, display: 'block', mt: 0.25, fontSize: 10 }}>{bt.error_message.substring(0, 50)}…</Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell><Typography variant="body2" sx={{ fontSize: 12 }}>{new Date(bt.submitted_at).toLocaleString()}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ color: bt.net_pnl != null ? (bt.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed) : 'inherit', fontVariantNumeric: 'tabular-nums', fontWeight: 700 }}>{bt.net_pnl != null ? `${bt.net_pnl >= 0 ? '+' : ''}$${bt.net_pnl?.toFixed(0)}` : '—'}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{bt.win_rate != null ? `${(bt.win_rate * 100).toFixed(1)}%` : '—'}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{bt.sharpe?.toFixed(2) ?? '—'}</Typography></TableCell>
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
