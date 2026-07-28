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
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Button from '@mui/material/Button';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import EquityCurveChart from '../../components/charts/EquityCurveChart';
import DrawdownChart from '../../components/charts/DrawdownChart';
import MonthlyReturnsChart from '../../components/charts/MonthlyReturnsChart';
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
import TuneRoundedIcon from '@mui/icons-material/TuneRounded';

function safeCurrency(val, fallback = '—') {
  if (val === null || val === undefined) return fallback;
  const n = Number(val);
  if (isNaN(n)) return fallback;
  return `${n >= 0 ? '+' : '-'}$${Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function safePercent(val, fallback = '—') {
  if (val === null || val === undefined) return fallback;
  const n = Number(val);
  if (isNaN(n)) return fallback;
  return `${n >= 0 ? '+' : ''}${(n * (Math.abs(n) <= 1.0 ? 100 : 1)).toFixed(2)}%`;
}

function safeDate(val, fallback = '—') {
  if (!val || val === '—' || val === 'Invalid Date') return fallback;
  try {
    const str = String(val).split('.')[0].replace('Z', '').replace('UTC', '').replace('+00:00', '').trim();
    const d = new Date(str.includes(' ') ? str.replace(' ', 'T') : str);
    if (isNaN(d.getTime())) return str;
    return d.toLocaleString('en-US', { month: 'short', day: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
  } catch {
    return fallback;
  }
}

function formatCleanDate(val, fallback = '—') {
  if (!val || val === '—' || val === 'null' || val === 'undefined') return fallback;
  return String(val)
    .split('.')[0]
    .replace('T', ' ')
    .replace('+00:00', '')
    .replace('Z', '')
    .replace('UTC', '')
    .trim();
}

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
  const [chartTab, setChartTab] = React.useState(0);

  const { data: exec, loading, error } = useMockFetch(() => getDeploymentById(id), [id]);

  const rawTrades = exec?.trades ?? [];
  const filteredTrades = filterLedgerRows(rawTrades, ledgerFilters);

  if (loading) return <PageContainer title="Execution Details" breadcrumbs="Execution"><Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box></PageContainer>;
  if (error || !exec) return (
    <PageContainer title="Execution Details" breadcrumbs="Execution">
      <EmptyState icon={ErrorOutlineRoundedIcon} title="Execution not found" description={error || 'The requested execution instance does not exist.'} action={<Button onClick={() => navigate('/deployment')}>Back to Execution</Button>} />
    </PageContainer>
  );

  if (exec.has_ledger === false) return (
    <PageContainer title={exec.strategy_name} breadcrumbs="Execution">
      <Box sx={{ pt: 3 }}>
        <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/deployment')} size="small" sx={{ mb: 2 }}>Back</Button>
        <EmptyState
          icon={ErrorOutlineRoundedIcon}
          title="Execution Ledger Not Found"
          description={`No trade ledger table (execution_ledgers) exists for '${exec.strategy_name}' in the database yet. Details will open once trades are recorded in database.`}
          action={<Button onClick={() => navigate('/deployment')}>Back to Execution</Button>}
        />
      </Box>
    </PageContainer>
  );

  const pos = exec.active_position;

  // Derive position size data from real DB trades if position_size_history is empty
  const positionSizeData = exec.position_size_history?.length
    ? exec.position_size_history
    : (exec.trades ?? []).map((t, idx) => {
        const rawVal = t.quantity && t.entry_price ? (t.quantity * t.entry_price) : (t.quantity || 1000);
        return {
          trade: t.trade_id || `#${idx + 1}`,
          size: Math.round(Number(rawVal) || 1000),
          side: (t.side || 'LONG').toLowerCase(),
        };
      });

  // Build trade markers for TradeHistoryChart directly from real DB trades or signals
  const tradeMarkers = (exec.trades?.length ? exec.trades : (exec.signal_history ?? []))
    .map((t, idx) => {
      const rawTime = t.exit_time || t.entry_time || t.timestamp || '';
      const cleanTime = String(rawTime).split(' ')[0].split('T')[0];
      const isLong = (t.side || t.signal || 'LONG').toUpperCase() === 'LONG';
      return {
        time: cleanTime,
        position: isLong ? 'belowBar' : 'aboveBar',
        color: isLong ? COLORS.pnlGreen : COLORS.pnlRed,
        shape: isLong ? 'arrowUp' : 'arrowDown',
        text: t.trade_id || (isLong ? 'BUY' : 'SELL'),
      };
    })
    .filter((m) => Boolean(m.time));

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
          <Chip label={exec.wallet_label || `Live ${exec.exchange} Wallet`} />
        </Box>

        {/* PnL & Performance Key Stats Matrix (8 Cards filling 100% full width) */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)', lg: 'repeat(4, 1fr)' },
            gap: 2,
            mb: 3,
            width: '100%',
            boxSizing: 'border-box',
          }}
        >
          {[
            { label: 'Current PnL', value: safeCurrency(exec.current_pnl ?? exec.net_pnl), color: (exec.current_pnl ?? exec.net_pnl ?? 0) >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
            { label: 'PnL %', value: safePercent(exec.current_pnl_pct), color: (exec.current_pnl_pct ?? 0) >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
            { label: 'Win Rate', value: safePercent(exec.win_rate), color: (exec.win_rate ?? 0) >= 0.5 ? COLORS.pnlGreen : theme.palette.text.primary, sub: exec.winning_trades != null ? `${exec.winning_trades}W / ${exec.losing_trades ?? 0}L` : '' },
            { label: 'Profit Factor', value: exec.profit_factor ? Number(exec.profit_factor).toFixed(2) : '—', color: (exec.profit_factor ?? 0) >= 1.2 ? COLORS.pnlGreen : theme.palette.text.primary },
            { label: 'Total Trades', value: exec.total_trades != null ? `${exec.total_trades} trades` : '—' },
            { label: 'Max Drawdown', value: safePercent(exec.max_drawdown), color: (exec.max_drawdown ?? 0) < 0 ? COLORS.pnlRed : theme.palette.text.primary },
            { label: 'Last Signal', value: exec.last_signal ? String(exec.last_signal).toUpperCase() : '—' },
            { label: 'Last Execution', value: safeDate(exec.last_execution_time) },
          ].map(({ label, value, color, sub }) => (
            <Card key={label} sx={{ textAlign: 'center', p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', boxShadow: isDark ? '0 4px 16px rgba(0,0,0,0.3)' : '0 6px 20px rgba(0,0,0,0.06)' }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 10, display: 'block' }}>{label}</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: color || theme.palette.text.primary, fontSize: '1.05rem', mt: 0.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</Typography>
              {sub && <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontSize: 10, mt: 0.25 }}>{sub}</Typography>}
            </Card>
          ))}
        </Box>

        {/* Execution Configuration Card (Attractive Parameter Matrix) */}
        <Card
          sx={{
            mb: 3,
            background: isDark ? COLORS.darkSurface : '#ffffff',
            border: 'none',
            boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.4)' : '0 8px 26px rgba(14, 203, 129, 0.24)',
            borderRadius: 2.5,
            width: '100%',
          }}
        >
          <CardContent sx={{ p: '20px !important', boxSizing: 'border-box', width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TuneRoundedIcon sx={{ color: COLORS.pnlGreen }} />
                <Typography variant="h5" sx={{ fontWeight: 800 }}>
                  Execution Configuration
                </Typography>
              </Box>
              <Chip label={exec.status?.toUpperCase() || 'ACTIVE'} size="small" sx={{ height: 22, fontSize: 11, fontWeight: 700, background: 'rgba(14, 203, 129, 0.15)', color: '#0ECB81' }} />
            </Box>

            {/* 8 Clean Parameter Matrix Boxes */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)', lg: 'repeat(4, 1fr)' },
                gap: 1.5,
                width: '100%',
                boxSizing: 'border-box',
              }}
            >
              {[
                ['Reference Balance', exec.reference_balance ? `$${Number(exec.reference_balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '$10,000.00'],
                ['Exchange', exec.exchange || 'BYBIT'],
                ['Symbol', exec.symbol || 'BTC/USDT'],
                ['Timeframe', exec.timeframe || '15m'],
                ['Contract Category', exec.category || 'Linear'],
                ['Order Type', exec.order_type || 'Market'],
                ['Position Size Type', exec.position_size_type || 'Percent'],
                ['Position Size Value', safePercent(exec.position_size_value)],
              ].map(([label, value]) => (
                <Box
                  key={label}
                  sx={{
                    p: '12px 14px',
                    minHeight: '62px',
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
                  <Typography variant="body2" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', mt: 0.5, color: theme.palette.text.primary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {value ?? '—'}
                  </Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Performance Charts & Oscillators Card (Tabs matching Backtest Details) */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2.5, flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                Performance Charts & Oscillators
              </Typography>
              <Tabs
                value={chartTab}
                onChange={(_, v) => {
                  setChartTab(v);
                  setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
                }}
                sx={{ minHeight: '36px' }}
              >
                <Tab label="Equity Curve & Drawdown" sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
                <Tab label="PnL Per Trade" sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
                <Tab label="Trade History & Position Size" sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
                <Tab label="Monthly Returns" sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
              </Tabs>
            </Box>

            {chartTab === 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%' }}>
                <Box sx={{ width: '100%', minWidth: 0 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                    Equity Curve Trajectory
                  </Typography>
                  <Box sx={{ height: 320, width: '100%', minWidth: 0, position: 'relative' }}>
                    <EquityCurveChart data={exec.equity_curve ?? []} height={320} />
                  </Box>
                </Box>

                <Box sx={{ width: '100%', minWidth: 0 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                    Underwater Drawdown
                  </Typography>
                  <Box sx={{ height: 260, width: '100%', minWidth: 0, position: 'relative' }}>
                    <DrawdownChart data={exec.drawdown_curve ?? []} height={260} />
                  </Box>
                </Box>
              </Box>
            )}

            {chartTab === 1 && (
              <Box sx={{ width: '100%', height: 360 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Net PnL Per Trade ($)
                </Typography>
                <TradePnlChart data={(exec.pnl_per_trade?.length && exec.pnl_per_trade.length >= exec.trades?.length) ? exec.pnl_per_trade : (exec.trades ?? [])} height={340} />
              </Box>
            )}

            {chartTab === 2 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%' }}>
                <Box sx={{ width: '100%', minWidth: 0 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                    Position Size per Trade
                  </Typography>
                  <Box sx={{ height: 280, width: '100%', minWidth: 0, position: 'relative' }}>
                    <PositionSizeChart data={positionSizeData} height={280} />
                  </Box>
                </Box>

                <Box sx={{ width: '100%', minWidth: 0 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                    Trade History (Entry/Exit Markers)
                  </Typography>
                  <Box sx={{ height: 280, width: '100%', minWidth: 0, position: 'relative' }}>
                    <TradeHistoryChart equityData={exec.equity_curve ?? []} markers={tradeMarkers} height={280} />
                  </Box>
                </Box>
              </Box>
            )}

            {chartTab === 3 && (
              <Box sx={{ width: '100%', height: 360 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Monthly Returns Breakdown
                </Typography>
                <MonthlyReturnsChart data={exec.monthly_returns ?? []} height={340} />
              </Box>
            )}
          </CardContent>
        </Card>

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
                      <TableCell align="right">Return %</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredTrades.map((t) => {
                      const retPct = t.return_pct != null && t.return_pct !== 0
                        ? t.return_pct
                        : (t.entry_price && t.quantity ? (t.net_pnl / (t.entry_price * t.quantity)) * 100 : 0);

                      return (
                        <TableRow key={t.trade_id} hover>
                          <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{t.trade_id}</Typography></TableCell>
                          <TableCell><StatusChip status={t.side} /></TableCell>
                          <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{formatCleanDate(t.entry_time)}</Typography></TableCell>
                          <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{formatCleanDate(t.exit_time)}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${t.entry_price?.toLocaleString()}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${t.exit_price?.toLocaleString()}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{t.quantity}</Typography></TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" sx={{ color: t.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                              {t.net_pnl >= 0 ? '+' : ''}${t.net_pnl?.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" sx={{ color: retPct >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                              {retPct >= 0 ? '+' : ''}{retPct.toFixed(2)}%
                            </Typography>
                          </TableCell>
                          <TableCell><StatusChip status={t.status || 'Completed'} /></TableCell>
                        </TableRow>
                      );
                    })}
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
