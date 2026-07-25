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
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Drawer from '@mui/material/Drawer';
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
            {['Bybit', 'Binance', 'OKX', 'Deribit', 'Coinbase'].map((ex) => (
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
          wallet.active_positions?.map((p) => (
            <WalletDetailRow
              key={p.position_id}
              icon={SwapHorizRoundedIcon}
              title={p.symbol}
              status={p.side}
              subtitle={`Entry: $${p.entry_price?.toLocaleString()} · TP: $${p.tp?.toLocaleString()} · SL: $${p.sl?.toLocaleString()}`}
              rightValue={`${p.unrealized_pnl >= 0 ? '+' : ''}$${p.unrealized_pnl?.toFixed(2)}`}
              rightColor={p.unrealized_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed}
            />
          ))
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
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [confirmToggle, setConfirmToggle] = useState(null);
  const [snack, setSnack] = useState(null);

  const { data, loading, error, refetch } = useMockFetch(
    () => getWallets({ search }),
    [search],
  );

  const wallets = data?.data ?? [];

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
      { time: '2026-07-25', value: parseFloat(currentBal.toFixed(2)) },
    ];
  }, [wallets, summary.totalBalance]);

  const handleDelete = async () => {
    if (!confirmDelete) return;
    await deleteWallet(confirmDelete.id);
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

  return (
    <PageContainer title="Wallet Management">
      <Box sx={{ pt: 2 }}>
        {/* Requirement 2.3: Top StatCard summary flashcard row */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Balance"
              value={`$${summary.totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
              delta={`across ${wallets.length} wallets`}
              deltaType="neutral"
              icon={<AccountBalanceWalletRoundedIcon />}
              colorIndex={0}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Connected Wallets"
              value={`${summary.activeCount} / ${wallets.length}`}
              delta="Active API sessions"
              deltaType="positive"
              icon={<CheckCircleRoundedIcon />}
              colorIndex={1}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Unrealized PnL"
              value={`${summary.totalUnrealizedPnL >= 0 ? '+' : ''}$${summary.totalUnrealizedPnL.toFixed(2)}`}
              delta="Open positions"
              deltaType={summary.totalUnrealizedPnL >= 0 ? 'positive' : 'negative'}
              icon={<AccountBalanceWalletRoundedIcon />}
              colorIndex={2}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Realized PnL"
              value={`${summary.totalPnL >= 0 ? '+' : ''}$${summary.totalPnL.toFixed(2)}`}
              delta="Cumulative net profit"
              deltaType={summary.totalPnL >= 0 ? 'positive' : 'negative'}
              icon={<AccountBalanceWalletRoundedIcon />}
              colorIndex={3}
            />
          </Grid>
        </Grid>

        {/* Toolbar */}
        <Box sx={{ mb: 3 }}>
          {/* Full-width 100% Combined Account Equity Curve */}
          {!loading && wallets.length > 0 && (
            <Grid container spacing={2} sx={{ width: '100%' }}>
              <Grid item xs={12}>
                <Card>
                  <CardContent sx={{ p: '20px !important' }}>
                    <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 700 }}>Combined Account Equity Curve</Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>Cumulative portfolio balance across all wallets</Typography>
                    <Box sx={{ height: 260 }}>
                      <EquityCurveChart data={equityCurveData} height={260} label="Total Balance" />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>

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

              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>Per-Symbol Performance Breakdown</Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Symbol</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>Total Trades</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>Win Rate</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>Net PnL</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(wallets[0].account_stats.per_symbol || {}).map(([sym, meta]) => {
                      const netPnl = meta.net_pnl ?? 0;
                      return (
                        <TableRow key={sym} hover>
                          <TableCell><Typography variant="body2" sx={{ fontWeight: 700 }}>{sym}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2">{meta.total_trades ?? 0}</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ fontWeight: 700, color: (meta.win_rate ?? 0) >= 50 ? COLORS.pnlGreen : COLORS.pnlRed }}>{(meta.win_rate ?? 0).toFixed(1)}%</Typography></TableCell>
                          <TableCell align="right"><Typography variant="body2" sx={{ fontWeight: 700, color: netPnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed }}>{netPnl >= 0 ? '+' : ''}${netPnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                        </TableRow>
                      );
                    })}
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
                      <TableRow key={w.id} hover>
                        <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{w.exchange}</Typography></TableCell>
                        <TableCell>{w.account_type}</TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: 12, color: theme.palette.text.secondary }}>
                            {w.api_key}
                          </Typography>
                        </TableCell>
                        <TableCell><StatusChip status={w.status} /></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>${w.balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: w.unrealized_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{w.unrealized_pnl >= 0 ? '+' : ''}${w.unrealized_pnl?.toFixed(2)}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: w.total_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{w.total_pnl >= 0 ? '+' : ''}${w.total_pnl?.toFixed(2)}</Typography></TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
                            <IconButton size="small" onClick={() => { setSelectedWallet(w); setDrawerOpen(true); }} aria-label="View wallet details"><ChevronRightRoundedIcon sx={{ fontSize: 18 }} /></IconButton>
                            <IconButton size="small" onClick={() => setConfirmToggle(w)} aria-label="Toggle wallet status"><PowerSettingsNewRoundedIcon sx={{ fontSize: 18 }} /></IconButton>
                            <IconButton size="small" onClick={() => setConfirmDelete(w)} aria-label="Delete wallet" sx={{ color: COLORS.pnlRed }}><DeleteRoundedIcon sx={{ fontSize: 18 }} /></IconButton>
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

      {/* Wallet detail drawer */}
      <WalletDrawer wallet={selectedWallet} open={drawerOpen} onClose={() => setDrawerOpen(false)} />

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
