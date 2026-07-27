import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Button from '@mui/material/Button';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import EquityCurveChart from '../../components/charts/EquityCurveChart';
import DailyReturnsChart from '../../components/charts/DailyReturnsChart';
import PositionSizeChart from '../../components/charts/PositionSizeChart';
import TradeHistoryChart from '../../components/charts/TradeHistoryChart';
import TradePnlChart from '../../components/charts/TradePnlChart';
import LedgerFilterBar, { filterLedgerRows } from '../../components/ui/LedgerFilterBar';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getDeploymentById } from '../../api/deploymentApi';
import { COLORS } from '../../theme/theme';

import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';

function InfoRow({ label, value, color }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.75, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
      <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>{label}</Typography>
      <Typography variant="body2" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: color || theme.palette.text.primary }}>{value ?? '—'}</Typography>
    </Box>
  );
}

function ChartCard({ title, children, height = 240 }) {
  return (
    <Card>
      <CardContent sx={{ p: '20px !important' }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>{title}</Typography>
        <Box sx={{ height }}>{children}</Box>
      </CardContent>
    </Card>
  );
}

export default function ExecutionDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const [ledgerFilters, setLedgerFilters] = React.useState({ startDate: '', endDate: '', side: 'all', symbol: '' });

  const { data: exec, loading, error } = useMockFetch(() => getDeploymentById(id), [id]);

  const rawSignals = exec?.signal_history ?? [];
  const filteredSignals = filterLedgerRows(rawSignals, ledgerFilters);
  const rawTrades = exec?.trades ?? [];
  const filteredTrades = filterLedgerRows(rawTrades, ledgerFilters);

  if (loading) return <PageContainer title="Execution Details" breadcrumbs="Execution"><Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box></PageContainer>;
  if (error || !exec) return (
    <PageContainer title="Execution Details" breadcrumbs="Execution">
      <EmptyState icon={ErrorOutlineRoundedIcon} title="Execution not found" description={error || 'The requested execution instance does not exist.'} action={<Button onClick={() => navigate('/deployment')}>Back to Execution</Button>} />
    </PageContainer>
  );

  const pos = exec.active_position;

  // Build trade markers for TradeHistoryChart
  const tradeMarkers = (exec.signal_history ?? [])
    .filter((s) => s.triggered && s.signal !== 'flat')
    .map((s) => ({
      time: s.timestamp.split('T')[0],
      position: s.signal === 'long' ? 'belowBar' : 'aboveBar',
      color: s.signal === 'long' ? COLORS.pnlGreen : COLORS.pnlRed,
      shape: s.signal === 'long' ? 'arrowUp' : 'arrowDown',
      text: s.signal.toUpperCase(),
    }));

  return (
    <PageContainer title={exec.strategy_name} breadcrumbs="Execution">
      <Box sx={{ pt: 3 }}>
        <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/deployment')} size="small" sx={{ mb: 2 }}>Back</Button>

        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Typography variant="h2" sx={{ fontWeight: 700 }}>{exec.strategy_name}</Typography>
          <StatusChip status={exec.status} size="medium" />
          <Chip label={exec.symbol} sx={{ color: COLORS.accent, background: `${COLORS.accent}15` }} />
          <Chip label={exec.exchange} />
          <Chip label={exec.wallet_label} />
        </Box>

        {/* PnL summary */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            { label: 'Current PnL', value: `${exec.current_pnl >= 0 ? '+' : ''}$${exec.current_pnl?.toFixed(2)}`, color: exec.current_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
            { label: 'PnL %', value: `${exec.current_pnl_pct >= 0 ? '+' : ''}${(exec.current_pnl_pct * 100).toFixed(2)}%`, color: exec.current_pnl_pct >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
            { label: 'Daily Return', value: `${exec.daily_return >= 0 ? '+' : ''}${(exec.daily_return * 100).toFixed(2)}%`, color: exec.daily_return >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
            { label: 'Last Signal', value: exec.last_signal?.toUpperCase() },
            { label: 'Last Execution', value: new Date(exec.last_execution_time).toLocaleString() },
            { label: 'Running Since', value: new Date(exec.started_at).toLocaleDateString() },
          ].map(({ label, value, color }) => (
            <Grid item xs={6} sm={4} md={2} key={label}>
              <Card sx={{ textAlign: 'center', p: 1.5 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block' }}>{label}</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: color || theme.palette.text.primary, fontSize: '1rem', mt: 0.5 }}>{value}</Typography>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Config + Current Position */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: '20px !important' }}>
                <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Simulation Config</Typography>
                <InfoRow label="Initial Balance" value={`$${exec.initial_balance?.toLocaleString()}`} />
                <InfoRow label="Position Size Type" value={exec.position_size_type} />
                <InfoRow label="Position Size Value" value={exec.position_size_type === 'percent' ? `${(exec.position_size_value * 100).toFixed(0)}%` : `$${exec.position_size_value}`} />
                <InfoRow label="Commission" value={`${(exec.commission * 100).toFixed(2)}%`} />
                <InfoRow label="Slippage" value={`${(exec.slippage * 100).toFixed(2)}%`} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={8}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: '20px !important' }}>
                <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Current Position</Typography>
                {!pos ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', height: 80 }}>
                    <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>No active position</Typography>
                  </Box>
                ) : (
                  <Grid container spacing={2}>
                    <Grid item xs={6} md={3}><InfoRow label="Symbol" value={pos.symbol} /></Grid>
                    <Grid item xs={6} md={3}><InfoRow label="Side" value={<StatusChip status={pos.side} />} /></Grid>
                    <Grid item xs={6} md={3}><InfoRow label="Entry Price" value={`$${pos.entry_price?.toLocaleString()}`} /></Grid>
                    <Grid item xs={6} md={3}><InfoRow label="Current Price" value={`$${pos.current_price?.toLocaleString()}`} /></Grid>
                    <Grid item xs={6} md={3}><InfoRow label="Take Profit" value={(pos.tp ?? pos.take_profit) != null ? `$${pos.tp ?? pos.take_profit}` : '—'} color={COLORS.pnlGreen} /></Grid>
                    <Grid item xs={6} md={3}><InfoRow label="Stop Loss" value={(pos.sl ?? pos.stop_loss) != null ? `$${pos.sl ?? pos.stop_loss}` : '—'} color={COLORS.pnlRed} /></Grid>
                    <Grid item xs={6} md={3}><InfoRow label="Unrealized PnL" value={`${pos.unrealized_pnl >= 0 ? '+' : ''}$${pos.unrealized_pnl?.toFixed(2)}`} color={pos.unrealized_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed} /></Grid>
                    <Grid item xs={6} md={3}><InfoRow label="Opened" value={new Date(pos.opened_at).toLocaleString()} /></Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={8}>
            <ChartCard title="Equity Curve" height={300}>
              <EquityCurveChart data={exec.equity_curve ?? []} height={300} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={4}>
            <ChartCard title="Net PnL Per Trade ($)" height={300}>
              <TradePnlChart data={exec.pnl_per_trade?.length ? exec.pnl_per_trade : (exec.trades?.length ? exec.trades : (exec.daily_returns ?? []))} height={280} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Position Size per Trade" height={280}>
              <PositionSizeChart data={exec.position_size_history ?? []} height={280} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Trade History (Entry/Exit Markers)" height={280}>
              <TradeHistoryChart equityData={exec.equity_curve ?? []} markers={tradeMarkers} height={280} />
            </ChartCard>
          </Grid>
        </Grid>

        {/* Execution Trade Ledgers Table */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
              Execution Trade Ledgers ({filteredTrades.length} trades recorded)
            </Typography>
            <LedgerFilterBar onChange={setLedgerFilters} />
            {!filteredTrades.length ? (
              <EmptyState icon={ShowChartRoundedIcon} title="No trades found" description="No trade ledgers recorded for this strategy execution run yet." />
            ) : (
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Trade ID</TableCell>
                      <TableCell>Direction</TableCell>
                      <TableCell>Entry Time</TableCell>
                      <TableCell>Exit Time</TableCell>
                      <TableCell align="right">Entry Price</TableCell>
                      <TableCell align="right">Exit Price</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell align="right">Net PnL ($)</TableCell>
                      <TableCell>Exit Reason</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredTrades.map((t) => (
                      <TableRow key={t.trade_id} hover>
                        <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{t.trade_id}</Typography></TableCell>
                        <TableCell><StatusChip status={t.side} /></TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontSize: 12 }}>{t.entry_time?.replace('Z', '').replace('UTC', '')}</Typography></TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontSize: 12 }}>{t.exit_time?.replace('Z', '').replace('UTC', '')}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${t.entry_price?.toLocaleString()}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${t.exit_price?.toLocaleString()}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{t.quantity}</Typography></TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: t.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                            {t.net_pnl >= 0 ? '+' : ''}${t.net_pnl?.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontSize: 12 }}>{t.exit_reason}</Typography></TableCell>
                        <TableCell><StatusChip status={t.status || 'Completed'} /></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>

        {/* Signal History */}
        <Card>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Signal History ({filteredSignals.length} displayed)</Typography>
            <LedgerFilterBar onChange={setLedgerFilters} />
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Signal</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell>Triggered</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredSignals.slice(0, 20).map((s) => (
                    <TableRow key={s.signal_id} hover>
                      <TableCell>{s.signal_id}</TableCell>
                      <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{new Date(s.timestamp).toLocaleString()}</Typography></TableCell>
                      <TableCell><StatusChip status={s.signal === 'flat' ? 'neutral' : s.signal} label={s.signal?.toUpperCase()} /></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${s.price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                      <TableCell>
                        <Chip label={s.triggered ? 'Yes' : 'No'} size="small" sx={{ height: 20, fontSize: 11, color: s.triggered ? COLORS.pnlGreen : theme.palette.text.secondary, background: s.triggered ? `${COLORS.pnlGreen}15` : 'rgba(139,147,167,0.1)' }} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>
    </PageContainer>
  );
}
