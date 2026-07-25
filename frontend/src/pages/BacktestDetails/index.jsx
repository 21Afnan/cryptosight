import React, { useState } from 'react';
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
import TableSortLabel from '@mui/material/TableSortLabel';
import Button from '@mui/material/Button';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
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
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import ShieldRoundedIcon from '@mui/icons-material/ShieldRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import LocalAtmRoundedIcon from '@mui/icons-material/LocalAtmRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import SpeedRoundedIcon from '@mui/icons-material/SpeedRounded';

function HeroKpiCard({ icon, label, value, subtext, color, glowColor }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const activeColor = color || '#0ECB81';
  const activeGlow = glowColor || activeColor;

  const cardBg = isDark ? COLORS.darkSurface : '#ffffff';

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

export default function BacktestDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const [snack, setSnack] = useState(null);
  const [chartTab, setChartTab] = useState(0);
  const [ledgerFilters, setLedgerFilters] = useState({ startDate: '', endDate: '', side: 'all', symbol: '' });
  const [sortConfig, setSortConfig] = useState({ key: 'entry_time', direction: 'desc' });

  const { data: bt, loading, error } = useMockFetch(() => getBacktestById(id), [id]);

  const rawTrades = bt?.trades ?? [];
  const filteredTrades = filterLedgerRows(rawTrades, ledgerFilters);

  const handleSort = (columnKey) => {
    setSortConfig((prev) => ({
      key: columnKey,
      direction: prev.key === columnKey && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const sortedTrades = React.useMemo(() => {
    const items = [...filteredTrades];
    if (!sortConfig.key) return items;

    return items.sort((a, b) => {
      let valA = a[sortConfig.key];
      let valB = b[sortConfig.key];

      if (sortConfig.key === 'entry_time' || sortConfig.key === 'exit_time') {
        valA = new Date(valA || 0).getTime();
        valB = new Date(valB || 0).getTime();
      } else if (typeof valA === 'string') {
        valA = (valA || '').toLowerCase();
        valB = (valB || '').toLowerCase();
      } else {
        valA = Number(valA || 0);
        valB = Number(valB || 0);
      }

      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredTrades, sortConfig]);

  if (loading) return <PageContainer title="Backtest Details" breadcrumbs="Backtests"><Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box></PageContainer>;
  if (error || !bt) return (
    <PageContainer title="Backtest Details" breadcrumbs="Backtests">
      <EmptyState icon={ErrorOutlineRoundedIcon} title="Backtest not found" description={error || 'The requested backtest does not exist.'} action={<Button onClick={() => navigate('/backtests')}>Back to Backtests</Button>} />
    </PageContainer>
  );

  // Dynamic Value-Based Color Evaluation (Green = Profit/Good, Red = Loss/Bad)
  const pnlColor = (bt.net_pnl ?? 0) >= 0 ? '#0ECB81' : COLORS.pnlRed;
  const cagrColor = (bt.cagr ?? 0) >= 0 ? '#0ECB81' : COLORS.pnlRed;
  const winRateColor = (bt.win_rate ?? 0) >= 0.5 ? '#0ECB81' : COLORS.pnlRed;
  const tradesColor = (bt.avg_trade_pnl ?? 0) >= 0 ? '#0ECB81' : COLORS.pnlRed;
  const sharpeColor = (bt.sharpe ?? 0) >= 1.0 ? '#0ECB81' : COLORS.pnlRed;
  const sortinoColor = (bt.sortino ?? 0) >= 1.0 ? '#0ECB81' : COLORS.pnlRed;
  const calmarColor = (bt.calmar ?? 0) >= 1.0 ? '#0ECB81' : COLORS.pnlRed;
  const ddColor = COLORS.pnlRed; // Drawdown is always loss/decline

  const cardLightShadow = '0 6px 22px rgba(14, 203, 129, 0.25)';
  const cardLightBorder = '1.5px solid #0ECB81';

  return (
    <PageContainer title={bt.strategy_name} breadcrumbs="Backtests">
      <Box sx={{ pt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>

        {/* Navigation & Header Bar */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/backtests')} variant="outlined" size="small" sx={{ borderRadius: 2 }}>
              Back
            </Button>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h5" sx={{ fontWeight: 800 }}>
                  {bt.strategy_name}
                </Typography>
                <Chip label={bt.symbol} size="small" color="primary" sx={{ fontWeight: 700 }} />
                <Chip label={bt.exchange} size="small" variant="outlined" sx={{ fontWeight: 600 }} />
              </Box>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Completed on {bt.completed_at ? new Date(bt.completed_at).toLocaleString() : 'Recent'}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Button
              id="export-report-btn"
              startIcon={<DownloadRoundedIcon />}
              variant="contained"
              size="small"
              onClick={() => setSnack({ severity: 'info', message: 'Report export queued — PDF generation ready.' })}
              sx={{ fontWeight: 700, height: 32 }}
            >
              Export Report
            </Button>
          </Box>
        </Box>

        {/* Guaranteed 100% Equal Width & Height Cards Grid (CSS Grid repeat(4, 1fr)) */}
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
            value={bt.net_pnl != null ? `${bt.net_pnl >= 0 ? '+' : ''}$${bt.net_pnl?.toFixed(2)}` : '—'}
            subtext={bt.final_balance ? `Ending Balance: $${bt.final_balance.toLocaleString()}` : 'Total dollar gain'}
            color={pnlColor}
            glowColor={pnlColor}
          />
          <HeroKpiCard
            icon={<TrendingUpRoundedIcon />}
            label="CAGR"
            value={bt.cagr != null ? `${(bt.cagr * 100).toFixed(1)}%` : '—'}
            subtext="Annualized Compound Growth"
            color={cagrColor}
            glowColor={cagrColor}
          />
          <HeroKpiCard
            icon={<SpeedRoundedIcon />}
            label="Win Rate"
            value={bt.win_rate != null ? `${(bt.win_rate * 100).toFixed(1)}%` : '—'}
            subtext={`Profit Factor: ${bt.profit_factor?.toFixed(2) ?? '—'}`}
            color={winRateColor}
            glowColor={winRateColor}
          />
          <HeroKpiCard
            icon={<BarChartRoundedIcon />}
            label="Total Trades"
            value={bt.total_trades ?? '—'}
            subtext={bt.avg_trade_pnl != null ? `Avg Trade: $${bt.avg_trade_pnl?.toFixed(2)}` : 'Executed trades'}
            color={tradesColor}
            glowColor={tradesColor}
          />
          <HeroKpiCard
            icon={<ShowChartRoundedIcon />}
            label="Sharpe Ratio"
            value={bt.sharpe?.toFixed(2) ?? '—'}
            subtext="Excess Risk-Adjusted Return"
            color={sharpeColor}
            glowColor={sharpeColor}
          />
          <HeroKpiCard
            icon={<ShowChartRoundedIcon />}
            label="Sortino Ratio"
            value={bt.sortino?.toFixed(2) ?? '—'}
            subtext="Downside Risk Adjusted"
            color={sortinoColor}
            glowColor={sortinoColor}
          />
          <HeroKpiCard
            icon={<ShowChartRoundedIcon />}
            label="Calmar Ratio"
            value={bt.calmar?.toFixed(2) ?? '—'}
            subtext="CAGR / Max Drawdown Ratio"
            color={calmarColor}
            glowColor={calmarColor}
          />
          <HeroKpiCard
            icon={<ShieldRoundedIcon />}
            label="Max Drawdown"
            value={bt.max_drawdown != null ? `${(bt.max_drawdown * 100).toFixed(1)}%` : '—'}
            subtext="Peak-to-Trough Decline"
            color={ddColor}
            glowColor={ddColor}
          />
        </Box>

        {/* Backtest Configuration Parameters Card (Permanent Green Border + Glowing Shadow) */}
        <Card
          sx={{
            background: isDark ? COLORS.darkSurface : '#ffffff',
            boxShadow: isDark ? '0 4px 20px rgba(34, 197, 94, 0.15)' : '0 8px 26px rgba(14, 203, 129, 0.24)',
            border: 'none',
            borderRadius: 2.5,
          }}
        >
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
              Strategy Configuration
            </Typography>

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(5, 1fr)' },
                gap: 1.5,
                width: '100%',
              }}
            >
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
                <Box
                  key={label}
                  sx={{
                    p: '12px 16px',
                    width: '100%',
                    height: '64px',
                    boxSizing: 'border-box',
                    borderRadius: '12px',
                    background: isDark ? 'rgba(38, 46, 37, 0.7)' : '#ffffff',
                    border: 'none',
                    boxShadow: isDark ? '0 4px 14px rgba(0, 0, 0, 0.3)' : '0 6px 18px rgba(14, 203, 129, 0.20)',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      boxShadow: '0 10px 24px rgba(14, 203, 129, 0.35)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, display: 'block', textTransform: 'uppercase', letterSpacing: 0.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', mt: 0.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value ?? '—'}</Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Full Width Performance Charts Canvas */}
        <Card
          sx={{
            background: isDark ? COLORS.darkSurface : '#ffffff',
            boxShadow: isDark ? '0 4px 24px rgba(0,0,0,0.5)' : cardLightShadow,
            border: isDark ? '1px solid rgba(34, 197, 94, 0.25)' : cardLightBorder,
            borderRadius: 2.5,
          }}
        >
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2.5, flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Performance Charts & Oscillators
              </Typography>
              <Tabs value={chartTab} onChange={(_, v) => { setChartTab(v); setTimeout(() => window.dispatchEvent(new Event('resize')), 50); }} sx={{ minHeight: '36px' }}>
                <Tab label="Equity Curve & Drawdown" sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
                <Tab label="Monthly Returns" sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
                <Tab label="Rolling Metrics" sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
              </Tabs>
            </Box>

            {chartTab === 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%' }}>
                <Box sx={{ width: '100%', minWidth: 0 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                    Equity Curve Trajectory
                  </Typography>
                  <Box sx={{ height: 320, width: '100%', minWidth: 0, position: 'relative' }}>
                    <EquityCurveChart data={bt.equity_curve ?? []} height={320} />
                  </Box>
                </Box>

                <Box sx={{ width: '100%', minWidth: 0 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                    Underwater Drawdown
                  </Typography>
                  <Box sx={{ height: 260, width: '100%', minWidth: 0, position: 'relative' }}>
                    <DrawdownChart data={bt.drawdown_curve ?? []} height={260} />
                  </Box>
                </Box>
              </Box>
            )}

            {chartTab === 1 && (
              <Box sx={{ width: '100%', height: 360 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Monthly Returns Breakdown
                </Typography>
                <MonthlyReturnsChart data={bt.monthly_returns ?? []} height={340} />
              </Box>
            )}

            {chartTab === 2 && (
              <Box sx={{ width: '100%', height: 360 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Rolling Ratios (Sharpe · Sortino · Calmar)
                </Typography>
                <RollingMetricsChart data={bt.rolling_metrics ?? []} height={340} />
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Trade Ledger Table Card */}
        <Card
          sx={{
            background: isDark ? COLORS.darkSurface : '#ffffff',
            boxShadow: isDark ? '0 4px 24px rgba(0,0,0,0.5)' : cardLightShadow,
            border: isDark ? '1px solid rgba(34, 197, 94, 0.25)' : cardLightBorder,
            borderRadius: 2.5,
          }}
        >
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Trade Execution Ledger ({filteredTrades.length} displayed)
              </Typography>
              <Chip label="Order Log" size="small" variant="outlined" />
            </Box>

            <LedgerFilterBar onChange={setLedgerFilters} />

            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>
                      <TableSortLabel
                        active={sortConfig.key === 'entry_time'}
                        direction={sortConfig.key === 'entry_time' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('entry_time')}
                      >
                        Entry Time
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortConfig.key === 'exit_time'}
                        direction={sortConfig.key === 'exit_time' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('exit_time')}
                      >
                        Exit Time
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortConfig.key === 'side'}
                        direction={sortConfig.key === 'side' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('side')}
                      >
                        Side
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortConfig.key === 'exit_reason'}
                        direction={sortConfig.key === 'exit_reason' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('exit_reason')}
                      >
                        Exit Reason
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortConfig.key === 'status'}
                        direction={sortConfig.key === 'status' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('status')}
                      >
                        Status
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="right">
                      <TableSortLabel
                        active={sortConfig.key === 'entry_price'}
                        direction={sortConfig.key === 'entry_price' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('entry_price')}
                      >
                        Entry Price
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="right">
                      <TableSortLabel
                        active={sortConfig.key === 'exit_price'}
                        direction={sortConfig.key === 'exit_price' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('exit_price')}
                      >
                        Exit Price
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="right">
                      <TableSortLabel
                        active={sortConfig.key === 'net_pnl'}
                        direction={sortConfig.key === 'net_pnl' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('net_pnl')}
                      >
                        Net PnL
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="right">
                      <TableSortLabel
                        active={sortConfig.key === 'return_pct'}
                        direction={sortConfig.key === 'return_pct' ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort('return_pct')}
                      >
                        Return %
                      </TableSortLabel>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sortedTrades.slice(0, 200).map((trade, idx) => (
                    <TableRow key={trade.trade_id || idx} hover>
                      <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{trade.entry_time ? new Date(trade.entry_time).toLocaleString() : '—'}</Typography></TableCell>
                      <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{trade.exit_time ? new Date(trade.exit_time).toLocaleString() : '—'}</Typography></TableCell>
                      <TableCell><StatusChip status={trade.side} /></TableCell>
                      <TableCell>
                        <Chip
                          label={trade.exit_reason ? String(trade.exit_reason).replace(/_/g, ' ').toUpperCase() : 'TAKE PROFIT'}
                          size="small"
                          variant="outlined"
                          sx={{ height: 22, fontSize: 11, fontWeight: 700 }}
                        />
                      </TableCell>
                      <TableCell><StatusChip status={trade.status || 'Completed'} /></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${trade.entry_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', color: trade.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700 }}>${trade.exit_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ color: trade.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{trade.net_pnl >= 0 ? '+' : ''}${trade.net_pnl?.toFixed(2)}</Typography></TableCell>
                      <TableCell align="right"><Typography variant="body2" sx={{ color: trade.return_pct >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{trade.return_pct >= 0 ? '+' : ''}{trade.return_pct?.toFixed(2)}%</Typography></TableCell>
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
