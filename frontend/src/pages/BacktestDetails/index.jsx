import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Button from '@mui/material/Button';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import EquityCurveChart from '../../components/charts/EquityCurveChart';
import DrawdownChart from '../../components/charts/DrawdownChart';
import MonthlyReturnsChart from '../../components/charts/MonthlyReturnsChart';
import RollingMetricsChart from '../../components/charts/RollingMetricsChart';
import LedgerFilterBar, { filterLedgerRows } from '../../components/ui/LedgerFilterBar';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getBacktestById } from '../../api/backtestsApi';
import { COLORS } from '../../theme/theme';

import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

function StatBox({ label, value, color }) {
  const theme = useTheme();
  return (
    <Box sx={{ textAlign: 'center', p: 2 }}>
      <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mb: 0.5 }}>{label}</Typography>
      <Typography variant="h4" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: color || theme.palette.text.primary, fontSize: '1.25rem' }}>
        {value}
      </Typography>
    </Box>
  );
}

function ChartCard({ title, children, height = 280 }) {
  return (
    <Card>
      <CardContent sx={{ p: '20px !important' }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>{title}</Typography>
        <Box sx={{ height }}>{children}</Box>
      </CardContent>
    </Card>
  );
}

export default function BacktestDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const [snack, setSnack] = React.useState(null);
  const [ledgerFilters, setLedgerFilters] = React.useState({ startDate: '', endDate: '', side: 'all', symbol: '' });
  const { data: bt, loading, error } = useMockFetch(() => getBacktestById(id), [id]);

  const rawTrades = bt?.trades ?? [];
  const filteredTrades = filterLedgerRows(rawTrades, ledgerFilters);

  if (loading) return <PageContainer title="Backtest Details" breadcrumbs="Backtests"><Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box></PageContainer>;
  if (error || !bt) return (
    <PageContainer title="Backtest Details" breadcrumbs="Backtests">
      <EmptyState icon={ErrorOutlineRoundedIcon} title="Backtest not found" description={error || 'The requested backtest does not exist.'} action={<Button onClick={() => navigate('/backtests')}>Back to Backtests</Button>} />
    </PageContainer>
  );

  return (
    <PageContainer title={`${bt.strategy_name} — Backtest`} breadcrumbs="Backtests">
      <Box sx={{ pt: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/backtests')} size="small">Back</Button>
          <Button
            id="export-report-btn"
            startIcon={<DownloadRoundedIcon />}
            variant="outlined"
            size="small"
            onClick={() => setSnack({ severity: 'info', message: 'Report export queued — PDF generation not available in mock mode.' })}
          >
            Export Report
          </Button>
        </Box>

        {/* Full Stats Panel */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Backtest Results</Typography>
            <Grid container>
              {[
                { label: 'Net PnL', value: bt.net_pnl != null ? `$${bt.net_pnl?.toFixed(2)}` : '—', color: bt.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
                { label: 'Final Balance', value: bt.final_balance != null ? `$${bt.final_balance?.toFixed(2)}` : '—' },
                { label: 'Total Trades', value: bt.total_trades ?? '—' },
                { label: 'Win Rate', value: bt.win_rate != null ? `${(bt.win_rate * 100).toFixed(1)}%` : '—', color: COLORS.pnlGreen },
                { label: 'Sharpe Ratio', value: bt.sharpe?.toFixed(2) ?? '—' },
                { label: 'Sortino Ratio', value: bt.sortino?.toFixed(2) ?? '—' },
                { label: 'Calmar Ratio', value: bt.calmar?.toFixed(2) ?? '—' },
                { label: 'CAGR', value: bt.cagr != null ? `${(bt.cagr * 100).toFixed(1)}%` : '—', color: COLORS.pnlGreen },
                { label: 'Max Drawdown', value: bt.max_drawdown != null ? `${(bt.max_drawdown * 100).toFixed(1)}%` : '—', color: COLORS.pnlRed },
                { label: 'Profit Factor', value: bt.profit_factor?.toFixed(2) ?? '—' },
                { label: 'Avg Trade PnL', value: bt.avg_trade_pnl != null ? `$${bt.avg_trade_pnl?.toFixed(2)}` : '—' },
                { label: 'Avg Win / Loss', value: (bt.avg_win != null && bt.avg_loss != null) ? `$${bt.avg_win?.toFixed(0)} / $${bt.avg_loss?.toFixed(0)}` : '—' },
              ].map((stat) => (
                <Grid item xs={6} sm={4} md={3} lg={2} key={stat.label}>
                  <StatBox {...stat} />
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>

        {/* Backtest Config */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Backtest Configuration</Typography>
            <Grid container spacing={2}>
              {[
                ['Symbol', bt.symbol],
                ['Exchange', bt.exchange],
                ['Timeframe', bt.timeframe],
                ['Start Date', bt.backtest_config?.start_date],
                ['End Date', bt.backtest_config?.end_date],
                ['Initial Balance', bt.backtest_config?.initial_balance != null ? `$${bt.backtest_config?.initial_balance?.toLocaleString()}` : '—'],
                ['Commission', bt.backtest_config?.commission != null ? `${(bt.backtest_config?.commission * 100).toFixed(3)}%` : '—'],
                ['Slippage', bt.backtest_config?.slippage != null ? `${(bt.backtest_config?.slippage * 100).toFixed(3)}%` : '—'],
                ['Take Profit', bt.backtest_config?.take_profit != null ? `${(bt.backtest_config?.take_profit * 100).toFixed(1)}%` : '—'],
                ['Stop Loss', bt.backtest_config?.stop_loss != null ? `${(bt.backtest_config?.stop_loss * 100).toFixed(1)}%` : '—'],
              ].map(([label, value]) => (
                <Grid item xs={6} sm={4} md={3} lg={2} key={label}>
                  <Box>
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>{label}</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums', mt: 0.25 }}>{value ?? '—'}</Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>

        {/* Charts */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={8}>
            <ChartCard title="Equity Curve" height={300}>
              <EquityCurveChart data={bt.equity_curve ?? []} height={300} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={4}>
            <ChartCard title="Drawdown" height={300}>
              <DrawdownChart data={bt.drawdown_curve ?? []} height={300} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Monthly Returns" height={270}>
              <MonthlyReturnsChart data={bt.monthly_returns ?? []} height={270} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Rolling Metrics (Sharpe · Sortino · Calmar)" height={270}>
              <RollingMetricsChart data={bt.rolling_metrics ?? []} height={270} />
            </ChartCard>
          </Grid>
        </Grid>

        {/* Trade List */}
        <Card>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Trade List ({filteredTrades.length} displayed)</Typography>
            <LedgerFilterBar onChange={setLedgerFilters} />
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
                    <TableCell align="right">Size</TableCell>
                    <TableCell align="right">Net PnL</TableCell>
                    <TableCell align="right">Return %</TableCell>
                    <TableCell align="right">Fees</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredTrades.slice(0, 50).map((trade) => (
                    <TableRow key={trade.trade_id} hover>
                      <TableCell>{trade.trade_id}</TableCell>
                      <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{new Date(trade.entry_time).toLocaleDateString()}</Typography></TableCell>
                      <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{new Date(trade.exit_time).toLocaleDateString()}</Typography></TableCell>
                      <TableCell><StatusChip status={trade.side} /></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${trade.entry_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${trade.exit_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${trade.position_size?.toFixed(0)}</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ color: trade.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{trade.net_pnl >= 0 ? '+' : ''}${trade.net_pnl?.toFixed(2)}</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ color: trade.return_pct >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{trade.return_pct >= 0 ? '+' : ''}{trade.return_pct?.toFixed(2)}%</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', color: theme.palette.text.secondary }}>${trade.fees?.toFixed(2)}</Typography></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity={snack?.severity} onClose={() => setSnack(null)}>{snack?.message}</Alert>
      </Snackbar>
    </PageContainer>
  );
}
