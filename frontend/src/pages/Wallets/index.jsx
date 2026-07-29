import React, { useState, useMemo } from 'react';
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
import TablePagination from '@mui/material/TablePagination';
import TableSortLabel from '@mui/material/TableSortLabel';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Drawer from '@mui/material/Drawer';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Snackbar from '@mui/material/Snackbar';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatCard from '../../components/ui/StatCard';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import SearchBar from '../../components/ui/SearchBar';
import EquityCurveChart from '../../components/charts/EquityCurveChart';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getWallets, deleteWallet, toggleWalletStatus, addWallet } from '../../api/walletsApi';
import { toggleStrategyExecution } from '../../api/strategiesApi';
import { COLORS } from '../../theme/theme';

import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import PowerSettingsNewRoundedIcon from '@mui/icons-material/PowerSettingsNewRounded';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import SwapHorizRoundedIcon from '@mui/icons-material/SwapHorizRounded';
import ReceiptLongRoundedIcon from '@mui/icons-material/ReceiptLongRounded';
import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';

function SectionLabel({ children }) {
  const theme = useTheme();
  return (
    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mb: 1.5, mt: 2, fontWeight: 700, letterSpacing: '0.04em' }}>
      {children}
    </Typography>
  );
}

function WalletDetailRow({ icon: IconComponent, title, badge, subtitle, rightValue, rightColor, status }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        p: 1.25,
        px: 1.5,
        mb: 1,
        borderRadius: '12px',
        background: isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)',
        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
        transition: 'all 200ms ease',
        '&:hover': {
          background: isDark ? 'rgba(94, 139, 110, 0.12)' : 'rgba(94, 139, 110, 0.08)',
          transform: 'translateY(-1px)',
          boxShadow: '0 4px 12px rgba(15, 40, 25, 0.06)',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
        {IconComponent && (
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: `${COLORS.accent}15`,
              color: COLORS.accent,
              flexShrink: 0,
            }}
          >
            <IconComponent sx={{ fontSize: 18 }} />
          </Box>
        )}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {title}
            </Typography>
            {badge && (
              <Chip
                label={badge}
                size="small"
                sx={{ height: 18, fontSize: 10, color: COLORS.accent, background: `${COLORS.accent}15`, fontWeight: 600 }}
              />
            )}
            {status && <StatusChip status={status} />}
          </Box>
          {subtitle && (
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mt: 0.25 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>

      {rightValue && (
        <Typography
          variant="body2"
          sx={{
            fontWeight: 700,
            fontVariantNumeric: 'tabular-nums',
            color: rightColor || theme.palette.text.primary,
          }}
        >
          {rightValue}
        </Typography>
      )}
    </Box>
  );
}

