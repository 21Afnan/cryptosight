import React, { useState } from 'react';
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

function StatBox({ label, value, color }) {
  const theme = useTheme();
  return (
    <Box sx={{ textAlign: 'center', p: 2 }}>
      <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mb: 0.5 }}>{label}</Typography>
      <Typography variant="h4" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: color || theme.palette.text.primary }}>
        {value}
      </Typography>
    </Box>
  );
}

function ChartCard({ title, children, height }) {
  return (
    <Card>
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
          <Card>
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
                            <TableSortLabel active={sortField === 'max_drawdown'} direction={sortField === 'max_drawdown' ? sortOrder : 'desc'} onClick={() => handleSort('max_drawdown')}>
                              Max DD
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
                            <TableCell align="right"><Typography variant="body2" sx={{ color: COLORS.pnlRed, fontVariantNumeric: 'tabular-nums' }}>{s.max_drawdown != null ? `${(s.max_drawdown * 100).toFixed(1)}%` : '—'}</Typography></TableCell>
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

// Strategy Detail view
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

  const indicators = Object.entries(strategy.indicators_config ?? {});

  return (
    <PageContainer title={strategy.strategy_name} breadcrumbs="Strategies">
      <Box sx={{ pt: 3 }}>
        <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/strategies')} size="small" sx={{ mb: 2 }}>Back</Button>

        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Typography variant="h2" sx={{ fontWeight: 700 }}>{strategy.strategy_name}</Typography>
          <StatusChip status={strategy.status} size="medium" />
          <Chip label={strategy.symbol} sx={{ color: COLORS.accent, background: `${COLORS.accent}15` }} />
          <Chip label={strategy.exchange} />
          <Chip label={strategy.target_timeframe} />
        </Box>

        {/* Performance Summary */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Performance Summary</Typography>
            <Grid container spacing={1.5}>
              {(() => {
                const perf = strategy.performance || {};
                const netPnl = perf.net_pnl ?? strategy.net_pnl ?? 0;
                const winRate = perf.win_rate ?? strategy.win_rate;
                const sharpe = perf.sharpe ?? strategy.sharpe;
                const sortino = perf.sortino ?? strategy.sortino;
                const calmar = perf.calmar ?? strategy.calmar;
                const maxDd = perf.max_drawdown ?? strategy.max_drawdown;
                const cagr = perf.cagr ?? strategy.cagr;
                const totalTrades = perf.total_trades ?? strategy.total_trades ?? 0;

                return [
                  { label: 'Net PnL', value: `${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)}`, color: netPnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
                  { label: 'Win Rate', value: winRate != null ? `${(winRate * 100).toFixed(1)}%` : '—' },
                  { label: 'Sharpe Ratio', value: typeof sharpe === 'number' ? sharpe.toFixed(2) : '—' },
                  { label: 'Sortino Ratio', value: typeof sortino === 'number' ? sortino.toFixed(2) : '—' },
                  { label: 'Calmar Ratio', value: typeof calmar === 'number' ? calmar.toFixed(2) : '—' },
                  { label: 'Max Drawdown', value: typeof maxDd === 'number' ? `${(maxDd * 100).toFixed(1)}%` : '—', color: COLORS.pnlRed },
                  { label: 'CAGR', value: typeof cagr === 'number' ? `${(cagr * 100).toFixed(1)}%` : '—', color: COLORS.pnlGreen },
                  { label: 'Total Trades', value: totalTrades },
                ].map((stat) => (
                  <Grid item xs={6} sm={3} md={3} lg={1.5} key={stat.label}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: '12px',
                        background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
                        textAlign: 'center',
                        transition: 'all 200ms ease',
                        '&:hover': {
                          borderColor: COLORS.accent,
                          transform: 'translateY(-2px)',
                        },
                      }}
                    >
                      <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mb: 0.5, fontSize: '0.6875rem', fontWeight: 600 }}>
                        {stat.label}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: stat.color || theme.palette.text.primary, fontSize: '1.05rem', lineHeight: 1.2 }}>
                        {stat.value}
                      </Typography>
                    </Box>
                  </Grid>
                ));
              })()}
            </Grid>
          </CardContent>
        </Card>

        {/* Configuration & Risk Management Cards (2 equal flashcards) */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mb: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: '20px !important' }}>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Configuration</Typography>
              {(() => {
                const cfg = strategy.configuration || {};
                return [
                  ['Exchange', cfg.exchange || strategy.exchange],
                  ['Symbol', cfg.symbol || strategy.symbol],
                  ['Target Timeframe', cfg.target_timeframe || strategy.target_timeframe],
                  ['Base Timeframe', cfg.base_timeframe || strategy.timeframe || '—'],
                  ['Long Signals', cfg.long_signals ?? strategy.long_signals ?? '—'],
                  ['Short Signals', cfg.short_signals ?? strategy.short_signals ?? '—'],
                  ['Total Rows', cfg.total_rows != null ? cfg.total_rows.toLocaleString() : (strategy.total_rows ? strategy.total_rows.toLocaleString() : '—')],
                  ['Last Signal', cfg.last_signal || (strategy.last_signal_time ? new Date(strategy.last_signal_time).toLocaleString() : '—')],
                ].map(([k, v]) => (
                  <Box key={k} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.75, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                    <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>{k}</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{v ?? '—'}</Typography>
                  </Box>
                ));
              })()}
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: '20px !important' }}>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Risk Management</Typography>
              {(() => {
                const rm = strategy.risk_management || {};
                const sc = strategy.strategy_config || {};
                const bc = strategy.backtest_config || {};
                return [
                  ['Take Profit', rm.take_profit || (sc.take_profit != null ? `${(sc.take_profit * 100).toFixed(1)}%` : '—')],
                  ['Stop Loss', rm.stop_loss || (sc.stop_loss != null ? `${(sc.stop_loss * 100).toFixed(1)}%` : '—')],
                  ['Position Size', rm.position_size || (sc.position_size != null ? `${(sc.position_size * 100).toFixed(0)}%` : '—')],
                  ['Commission', rm.commission || (bc.commission != null ? `${(bc.commission * 100).toFixed(2)}%` : '—')],
                  ['Slippage', rm.slippage || (bc.slippage != null ? `${(bc.slippage * 100).toFixed(2)}%` : '—')],
                ].map(([k, v]) => (
                  <Box key={k} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.75, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                    <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>{k}</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{v}</Typography>
                  </Box>
                ));
              })()}
            </CardContent>
          </Card>
        </Box>

        {/* 4 Performance Charts: 2 per row (2 in row 1, 2 in row 2) */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mb: 3 }}>
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
        <Card sx={{ width: '100%' }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Recent Trades</Typography>
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
                        <TableCell><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontSize: 12 }}>{trade.entry_time || '—'}</Typography></TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontSize: 12 }}>{trade.exit_time || '—'}</Typography></TableCell>
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