// ─── Add Wallet Modal Form ───────────────────────────────────────────────────
function AddWalletDialog({ open, onClose, onSuccess }) {
  const [exchange, setExchange] = useState('Bybit');
  const [accountType, setAccountType] = useState('Unified Margin');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const maskedKey = apiKey ? `****...${apiKey.slice(-4)}` : '****...9c3e';
      await addWallet({
        exchange,
        account_type: accountType,
        api_key: maskedKey,
        status: enabled ? 'connected' : 'disabled',
      });
      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle sx={{ fontWeight: 700 }}>Connect New Exchange Wallet</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
          <TextField
            select
            label="Exchange"
            value={exchange}
            onChange={(e) => setExchange(e.target.value)}
            fullWidth
            size="small"
          >
            {['Bybit', 'Binance'].map((ex) => (
              <MenuItem key={ex} value={ex}>{ex}</MenuItem>
            ))}
          </TextField>

          <TextField
            label="Account Type"
            value={accountType}
            onChange={(e) => setAccountType(e.target.value)}
            placeholder="e.g. Unified Margin / Futures"
            fullWidth
            size="small"
          />

          <TextField
            label="API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Paste your API key"
            fullWidth
            size="small"
            required
          />

          <TextField
            label="API Secret"
            type="password"
            value={apiSecret}
            onChange={(e) => setApiSecret(e.target.value)}
            placeholder="Paste your API secret"
            fullWidth
            size="small"
            required
          />

          <FormControlLabel
            control={<Switch checked={enabled} onChange={(e) => setEnabled(e.target.checked)} color="primary" />}
            label="Enable for trading execution"
          />
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button onClick={onClose} variant="text" color="inherit">Cancel</Button>
          <Button type="submit" variant="contained" disabled={submitting}>
            {submitting ? 'Connecting…' : 'Connect Wallet'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

// ─── Wallet Detail Drawer ─────────────────────────────────────────────────────
function WalletDrawer({ wallet, open, onClose }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  if (!wallet) return null;

  return (
    <Drawer anchor="right" open={open} onClose={onClose} PaperProps={{ sx: { width: 480, p: 0, background: theme.palette.background.paper } }}>
      <Box sx={{ p: 3 }}>
        {/* Header — API status badge present, plain-text API key removed per 2.2 */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{wallet.exchange} — {wallet.account_type}</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StatusChip status={wallet.status} />
            <IconButton size="small" onClick={onClose}><CloseRoundedIcon /></IconButton>
          </Box>
        </Box>

        {/* Balance row */}
        <Card sx={{ mb: 2 }}>
          <CardContent sx={{ p: '16px !important', display: 'flex', gap: 3 }}>
            {[
              { label: 'Balance', value: `$${wallet.balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}` },
              { label: 'Unrealized PnL', value: `${wallet.unrealized_pnl >= 0 ? '+' : ''}$${wallet.unrealized_pnl?.toFixed(2)}`, color: wallet.unrealized_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
              { label: 'Total PnL', value: `${wallet.total_pnl >= 0 ? '+' : ''}$${wallet.total_pnl?.toFixed(2)}`, color: wallet.total_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
            ].map(({ label, value, color }) => (
              <Box key={label}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>{label}</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: color || theme.palette.text.primary }}>{value}</Typography>
              </Box>
            ))}
          </CardContent>
        </Card>

        {wallet.error_message && (
          <Alert severity="error" sx={{ mb: 2, fontSize: 12 }}>{wallet.error_message}</Alert>
        )}

        {/* 1. Assigned Strategies */}
        <SectionLabel>Assigned Strategies ({wallet.assigned_strategies?.length ?? 0})</SectionLabel>
        {wallet.assigned_strategies?.length === 0 ? (
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>No assigned strategies</Typography>
        ) : (
          wallet.assigned_strategies?.map((s) => (
            <WalletDetailRow
              key={s.strategy_id}
              icon={ShowChartRoundedIcon}
              title={s.strategy_name}
              badge={s.symbol}
            />
          ))
        )}

        <Divider sx={{ my: 2 }} />

        {/* 2. Active Positions */}
        <SectionLabel>Active Positions ({wallet.active_positions?.length ?? 0})</SectionLabel>
        {wallet.active_positions?.length === 0 ? (
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>No active positions</Typography>
        ) : (
          wallet.active_positions?.map((p) => {
            const tpVal = p.tp ?? p.take_profit;
            const slVal = p.sl ?? p.stop_loss;
            const tpStr = tpVal != null ? `$${tpVal}` : '—';
            const slStr = slVal != null ? `$${slVal}` : '—';
            return (
              <WalletDetailRow
                key={p.position_id || p.order_id || p.symbol}
                icon={SwapHorizRoundedIcon}
                title={p.symbol}
                status={p.side}
                subtitle={`Entry: $${p.entry_price != null ? p.entry_price : '—'} · TP: ${tpStr} · SL: ${slStr}`}
                rightValue={`${p.unrealized_pnl >= 0 ? '+' : ''}$${p.unrealized_pnl?.toFixed(2)}`}
                rightColor={p.unrealized_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed}
              />
            );
          })
        )}

        <Divider sx={{ my: 2 }} />

        {/* 3. Open Orders */}
        <SectionLabel>Open Orders ({wallet.open_orders?.length ?? 0})</SectionLabel>
        {wallet.open_orders?.length === 0 ? (
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>No open orders</Typography>
        ) : (
          wallet.open_orders?.map((o) => (
            <WalletDetailRow
              key={o.order_id}
              icon={ReceiptLongRoundedIcon}
              title={`${o.symbol} — ${o.type?.toUpperCase()} ${o.side?.toUpperCase()}`}
              status={o.status}
              subtitle={`Qty: ${o.quantity} · Price: $${o.price?.toLocaleString()}`}
            />
          ))
        )}

        <Divider sx={{ my: 2 }} />

        {/* 4. Running Executions */}
        <SectionLabel>Running Executions ({wallet.running_executions?.length ?? 0})</SectionLabel>
        {wallet.running_executions?.length === 0 ? (
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>No running executions</Typography>
        ) : (
          wallet.running_executions?.map((e) => (
            <WalletDetailRow
              key={e.execution_id}
              icon={RocketLaunchRoundedIcon}
              title={e.strategy_name}
              subtitle={`Started: ${new Date(e.started_at).toLocaleDateString()}`}
              rightValue={`${e.current_pnl >= 0 ? '+' : ''}$${e.current_pnl?.toFixed(2)}`}
              rightColor={e.current_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed}
            />
          ))
        )}
      </Box>
    </Drawer>
  );
}

// ─── Main Wallets Page ────────────────────────────────────────────────────────
export default function Wallets() {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [detailTab, setDetailTab] = useState(0);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [confirmToggle, setConfirmToggle] = useState(null);
  const [snack, setSnack] = useState(null);
  const detailsRef = React.useRef(null);

  const { data, loading, error, refetch } = useMockFetch(
    () => getWallets({ search }),
    [search],
  );

  const wallets = data?.data ?? [];

  React.useEffect(() => {
    if (wallets.length > 0 && !selectedWallet) {
      setSelectedWallet(wallets[0]);
    }
  }, [wallets, selectedWallet]);

  // Symbol performance breakdown filter and sort states
  const [symbolSearch, setSymbolSearch] = useState('');
  const [symbolPnlFilter, setSymbolPnlFilter] = useState('all');
  const [symbolSortField, setSymbolSortField] = useState('net_pnl');
  const [symbolSortOrder, setSymbolSortOrder] = useState('desc');

  const handleSymbolSort = (field) => {
    if (symbolSortField === field) {
      setSymbolSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSymbolSortField(field);
      setSymbolSortOrder('desc');
    }
  };

  const filteredAndSortedSymbols = useMemo(() => {
    if (!wallets || wallets.length === 0 || !wallets[0]?.account_stats?.per_symbol) {
      return [];
    }

    let list = Object.entries(wallets[0].account_stats.per_symbol).map(([sym, meta]) => ({
      symbol: sym,
      total_trades: meta.total_trades ?? 0,
      win_rate: meta.win_rate ?? 0,
      net_pnl: meta.net_pnl ?? 0,
    }));

    if (symbolSearch.trim() !== '') {
      const q = symbolSearch.toLowerCase();
      list = list.filter(item => item.symbol.toLowerCase().includes(q));
    }

    if (symbolPnlFilter === 'profitable') {
      list = list.filter(item => item.net_pnl > 0);
    } else if (symbolPnlFilter === 'loss') {
      list = list.filter(item => item.net_pnl < 0);
    }

    if (symbolSortField) {
      list.sort((a, b) => {
        let valA = a[symbolSortField];
        let valB = b[symbolSortField];

        if (typeof valA === 'string') {
          valA = valA.toLowerCase();
          valB = valB.toLowerCase();
        }

        if (valA < valB) return symbolSortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return symbolSortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return list;
  }, [wallets, symbolSearch, symbolPnlFilter, symbolSortField, symbolSortOrder]);

  // Summary StatCards calculations (Requirement 2.3)
  const summary = useMemo(() => {
    const totalBalance = wallets.reduce((acc, w) => acc + (w.balance || 0), 0);
    const activeCount = wallets.filter((w) => w.status === 'connected').length;
    const totalUnrealizedPnL = wallets.reduce((acc, w) => acc + (w.unrealized_pnl || 0), 0);
    const totalPnL = wallets.reduce((acc, w) => acc + (w.total_pnl || 0), 0);
    return { totalBalance, activeCount, totalUnrealizedPnL, totalPnL };
  }, [wallets]);

  // Combined account equity curve from API data
  const equityCurveData = useMemo(() => {
    if (wallets.length > 0 && Array.isArray(wallets[0].equity_curve) && wallets[0].equity_curve.length > 0) {
      return wallets[0].equity_curve;
    }
    const currentBal = summary.totalBalance > 0 ? summary.totalBalance : 165865.91;
    return [
      { time: '2026-07-01', value: 150000.00 },
      { time: '2026-07-08', value: 154200.50 },
      { time: '2026-07-15', value: 159800.20 },
      { time: '2026-07-22', value: 162400.00 },
    ];
  }, [wallets, summary.totalBalance]);

  const handleSelectWallet = (w) => {
    setSelectedWallet(w);
    setTimeout(() => {
      const el = detailsRef.current;
      if (el) {
        const yOffset = -90; // offset to keep top header clean
        const y = el.getBoundingClientRect().top + window.pageYOffset + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    }, 150);
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    await deleteWallet(confirmDelete.id);
    if (selectedWallet?.id === confirmDelete.id) {
      setSelectedWallet(null);
    }
    setConfirmDelete(null);
    setSnack('Wallet removed successfully.');
    refetch();
  };

  const handleToggle = async () => {
    if (!confirmToggle) return;
    await toggleWalletStatus(confirmToggle.id);
    setConfirmToggle(null);
    setSnack('Wallet status updated.');
    refetch();
  };

  const handleToggleExecution = async (strategyId, enabled) => {
    // 1. Find the symbol of the toggled strategy
    const toggledStrat = selectedWallet?.assigned_strategies?.find(s => (s.strategy_id === strategyId || s.id === strategyId));
    const symbol = toggledStrat?.symbol;

    if (enabled && symbol) {
      // 2. Check if another strategy for the same symbol is already active
      const anotherActive = selectedWallet?.assigned_strategies?.some(s =>
        (s.strategy_id !== strategyId && s.id !== strategyId) && s.symbol === symbol && s.execution_enabled
      );
      if (anotherActive) {
        setSnack("You can activate just 1 strategy for this symbol, another is already activated.");
        return;
      }
    }

    try {
      const res = await toggleStrategyExecution(strategyId, enabled);
      if (res && res.success) {
        setSnack(enabled ? 'Strategy activated successfully!' : 'Strategy deactivated successfully!');

        // Update selectedWallet's assigned_strategies state locally to reflect the change instantly
        setSelectedWallet(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            assigned_strategies: prev.assigned_strategies.map(s => {
              if (s.strategy_id === strategyId || s.id === strategyId) {
                return { ...s, execution_enabled: enabled };
              }
              return s;
            })
          };
        });

        // Refetch backend wallets list
        refetch();
      } else {
        setSnack('Failed to toggle strategy execution.');
      }
    } catch (err) {
      console.error(err);
      setSnack('Error toggling strategy execution.');
    }
  };

  return (
    <PageContainer title="Wallet Management">
      <Box sx={{ pt: 2 }}>
        <Box sx={{ display: 'flex', gap: 2.5, width: '100%', mb: 3.5, flexDirection: { xs: 'column', sm: 'row' } }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="Total Balance"
              value={`$${summary.totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
              delta={`across ${wallets.length} wallets`}
              deltaType="neutral"
              icon={<AccountBalanceWalletRoundedIcon />}
              colorIndex={0}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="Connected Wallets"
              value={`${summary.activeCount} / ${wallets.length}`}
              delta="Active API sessions"
              deltaType="positive"
              icon={<CheckCircleRoundedIcon />}
              colorIndex={1}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="Unrealized PnL"
              value={`${summary.totalUnrealizedPnL >= 0 ? '+' : ''}$${summary.totalUnrealizedPnL.toFixed(2)}`}
              delta="Open positions"
              deltaType={summary.totalUnrealizedPnL >= 0 ? 'positive' : 'negative'}
              icon={<AccountBalanceWalletRoundedIcon />}
              colorIndex={2}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="Total Realized PnL"
              value={`${summary.totalPnL >= 0 ? '+' : ''}$${summary.totalPnL.toFixed(2)}`}
              delta="Cumulative net profit"
              deltaType={summary.totalPnL >= 0 ? 'positive' : 'negative'}
              icon={<AccountBalanceWalletRoundedIcon />}
              colorIndex={3}
            />
          </Box>
        </Box>

        {/* Toolbar */}
        {/* Full-width 100% Combined Account Equity Curve */}
        {!loading && (
          <Box sx={{ width: '100%', mb: 3 }}>
            <Card sx={{ width: '100%' }}>
              <CardContent sx={{ p: '20px !important' }}>
                <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 700 }}>Combined Account Equity Curve</Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>Cumulative portfolio balance across all wallets</Typography>
                <Box sx={{ height: 260, width: '100%' }}>
                  <EquityCurveChart data={equityCurveData} height={260} label="Total Balance" />
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Account Performance & Symbol Breakdown Card */}
        {!loading && wallets.length > 0 && wallets[0]?.account_stats && (
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: '20px !important' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>Account Performance & Symbol Analytics</Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>Realized performance metrics & trade distribution across active markets</Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                  <Chip
                    icon={<CheckCircleRoundedIcon sx={{ fontSize: 16 }} />}
                    label={`Win Rate: ${wallets[0].account_stats.win_rate}%`}
                    color="success"
                    variant="outlined"
                    sx={{ fontWeight: 700, borderRadius: '8px' }}
                  />
                  <Chip
                    label={`Profit Factor: ${wallets[0].account_stats.profit_factor}`}
                    variant="outlined"
                    sx={{ fontWeight: 700, borderRadius: '8px', color: COLORS.accent, borderColor: COLORS.accent }}
                  />
                  <Chip
                    label={`Top Traded: ${wallets[0].account_stats.top_traded_symbol}`}
                    variant="outlined"
                    sx={{ fontWeight: 700, borderRadius: '8px' }}
                  />
                  <Chip
                    label={`Traded Symbols: ${wallets[0].account_stats.total_symbols_traded}`}
                    variant="outlined"
                    sx={{ fontWeight: 700, borderRadius: '8px' }}
                  />
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Per-Symbol Performance Breakdown</Typography>
                <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
                  <TextField
                    size="small"
                    placeholder="Search symbol..."
                    value={symbolSearch}
                    onChange={(e) => setSymbolSearch(e.target.value)}
                    sx={{
                      width: 160,
                      '& .MuiInputBase-input': { py: 0.75, fontSize: '0.8125rem' }
                    }}
                  />
                  <TextField
                    select
                    size="small"
                    value={symbolPnlFilter}
                    onChange={(e) => setSymbolPnlFilter(e.target.value)}
                    sx={{
                      minWidth: 140,
                      '& .MuiInputBase-input': { py: 0.75, fontSize: '0.8125rem' }
                    }}
                  >
                    <MenuItem value="all" sx={{ fontSize: '0.8125rem' }}>All Symbols</MenuItem>
                    <MenuItem value="profitable" sx={{ fontSize: '0.8125rem' }}>Profitable Only</MenuItem>
                    <MenuItem value="loss" sx={{ fontSize: '0.8125rem' }}>Loss-making Only</MenuItem>
                  </TextField>
                </Box>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>
                        <TableSortLabel
                          active={symbolSortField === 'symbol'}
                          direction={symbolSortField === 'symbol' ? symbolSortOrder : 'asc'}
                          onClick={() => handleSymbolSort('symbol')}
                        >
                          Symbol
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>
                        <TableSortLabel
                          active={symbolSortField === 'total_trades'}
                          direction={symbolSortField === 'total_trades' ? symbolSortOrder : 'desc'}
                          onClick={() => handleSymbolSort('total_trades')}
                        >
                          Total Trades
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>
                        <TableSortLabel
                          active={symbolSortField === 'win_rate'}
                          direction={symbolSortField === 'win_rate' ? symbolSortOrder : 'desc'}
                          onClick={() => handleSymbolSort('win_rate')}
                        >
                          Win Rate
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>
                        <TableSortLabel
                          active={symbolSortField === 'net_pnl'}
                          direction={symbolSortField === 'net_pnl' ? symbolSortOrder : 'desc'}
                          onClick={() => handleSymbolSort('net_pnl')}
                        >
                          Net PnL
                        </TableSortLabel>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredAndSortedSymbols.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                          <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                            No matching symbols found.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredAndSortedSymbols.map((item) => {
                        const netPnl = item.net_pnl;
                        return (
                          <TableRow key={item.symbol} hover>
                            <TableCell><Typography variant="body2" sx={{ fontWeight: 700 }}>{item.symbol}</Typography></TableCell>
                            <TableCell align="right"><Typography variant="body2">{item.total_trades}</Typography></TableCell>
                            <TableCell align="right"><Typography variant="body2" sx={{ fontWeight: 700, color: item.win_rate >= 50 ? COLORS.pnlGreen : COLORS.pnlRed }}>{item.win_rate.toFixed(1)}%</Typography></TableCell>
                            <TableCell align="right"><Typography variant="body2" sx={{ fontWeight: 700, color: netPnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed }}>{netPnl >= 0 ? '+' : ''}${netPnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <SearchBar onSearch={setSearch} placeholder="Search wallets…" />
          <Button
            id="add-wallet-btn"
            variant="contained"
            startIcon={<AddRoundedIcon />}
            onClick={() => setAddDialogOpen(true)}
          >
            Add Wallet
          </Button>
        </Box>

        {error && <EmptyState icon={ErrorOutlineRoundedIcon} title="Failed to load wallets" description={error} />}
        {loading ? <LoadingSkeleton variant="table" /> : wallets.length === 0 ? (
          <EmptyState icon={AccountBalanceWalletRoundedIcon} title="No wallets found" description="No wallets match your search." />
        ) : (
          <Card>
            <CardContent sx={{ p: '20px !important' }}>
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Exchange</TableCell>
                      <TableCell>Account Type</TableCell>
                      <TableCell>API Key</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Balance</TableCell>
                      <TableCell align="right">Unrealized PnL</TableCell>
                      <TableCell align="right">Total PnL</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {wallets.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((w) => (
                      <TableRow
                        key={w.id}
                        hover
                        onClick={() => handleSelectWallet(w)}
                        selected={selectedWallet?.id === w.id}
                        sx={{
                          cursor: 'pointer',
                          '&.Mui-selected': {
                            backgroundColor: isDark ? 'rgba(94, 139, 110, 0.15) !important' : 'rgba(94, 139, 110, 0.08) !important',
                          }
                        }}
                      >
                        <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{w.exchange}</Typography></TableCell>
                        <TableCell>{w.account_type}</TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontSize: 12, color: theme.palette.text.secondary }}>
                            {w.api_key}
                          </Typography>
                        </TableCell>
                        <TableCell><StatusChip status={w.status} /></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>${w.balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: w.unrealized_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{w.unrealized_pnl >= 0 ? '+' : ''}${w.unrealized_pnl?.toFixed(2)}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: w.total_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{w.total_pnl >= 0 ? '+' : ''}${w.total_pnl?.toFixed(2)}</Typography></TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
                            <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleSelectWallet(w); }} aria-label="View wallet details"><ChevronRightRoundedIcon sx={{ fontSize: 18 }} /></IconButton>
                            <IconButton size="small" onClick={(e) => { e.stopPropagation(); setConfirmToggle(w); }} aria-label="Toggle wallet status"><PowerSettingsNewRoundedIcon sx={{ fontSize: 18 }} /></IconButton>
                            <IconButton size="small" onClick={(e) => { e.stopPropagation(); setConfirmDelete(w); }} aria-label="Delete wallet" sx={{ color: COLORS.pnlRed }}><DeleteRoundedIcon sx={{ fontSize: 18 }} /></IconButton>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={wallets.length}
                page={page}
                onPageChange={(_, p) => setPage(p)}
                rowsPerPage={rowsPerPage}
                onRowsPerPageChange={(e) => { setRowsPerPage(+e.target.value); setPage(0); }}
                rowsPerPageOptions={[5, 10, 25]}
              />
            </CardContent>
          </Card>
        )}

        {/* Render Live Wallet Ledgers directly inline on the main layout page */}
        {selectedWallet && (
          <Card ref={detailsRef} sx={{ mt: 3.5 }}>
            <CardContent sx={{ p: '20px !important' }}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Live Wallet Ledgers: {selectedWallet.exchange}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  Active positions, pending orders, execution logs & assigned strategies
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Tabs
                value={detailTab}
                onChange={(_, v) => setDetailTab(v)}
                sx={{ mb: 2.5, minHeight: '36px' }}
              >
                <Tab label={`Active Positions (${selectedWallet.active_positions?.length ?? 0})`} sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
                <Tab label={`Open Orders (${selectedWallet.open_orders?.length ?? 0})`} sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
                <Tab label={`Assigned Strategies (${selectedWallet.assigned_strategies?.filter(s => s.execution_enabled).length ?? 0})`} sx={{ minHeight: '36px', py: 0, fontWeight: 600 }} />
              </Tabs>

              {detailTab === 0 && (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Symbol</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Strategy Name</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Direction</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Quantity</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Entry Price</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Liq. Price</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Unrealized PnL</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(!selectedWallet.active_positions || selectedWallet.active_positions.length === 0) ? (
                        <TableRow>
                          <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                            <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                              No active positions found for this wallet.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ) : (
                        selectedWallet.active_positions.map((p, index) => {
                          const netPnl = p.unrealized_pnl ?? 0;
                          const isLong = String(p.direction || p.side || 'LONG').toUpperCase() === 'LONG';
                          return (
                            <TableRow key={p.id || index} hover>
                              <TableCell><Typography variant="body2" sx={{ fontWeight: 700 }}>{p.symbol}</Typography></TableCell>
                              <TableCell>
                                <Typography variant="body2" sx={{ fontWeight: 500, color: COLORS.accent }}>
                                  {p.strategy_name || '—'}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={isLong ? 'Long' : 'Short'}
                                  size="small"
                                  sx={{
                                    height: 18,
                                    fontSize: 10,
                                    fontWeight: 700,
                                    color: isLong ? COLORS.pnlGreen : COLORS.pnlRed,
                                    background: isLong ? `${COLORS.pnlGreen}15` : `${COLORS.pnlRed}15`,
                                  }}
                                />
                              </TableCell>
                              <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{p.quantity}</Typography></TableCell>
                              <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${p.entry_price != null ? Number(p.entry_price).toFixed(2) : '—'}</Typography></TableCell>
                              <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', color: p.liq_price != null ? COLORS.pnlRed : 'inherit' }}>{p.liq_price != null ? `$${Number(p.liq_price).toFixed(2)}` : '—'}</Typography></TableCell>
                              <TableCell align="right">
                                <Typography
                                  variant="body2"
                                  sx={{
                                    fontWeight: 700,
                                    fontVariantNumeric: 'tabular-nums',
                                    color: netPnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed
                                  }}
                                >
                                  {netPnl >= 0 ? '+' : ''}${netPnl.toFixed(2)}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          );
                        })
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {detailTab === 1 && (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Symbol</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Side</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Quantity</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Price</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(!selectedWallet.open_orders || selectedWallet.open_orders.length === 0) ? (
                        <TableRow>
                          <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                            <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                              No open orders found for this wallet.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ) : (
                        selectedWallet.open_orders.map((o, index) => {
                          const isBuy = String(o.side || 'BUY').toUpperCase() === 'BUY';
                          return (
                            <TableRow key={o.order_id || index} hover>
                              <TableCell><Typography variant="body2" sx={{ fontWeight: 700 }}>{o.symbol}</Typography></TableCell>
                              <TableCell><Typography variant="body2" sx={{ textTransform: 'uppercase' }}>{o.type || 'limit'}</Typography></TableCell>
                              <TableCell>
                                <Chip
                                  label={isBuy ? 'Buy' : 'Sell'}
                                  size="small"
                                  sx={{
                                    height: 18,
                                    fontSize: 10,
                                    fontWeight: 700,
                                    color: isBuy ? COLORS.pnlGreen : COLORS.pnlRed,
                                    background: isBuy ? `${COLORS.pnlGreen}15` : `${COLORS.pnlRed}15`,
                                  }}
                                />
                              </TableCell>
                              <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>{o.quantity}</Typography></TableCell>
                              <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>${o.price != null ? Number(o.price).toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—'}</Typography></TableCell>
                              <TableCell><StatusChip status={o.status || 'pending'} /></TableCell>
                            </TableRow>
                          );
                        })
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {detailTab === 2 && (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Strategy Name</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Symbol</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Exchange</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Timeframe</TableCell>
                        <TableCell sx={{ fontWeight: 700 }} align="center">Execution Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(!selectedWallet.assigned_strategies || selectedWallet.assigned_strategies.length === 0) ? (
                        <TableRow>
                          <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                            <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                              No assigned strategies found for this wallet.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ) : (
                        selectedWallet.assigned_strategies.map((s, index) => (
                          <TableRow key={s.strategy_id || s.id || index} hover>
                            <TableCell><Typography variant="body2" sx={{ fontWeight: 700 }}>{s.strategy_name || s.name}</Typography></TableCell>
                            <TableCell>
                              <Chip
                                label={s.symbol}
                                size="small"
                                sx={{ height: 18, fontSize: 10, color: COLORS.accent, background: `${COLORS.accent}15`, fontWeight: 600 }}
                              />
                            </TableCell>
                            <TableCell><Typography variant="body2" sx={{ textTransform: 'capitalize' }}>{s.exchange}</Typography></TableCell>
                            <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{s.timeframe}</Typography></TableCell>
                            <TableCell align="center">
                              <Switch
                                size="small"
                                checked={s.execution_enabled}
                                onChange={(e) => handleToggleExecution(s.strategy_id || s.id, e.target.checked)}
                                sx={{
                                  '& .MuiSwitch-switchBase.Mui-checked': {
                                    color: COLORS.accent,
                                  },
                                  '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                                    backgroundColor: COLORS.accent,
                                  },
                                }}
                              />
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        )}
      </Box>

      {/* Add Wallet Dialog (Requirement 2.1) */}
      <AddWalletDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onSuccess={() => {
          setSnack('Wallet connected successfully!');
          refetch();
        }}
      />

      {/* Confirm dialogs */}
      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        title="Remove Wallet"
        description={`Remove ${confirmDelete?.exchange} ${confirmDelete?.account_type} wallet? This will unassign all strategies and cannot be undone.`}
        confirmLabel="Remove"
        danger
      />
      <ConfirmDialog
        open={!!confirmToggle}
        onClose={() => setConfirmToggle(null)}
        onConfirm={handleToggle}
        title={confirmToggle?.status === 'disabled' ? 'Enable Wallet' : 'Disable Wallet'}
        description={`This will ${confirmToggle?.status === 'disabled' ? 'enable' : 'disable'} the ${confirmToggle?.exchange} wallet and ${confirmToggle?.status === 'disabled' ? 'resume' : 'pause'} all running executions.`}
        confirmLabel={confirmToggle?.status === 'disabled' ? 'Enable' : 'Disable'}
        danger={confirmToggle?.status !== 'disabled'}
      />

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity="success" onClose={() => setSnack(null)}>{snack}</Alert>
      </Snackbar>
    </PageContainer>
  );
}
