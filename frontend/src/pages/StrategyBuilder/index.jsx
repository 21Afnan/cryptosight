import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Checkbox from '@mui/material/Checkbox';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Stack from '@mui/material/Stack';
import Paper from '@mui/material/Paper';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Tooltip from '@mui/material/Tooltip';
import Divider from '@mui/material/Divider';
import InputAdornment from '@mui/material/InputAdornment';
import { useTheme, alpha } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import { COLORS, GRADIENTS } from '../../theme/theme';

// MUI Icons
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import SaveRoundedIcon from '@mui/icons-material/SaveRounded';
import DragIndicatorRoundedIcon from '@mui/icons-material/DragIndicatorRounded';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import ShieldRoundedIcon from '@mui/icons-material/ShieldRounded';
import SpeedRoundedIcon from '@mui/icons-material/SpeedRounded';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded';
import LabelRoundedIcon from '@mui/icons-material/LabelRounded';
import RemoveRoundedIcon from '@mui/icons-material/RemoveRounded';
import TuneRoundedIcon from '@mui/icons-material/TuneRounded';
import OpenInNewRoundedIcon from '@mui/icons-material/OpenInNewRounded';

// ─── Category Tag Color Helper ───────────────────────────────────────────────
const CATEGORY_COLORS = {
  'Trend Following': { bg: 'rgba(94,139,110,0.18)', text: '#5E8B6E' },
  'Mean Reversion': { bg: 'rgba(147,197,253,0.2)', text: '#3B82F6' },
  'Momentum': { bg: 'rgba(252,211,77,0.2)', text: '#D97706' },
  'Breakout': { bg: 'rgba(244,169,168,0.2)', text: '#D97070' },
};

const PLAYBOOK_ITEMS = [
  { id: 'ema_trend', name: 'EMA Trend', category: 'Trend Following', description: 'EMA crossover trend strategy', icon: ShowChartRoundedIcon },
  { id: 'rsi_reversal', name: 'RSI Mean Reversion', category: 'Mean Reversion', description: 'RSI oversold/overbought reversal', icon: TrendingUpRoundedIcon },
  { id: 'macd_momentum', name: 'MACD Momentum', category: 'Momentum', description: 'MACD crossover strategy', icon: BarChartRoundedIcon },
  { id: 'bollinger_breakout', name: 'Bollinger Breakout', category: 'Breakout', description: 'Bollinger Band breakout strategy', icon: ShieldRoundedIcon },
  { id: 'vwap_pullback', name: 'VWAP Pullback', category: 'Mean Reversion', description: 'Price pullback to VWAP strategy', icon: SpeedRoundedIcon },
  { id: 'adx_trend', name: 'ADX Trend Following', category: 'Trend Following', description: 'ADX based trend following', icon: ShowChartRoundedIcon },
  { id: 'donchian_breakout', name: 'Donchian Breakout', category: 'Breakout', description: 'Donchian channel breakout', icon: ShieldRoundedIcon },
];

const ML_MODELS_LIST = [
  { id: 'ml_classifier_v2', name: 'ML Classifier Model v2' },
  { id: 'btc_xgboost_reg', name: 'BTC XGBoost Regressor' },
  { id: 'lstm_trend_model', name: 'LSTM Trend Model' },
];

const INITIAL_SAVED_BACKTESTS = [
  { id: 1, name: 'EMA + RSI Crossover AND', symbol: 'BTCUSDT', timeframe: '1H', period: '2023-01-01 → 2024-12-31', totalReturn: 38.45, winRate: 61.54, totalTrades: 142, profitFactor: 1.78, maxDrawdown: -12.34, sharpeRatio: 1.32, runAt: '2024-12-27 15:30' },
  { id: 2, name: 'MACD + RSI Momentum OR', symbol: 'BTCUSDT', timeframe: '1H', period: '2023-01-01 → 2024-12-31', totalReturn: 24.18, winRate: 58.21, totalTrades: 187, profitFactor: 1.43, maxDrawdown: -15.21, sharpeRatio: 1.14, runAt: '2024-12-27 14:10' },
  { id: 3, name: 'EMA + MACD + ML AND', symbol: 'BTCUSDT', timeframe: '1H', period: '2023-01-01 → 2024-12-31', totalReturn: 52.67, winRate: 64.79, totalTrades: 118, profitFactor: 1.95, maxDrawdown: -9.88, sharpeRatio: 1.56, runAt: '2024-12-27 13:05' },
  { id: 4, name: 'Bollinger Breakout 4H', symbol: 'BTCUSDT', timeframe: '4H', period: '2023-01-01 → 2024-12-31', totalReturn: 17.23, winRate: 55.26, totalTrades: 96, profitFactor: 1.36, maxDrawdown: -14.02, sharpeRatio: 1.08, runAt: '2024-12-27 11:45' },
  { id: 5, name: 'VWAP Pullback Strategy', symbol: 'BTCUSDT', timeframe: '1H', period: '2023-01-01 → 2024-12-31', totalReturn: 21.34, winRate: 59.17, totalTrades: 131, profitFactor: 1.51, maxDrawdown: -11.76, sharpeRatio: 1.21, runAt: '2024-12-27 10:22' },
];

// ─── Small reusable Label component ──────────────────────────────────────────
function FieldLabel({ children }) {
  const theme = useTheme();
  return (
    <Typography sx={{ fontSize: '0.6875rem', fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: theme.palette.text.secondary, mb: 0.75, display: 'block' }}>
      {children}
    </Typography>
  );
}

// ─── PersistBars stepper ──────────────────────────────────────────────────────
function PersistStepper({ value, onDecrement, onIncrement }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0, background: isDark ? 'rgba(0,0,0,0.35)' : 'rgba(0,0,0,0.06)', borderRadius: '10px', border: `1px solid ${theme.palette.divider}`, overflow: 'hidden' }}>
      <IconButton size="small" onClick={onDecrement} sx={{ width: 24, height: 28, borderRadius: 0, color: theme.palette.text.secondary, '&:hover': { background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' } }}>
        <RemoveRoundedIcon sx={{ fontSize: 13 }} />
      </IconButton>
      <Typography sx={{ fontSize: '0.8125rem', fontWeight: 800, minWidth: 22, textAlign: 'center', color: theme.palette.text.primary }}>
        {value}
      </Typography>
      <IconButton size="small" onClick={onIncrement} sx={{ width: 24, height: 28, borderRadius: 0, color: theme.palette.text.secondary, '&:hover': { background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' } }}>
        <AddRoundedIcon sx={{ fontSize: 13 }} />
      </IconButton>
    </Box>
  );
}

// ─── Section Header ───────────────────────────────────────────────────────────
function SectionHeader({ step, title, subtitle, isDark }) {
  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 0.5 }}>
        <Box sx={{
          width: 26, height: 26, borderRadius: '8px', flexShrink: 0,
          background: `linear-gradient(135deg, ${COLORS.accent} 0%, ${COLORS.accentLight} 100%)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Typography sx={{ fontSize: '0.625rem', fontWeight: 900, color: '#fff', lineHeight: 1 }}>{step}</Typography>
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 800, fontSize: '0.875rem', lineHeight: 1.2 }}>{title}</Typography>
      </Box>
      <Typography variant="caption" sx={{ color: isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.45)', fontSize: '0.6875rem', pl: '38px', display: 'block' }}>
        {subtitle}
      </Typography>
    </Box>
  );
}

// ─── KPI Result Card ──────────────────────────────────────────────────────────
function KpiCard({ label, value, color, isDark }) {
  return (
    <Box sx={{
      flex: 1, minWidth: 0, p: { xs: 1.5, md: 2 }, borderRadius: '14px', textAlign: 'center',
      background: isDark ? 'rgba(255,255,255,0.025)' : 'rgba(0,0,0,0.018)',
      border: `1px solid ${isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)'}`,
      transition: 'all 0.2s ease',
      '&:hover': { transform: 'translateY(-2px)', borderColor: alpha(color, 0.4) },
    }}>
      <Typography sx={{ fontSize: '0.625rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.45)', mb: 0.5, display: 'block' }}>
        {label}
      </Typography>
      <Typography sx={{ fontSize: '1.375rem', fontWeight: 900, fontVariantNumeric: 'tabular-nums', color, lineHeight: 1.1 }}>
        {value}
      </Typography>
    </Box>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ═════════════════════════════════════════════════════════════════════════════
export default function StrategyBuilder() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const surface = isDark ? COLORS.darkSurface : COLORS.lightSurface;
  const surfaceAlt = isDark ? COLORS.darkSurfaceAlt : 'rgba(0,0,0,0.025)';
  const border = isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.07)';

  // ── State ─────────────────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState('');
  const [strategyName, setStrategyName] = useState('');

  const [selectedStrategies, setSelectedStrategies] = useState([]);
  const [selectedMlModels, setSelectedMlModels] = useState([]);
  const [combineLogic, setCombineLogic] = useState('AND');

  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1H');
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [takeProfit, setTakeProfit] = useState('2.00');
  const [stopLoss, setStopLoss] = useState('1.00');
  const [positionSizeType, setPositionSizeType] = useState('Fixed Percentage');
  const [positionSizeValue, setPositionSizeValue] = useState('10');

  const [isBacktesting, setIsBacktesting] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [backtestResults, setBacktestResults] = useState({
    totalReturn: 0, winRate: 0, totalTrades: 0,
    profitFactor: 0, maxDrawdown: 0, sharpeRatio: 0,
  });

  const [savedBacktests, setSavedBacktests] = useState(INITIAL_SAVED_BACKTESTS);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // ── Playbook handlers ─────────────────────────────────────────────────────
  const handleToggle = (item) => {
    setSelectedStrategies((prev) => {
      const exists = prev.some((s) => s.id === item.id);
      return exists ? prev.filter((s) => s.id !== item.id) : [...prev, { id: item.id, name: item.name, persistBars: 2 }];
    });
  };

  const handlePersist = (id, delta) =>
    setSelectedStrategies((prev) => prev.map((s) => s.id === id ? { ...s, persistBars: Math.max(1, s.persistBars + delta) } : s));

  const handleMlPersist = (id, delta) =>
    setSelectedMlModels((prev) => prev.map((m) => m.id === id ? { ...m, persistBars: Math.max(1, m.persistBars + delta) } : m));

  const handleAddMlModel = () => {
    const next = ML_MODELS_LIST.find((m) => !selectedMlModels.some((sm) => sm.id === m.id));
    if (next) setSelectedMlModels((prev) => [...prev, { ...next, persistBars: 1 }]);
    else setSnackbar({ open: true, message: 'All available ML models are already added.', severity: 'info' });
  };

  // ── Backtest handler ──────────────────────────────────────────────────────
  const handleRunBacktest = () => {
    if (!selectedStrategies.length) {
      setSnackbar({ open: true, message: 'Please select at least one strategy from the playbook.', severity: 'warning' });
      return;
    }
    setIsBacktesting(true);
    setTimeout(() => {
      setIsBacktesting(false);
      setHasResults(true);
      setBacktestResults({
        totalReturn: parseFloat((Math.random() * 40 + 12).toFixed(2)),
        winRate: parseFloat((Math.random() * 14 + 53).toFixed(2)),
        totalTrades: Math.floor(Math.random() * 80 + 90),
        profitFactor: parseFloat((Math.random() * 0.8 + 1.3).toFixed(2)),
        maxDrawdown: parseFloat((-1 * (Math.random() * 8 + 7)).toFixed(2)),
        sharpeRatio: parseFloat((Math.random() * 0.6 + 1.0).toFixed(2)),
      });
      setSnackbar({ open: true, message: 'Backtest executed successfully!', severity: 'success' });
    }, 1000);
  };

  // ── Save handler ──────────────────────────────────────────────────────────
  const handleSave = () => {
    if (!selectedStrategies.length) {
      setSnackbar({ open: true, message: 'Please assemble a strategy before saving.', severity: 'warning' });
      return;
    }
    if (!strategyName.trim()) {
      setSnackbar({ open: true, message: 'Please enter a Strategy Name before saving.', severity: 'warning' });
      return;
    }
    const newRecord = {
      id: savedBacktests.length + 1,
      name: strategyName.trim(),
      symbol, timeframe,
      period: `${startDate} → ${endDate}`,
      totalReturn: backtestResults.totalReturn,
      winRate: backtestResults.winRate,
      totalTrades: backtestResults.totalTrades,
      profitFactor: backtestResults.profitFactor,
      maxDrawdown: backtestResults.maxDrawdown,
      sharpeRatio: backtestResults.sharpeRatio,
      runAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
    };
    setSavedBacktests([newRecord, ...savedBacktests]);
    setSnackbar({ open: true, message: `Strategy "${strategyName.trim()}" saved successfully!`, severity: 'success' });
    setStrategyName('');
  };

  const filteredPlaybook = PLAYBOOK_ITEMS.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // ── Shared card sx ────────────────────────────────────────────────────────
  const cardSx = {
    borderRadius: '20px',
    background: surface,
    border: `1px solid ${border}`,
    boxShadow: isDark ? '0 4px 24px rgba(0,0,0,0.35)' : '0 4px 20px rgba(14,203,129,0.1)',
    display: 'flex',
    flexDirection: 'column',
    transition: 'box-shadow 0.25s ease',
  };

  return (
    <PageContainer title="Strategy Builder" breadcrumbs="Quantitative Catalog">
      <Box sx={{ pt: 1.5, display: 'flex', flexDirection: 'column', gap: 2.5 }}>

        {/* ── Page Header ───────────────────────────────────────────────── */}
        <Box sx={{
          borderRadius: '20px',
          background: 'linear-gradient(135deg, #2D4A38 0%, #3A6048 30%, #4A7A5A 60%, #5E8B6E 100%)',
          boxShadow: '0 8px 32px rgba(45,74,56,0.45)',
          p: { xs: 2.5, md: 3 },
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 2,
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* decorative circles */}
          <Box sx={{ position: 'absolute', right: -50, top: -50, width: 240, height: 240, borderRadius: '50%', background: 'rgba(255,255,255,0.07)' }} />
          <Box sx={{ position: 'absolute', right: 60, bottom: -90, width: 180, height: 180, borderRadius: '50%', background: 'rgba(255,255,255,0.04)' }} />
          <Box sx={{ position: 'absolute', left: -30, bottom: -60, width: 140, height: 140, borderRadius: '50%', background: 'rgba(255,255,255,0.03)' }} />

          <Box sx={{ zIndex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
              <Box sx={{ width: 42, height: 42, borderRadius: '13px', background: 'rgba(255,255,255,0.18)', backdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <TuneRoundedIcon sx={{ color: '#fff', fontSize: 22 }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 900, color: '#fff', letterSpacing: '-0.025em', textShadow: '0 2px 8px rgba(0,0,0,0.25)' }}>
                Strategy Builder
              </Typography>
            </Box>
            <Typography sx={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.75rem', pl: '56px', letterSpacing: '0.03em' }}>
              Select from Playbook · Configure · Run Backtest · Save
            </Typography>
          </Box>

          <Stack direction="row" spacing={1.5} sx={{ zIndex: 1 }}>
            <Button
              variant="outlined"
              startIcon={isBacktesting ? <CircularProgress size={15} sx={{ color: '#fff' }} /> : <PlayArrowRoundedIcon />}
              onClick={handleRunBacktest}
              disabled={isBacktesting}
              sx={{
                fontWeight: 700, borderRadius: '12px',
                borderColor: 'rgba(255,255,255,0.6)',
                color: '#fff',
                background: 'rgba(255,255,255,0.12)',
                backdropFilter: 'blur(6px)',
                '&:hover': { borderColor: '#fff', background: 'rgba(255,255,255,0.22)' },
              }}
            >
              {isBacktesting ? 'Running…' : 'Run Backtest'}
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveRoundedIcon />}
              onClick={handleSave}
              sx={{
                fontWeight: 700, borderRadius: '12px',
                background: '#ffffff',
                color: COLORS.accentDark,
                boxShadow: '0 4px 16px rgba(0,0,0,0.22)',
                '&:hover': { background: 'rgba(255,255,255,0.9)', boxShadow: '0 6px 22px rgba(0,0,0,0.3)' },
              }}
            >
              Save Strategy
            </Button>
          </Stack>
        </Box>

        {/* ── Strategy Name Input ───────────────────────────────────────── */}
        <Box sx={{ ...cardSx, p: 2, flexDirection: 'row', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
            <LabelRoundedIcon sx={{ color: COLORS.accent, fontSize: 20 }} />
            <Typography variant="body2" sx={{ fontWeight: 700, whiteSpace: 'nowrap' }}>Strategy Name</Typography>
          </Box>
          <TextField
            value={strategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            placeholder="e.g. BTC EMA + RSI Confluence AND"
            size="small"
            sx={{ flex: 1, minWidth: 280 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <AutoAwesomeRoundedIcon sx={{ fontSize: 16, color: COLORS.accent }} />
                </InputAdornment>
              ),
            }}
          />
          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, whiteSpace: 'nowrap', flexShrink: 0 }}>
            Give your strategy a unique, descriptive name before saving
          </Typography>
        </Box>

        {/* ── 3-Column Builder Workspace ────────────────────────────────── */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr 1fr' }, gap: 2.5, alignItems: 'start' }}>

          {/* ╔═══════════════════════════════════════════════════╗
              ║  COL 1 — PLAYBOOK                                ║
              ╚═══════════════════════════════════════════════════╝ */}
          <Box sx={cardSx}>
            <Box sx={{ p: '20px 20px 16px' }}>
              <SectionHeader step="01" title="Playbook Library" isDark={isDark} />
              {/* Search */}
              <Box sx={{
                display: 'flex', alignItems: 'center', gap: 1,
                background: surfaceAlt,
                border: `1px solid ${border}`,
                borderRadius: '12px',
                px: 1.5, py: 0.75,
              }}>
                <SearchRoundedIcon sx={{ fontSize: 16, color: theme.palette.text.secondary }} />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search strategies…"
                  style={{
                    background: 'transparent', border: 'none', outline: 'none',
                    fontSize: '0.8125rem', color: theme.palette.text.primary,
                    width: '100%', fontFamily: 'inherit',
                  }}
                />
              </Box>
            </Box>

            <Box sx={{ px: 1.5, pb: 2, display: 'flex', flexDirection: 'column', gap: 0.75, maxHeight: 440, overflowY: 'auto' }}>
              {filteredPlaybook.map((item) => {
                const isSelected = selectedStrategies.some((s) => s.id === item.id);
                const ItemIcon = item.icon;
                const catColor = CATEGORY_COLORS[item.category] || { bg: 'rgba(94,139,110,0.15)', text: COLORS.accent };

                return (
                  <Box
                    key={item.id}
                    onClick={() => handleToggle(item)}
                    sx={{
                      display: 'flex', alignItems: 'center', gap: 1.5,
                      px: 1.25, py: 1.25, borderRadius: '14px', cursor: 'pointer',
                      transition: 'all 0.18s ease',
                      background: isSelected
                        ? isDark ? 'rgba(94,139,110,0.15)' : 'rgba(94,139,110,0.09)'
                        : 'transparent',
                      border: `1px solid ${isSelected ? alpha(COLORS.accent, 0.4) : 'transparent'}`,
                      '&:hover': { background: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)', borderColor: alpha(COLORS.accent, 0.25) },
                    }}
                  >
                    {/* Checkbox */}
                    <Box sx={{
                      width: 20, height: 20, borderRadius: '6px', flexShrink: 0,
                      border: `2px solid ${isSelected ? COLORS.accent : isDark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)'}`,
                      background: isSelected ? COLORS.accent : 'transparent',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      transition: 'all 0.18s ease',
                    }}>
                      {isSelected && <CheckCircleRoundedIcon sx={{ fontSize: 13, color: '#fff' }} />}
                    </Box>

                    {/* Icon bubble */}
                    <Box sx={{ width: 36, height: 36, borderRadius: '11px', flexShrink: 0, background: catColor.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <ItemIcon sx={{ fontSize: 18, color: catColor.text }} />
                    </Box>

                    {/* Text */}
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700, color: theme.palette.text.primary, lineHeight: 1.2 }}>
                        {item.name}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mt: 0.4 }}>
                        <Box sx={{ px: 0.75, py: 0.1, borderRadius: '6px', background: catColor.bg }}>
                          <Typography sx={{ fontSize: '0.5625rem', fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase', color: catColor.text, lineHeight: 1.6 }}>
                            {item.category}
                          </Typography>
                        </Box>
                        <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {item.description}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                );
              })}
            </Box>

            <Box sx={{ px: 2.5, py: 1.5, borderTop: `1px solid ${border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary }}>
                {filteredPlaybook.length} / {PLAYBOOK_ITEMS.length} strategies
              </Typography>
              <Chip
                label={`${selectedStrategies.length} selected`}
                size="small"
                sx={{ height: 20, fontSize: '0.625rem', fontWeight: 800, background: alpha(COLORS.accent, 0.15), color: COLORS.accent }}
              />
            </Box>
          </Box>

          {/* ╔═══════════════════════════════════════════════════╗
              ║  COL 2 — BUILD STRATEGY                          ║
              ╚═══════════════════════════════════════════════════╝ */}
          <Box sx={cardSx}>
            <Box sx={{ p: '20px 20px 0' }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 0 }}>
                <SectionHeader step="02" title="Build Strategy" isDark={isDark} />
                {selectedStrategies.length > 0 && (
                  <Button size="small" onClick={() => setSelectedStrategies([])} sx={{ color: COLORS.pnlRed, fontSize: '0.6875rem', fontWeight: 700, mt: 0.25, minWidth: 0 }}>
                    Clear All
                  </Button>
                )}
              </Box>
            </Box>

            <Box sx={{ px: 2, pb: 2, flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>

              {/* Selected Strategies */}
              <Box>
                <FieldLabel>Selected Strategies</FieldLabel>
                <Stack spacing={1}>
                  {selectedStrategies.length === 0 ? (
                    <Box sx={{ py: 3, borderRadius: '14px', border: `1.5px dashed ${border}`, textAlign: 'center' }}>
                      <Typography sx={{ fontSize: '0.75rem', color: theme.palette.text.secondary }}>
                        Pick strategies from the Playbook →
                      </Typography>
                    </Box>
                  ) : (
                    selectedStrategies.map((strat) => (
                      <Box key={strat.id} sx={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1,
                        px: 1.25, py: 1, borderRadius: '14px',
                        background: surfaceAlt, border: `1px solid ${border}`,
                      }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                          <DragIndicatorRoundedIcon sx={{ fontSize: 16, color: theme.palette.text.secondary }} />
                          <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700 }}>{strat.name}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                            <Typography sx={{ fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: theme.palette.text.secondary }}>
                              Persist
                            </Typography>
                            <PersistStepper
                              value={strat.persistBars}
                              onDecrement={() => handlePersist(strat.id, -1)}
                              onIncrement={() => handlePersist(strat.id, +1)}
                            />
                          </Box>
                          <IconButton size="small" onClick={() => setSelectedStrategies((p) => p.filter((s) => s.id !== strat.id))} sx={{ color: theme.palette.text.secondary, '&:hover': { color: COLORS.pnlRed } }}>
                            <DeleteOutlineRoundedIcon sx={{ fontSize: 17 }} />
                          </IconButton>
                        </Box>
                      </Box>
                    ))
                  )}
                </Stack>
              </Box>

              <Divider sx={{ borderColor: border }} />

              {/* ML Models */}
              <Box>
                <FieldLabel>Optional — ML Model (same timeframe)</FieldLabel>
                <Stack spacing={1}>
                  {selectedMlModels.map((ml) => (
                    <Box key={ml.id} sx={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1,
                      px: 1.25, py: 1, borderRadius: '14px',
                      background: isDark ? 'rgba(94,139,110,0.1)' : 'rgba(94,139,110,0.07)',
                      border: `1px solid ${alpha(COLORS.accent, 0.3)}`,
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                        <PsychologyRoundedIcon sx={{ fontSize: 17, color: COLORS.accent }} />
                        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700, color: COLORS.accent }}>{ml.name}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                          <Typography sx={{ fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: theme.palette.text.secondary }}>
                            Persist
                          </Typography>
                          <PersistStepper
                            value={ml.persistBars}
                            onDecrement={() => handleMlPersist(ml.id, -1)}
                            onIncrement={() => handleMlPersist(ml.id, +1)}
                          />
                        </Box>
                        <IconButton size="small" onClick={() => setSelectedMlModels((p) => p.filter((m) => m.id !== ml.id))} sx={{ color: theme.palette.text.secondary, '&:hover': { color: COLORS.pnlRed } }}>
                          <DeleteOutlineRoundedIcon sx={{ fontSize: 17 }} />
                        </IconButton>
                      </Box>
                    </Box>
                  ))}
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AddRoundedIcon />}
                    onClick={handleAddMlModel}
                    fullWidth
                    sx={{ borderRadius: '12px', fontWeight: 700, fontSize: '0.75rem', borderColor: alpha(COLORS.accent, 0.4), color: COLORS.accent, py: 0.75, '&:hover': { borderColor: COLORS.accent, background: alpha(COLORS.accent, 0.08) } }}
                  >
                    Add Another ML Model
                  </Button>
                </Stack>
              </Box>

              <Divider sx={{ borderColor: border }} />

              {/* Combine Logic */}
              <Box>
                <FieldLabel>Combine Logic</FieldLabel>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
                    {['AND', 'OR'].map((logic) => (
                      <Button
                        key={logic}
                        onClick={() => setCombineLogic(logic)}
                        sx={{
                          minWidth: 64, borderRadius: '12px', fontWeight: 800, fontSize: '0.875rem',
                          transition: 'all 0.18s ease',
                          ...(combineLogic === logic
                            ? { background: `linear-gradient(135deg, ${COLORS.accent} 0%, ${COLORS.accentLight} 100%)`, color: '#fff', boxShadow: `0 4px 14px ${alpha(COLORS.accent, 0.45)}` }
                            : { background: surfaceAlt, color: theme.palette.text.secondary, border: `1px solid ${border}`, '&:hover': { borderColor: COLORS.accent, color: COLORS.accent } }),
                        }}
                      >
                        {logic}
                      </Button>
                    ))}
                  </Stack>

                  <Box sx={{ flex: 1, px: 1.5, py: 1.25, borderRadius: '12px', background: surfaceAlt, border: `1px solid ${border}` }}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, lineHeight: 1.5 }}>
                      {combineLogic === 'AND'
                        ? 'ALL selected strategies must agree on the same signal to trigger a trade.'
                        : 'ANY selected strategy producing a valid signal will trigger a trade.'}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          </Box>

          {/* ╔═══════════════════════════════════════════════════╗
              ║  COL 3 — BACKTEST CONFIGURATION                  ║
              ╚═══════════════════════════════════════════════════╝ */}
          <Box sx={cardSx}>
            <Box sx={{ p: '20px 20px 16px' }}>
              <SectionHeader step="03" title="Backtest Configuration" isDark={isDark} />
            </Box>

            <Box sx={{ px: 2, pb: 2.5, flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>

              {/* Symbol & Timeframe */}
              <Box>
                <FieldLabel>Market Settings</FieldLabel>
                <Grid container spacing={1.5}>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Symbol</Typography>
                    <Select value={symbol} onChange={(e) => setSymbol(e.target.value)} fullWidth size="small">
                      {['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'LTCUSDT', 'DOGEUSDT', 'MINAUSDT', 'SUIUSDT', 'ADAUSDT'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                    </Select>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Timeframe</Typography>
                    <Select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} fullWidth size="small">
                      {['1m', '5m', '15m', '30m', '1H', '4H', '1D', '1W'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                    </Select>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Start Date</Typography>
                    <TextField type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} fullWidth size="small" />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>End Date</Typography>
                    <TextField type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} fullWidth size="small" />
                  </Grid>
                </Grid>
              </Box>

              <Divider sx={{ borderColor: border }} />

              {/* Execution Settings */}
              <Box>
                <FieldLabel>Execution Settings</FieldLabel>
                <Grid container spacing={1.5}>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Take Profit (%)</Typography>
                    <TextField type="number" value={takeProfit} onChange={(e) => setTakeProfit(e.target.value)} fullWidth size="small" inputProps={{ step: '0.1' }} />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Stop Loss (%)</Typography>
                    <TextField type="number" value={stopLoss} onChange={(e) => setStopLoss(e.target.value)} fullWidth size="small" inputProps={{ step: '0.1' }} />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Position Size</Typography>
                    <Select value={positionSizeType} onChange={(e) => setPositionSizeType(e.target.value)} fullWidth size="small">
                      <MenuItem value="Fixed Percentage">Fixed Percentage</MenuItem>
                      <MenuItem value="Fixed Amount">Fixed Amount</MenuItem>
                    </Select>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Value (%)</Typography>
                    <TextField type="number" value={positionSizeValue} onChange={(e) => setPositionSizeValue(e.target.value)} fullWidth size="small" />
                  </Grid>
                </Grid>
              </Box>

              {/* Run Backtest */}
              <Button
                variant="contained"
                fullWidth
                onClick={handleRunBacktest}
                disabled={isBacktesting}
                startIcon={isBacktesting ? <CircularProgress size={17} sx={{ color: '#fff' }} /> : <PlayArrowRoundedIcon />}
                sx={{
                  mt: 'auto', py: 1.375, fontWeight: 800, fontSize: '0.9rem', borderRadius: '14px',
                  background: `linear-gradient(135deg, ${COLORS.accentDark} 0%, ${COLORS.accent} 50%, ${COLORS.accentLight} 100%)`,
                  color: '#fff',
                  boxShadow: `0 6px 20px ${alpha(COLORS.accent, 0.45)}`,
                  letterSpacing: '0.01em',
                  '&:hover': { boxShadow: `0 8px 28px ${alpha(COLORS.accent, 0.6)}`, transform: 'translateY(-1px)' },
                  transition: 'all 0.2s ease',
                }}
              >
                {isBacktesting ? 'Running Backtest…' : 'Run Backtest'}
              </Button>
            </Box>
          </Box>
        </Box>

        {hasResults && (
          <Box sx={{ ...cardSx, p: 2.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                <Box sx={{ width: 26, height: 26, borderRadius: '8px', background: `linear-gradient(135deg, ${COLORS.accent} 0%, ${COLORS.accentLight} 100%)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography sx={{ fontSize: '0.625rem', fontWeight: 900, color: '#fff' }}>04</Typography>
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 800, fontSize: '0.875rem' }}>Backtest Results</Typography>
              </Box>
              <Chip label="Latest Run" size="small" sx={{ height: 22, fontSize: '0.625rem', fontWeight: 800, background: alpha(COLORS.pnlGreen, 0.15), color: COLORS.pnlGreen }} />
            </Box>

            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
              {[
                { label: 'Total Return', value: `${backtestResults.totalReturn >= 0 ? '+' : ''}${backtestResults.totalReturn.toFixed(2)}%`, color: backtestResults.totalReturn >= 0 ? COLORS.pnlGreen : COLORS.pnlRed },
                { label: 'Win Rate', value: `${backtestResults.winRate.toFixed(2)}%`, color: backtestResults.winRate >= 50 ? COLORS.pnlGreen : COLORS.pnlRed },
                { label: 'Total Trades', value: backtestResults.totalTrades, color: theme.palette.text.primary },
                { label: 'Profit Factor', value: backtestResults.profitFactor.toFixed(2), color: backtestResults.profitFactor >= 1.2 ? COLORS.pnlGreen : COLORS.pnlRed },
                { label: 'Max Drawdown', value: `${backtestResults.maxDrawdown.toFixed(2)}%`, color: COLORS.pnlRed },
                { label: 'Sharpe Ratio', value: backtestResults.sharpeRatio.toFixed(2), color: backtestResults.sharpeRatio >= 1.0 ? COLORS.pnlGreen : theme.palette.text.primary },
              ].map((kpi) => (
                <KpiCard key={kpi.label} label={kpi.label} value={kpi.value} color={kpi.color} isDark={isDark} />
              ))}
            </Box>
          </Box>
        )}

        {/* ── Section 4: Saved Backtests Table ──────────────────────────── */}
        <Box sx={cardSx}>
          <Box sx={{ px: 2.5, pt: 2.5, pb: 1.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
              <Box sx={{ width: 26, height: 26, borderRadius: '8px', background: `linear-gradient(135deg, ${COLORS.accent} 0%, ${COLORS.accentLight} 100%)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography sx={{ fontSize: '0.625rem', fontWeight: 900, color: '#fff' }}>04</Typography>
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 800, fontSize: '0.875rem' }}>Saved Backtests & Strategies</Typography>
            </Box>
            <Chip label={`${savedBacktests.length} records`} size="small" sx={{ height: 22, fontSize: '0.625rem', fontWeight: 800, background: surfaceAlt, color: theme.palette.text.secondary }} />
          </Box>

          <TableContainer sx={{ borderRadius: '0 0 20px 20px' }}>
            <Table size="small" sx={{ tableLayout: 'fixed', width: '100%' }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ width: '4%', px: 1.5 }}>#</TableCell>
                  <TableCell sx={{ width: '24%', px: 1.5 }}>Strategy Name</TableCell>
                  <TableCell sx={{ width: '8%', px: 1 }}>Symbol</TableCell>
                  <TableCell sx={{ width: '6%', px: 1 }}>TF</TableCell>
                  <TableCell sx={{ width: '10%', px: 1.5 }} align="right">Return</TableCell>
                  <TableCell sx={{ width: '10%', px: 1.5 }} align="right">Win Rate</TableCell>
                  <TableCell sx={{ width: '8%', px: 1.5 }} align="right">Trades</TableCell>
                  <TableCell sx={{ width: '10%', px: 1.5 }} align="right">P.Factor</TableCell>
                  <TableCell sx={{ width: '10%', px: 1.5 }} align="right">Max DD</TableCell>
                  <TableCell sx={{ width: '9%', px: 1.5 }} align="right">Sharpe</TableCell>
                  <TableCell sx={{ width: '8%', px: 0.5 }} align="center">Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {savedBacktests.map((row, idx) => (
                  <TableRow key={row.id} hover>
                    <TableCell sx={{ color: theme.palette.text.secondary, fontSize: '0.75rem', px: 1.5 }}>{idx + 1}</TableCell>
                    <TableCell sx={{ px: 1.5 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, lineHeight: 1.2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.name}</Typography>
                    </TableCell>
                    <TableCell sx={{ px: 1 }}>
                      <Chip label={row.symbol.replace('USDT', '')} size="small" sx={{ height: 19, fontSize: '0.5625rem', fontWeight: 800, background: alpha(COLORS.accent, 0.14), color: COLORS.accent }} />
                    </TableCell>
                    <TableCell sx={{ px: 1 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: theme.palette.text.secondary }}>{row.timeframe}</Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ px: 1.5 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: row.totalReturn >= 0 ? COLORS.pnlGreen : COLORS.pnlRed }}>
                        {row.totalReturn >= 0 ? '+' : ''}{row.totalReturn.toFixed(2)}%
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ px: 1.5 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: COLORS.pnlGreen }}>
                        {row.winRate.toFixed(2)}%
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, fontSize: '0.75rem', px: 1.5 }}>{row.totalTrades}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, fontSize: '0.75rem', px: 1.5 }}>{row.profitFactor.toFixed(2)}</TableCell>
                    <TableCell align="right" sx={{ px: 1.5 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: COLORS.pnlRed }}>
                        {row.maxDrawdown.toFixed(2)}%
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ px: 1.5 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: row.sharpeRatio >= 1.0 ? COLORS.pnlGreen : theme.palette.text.primary }}>
                        {row.sharpeRatio.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center" sx={{ px: 0.5 }}>
                      <Button
                        size="small"
                        endIcon={<OpenInNewRoundedIcon sx={{ fontSize: 12 }} />}
                        onClick={() => navigate(`/backtests/${row.id}`)}
                        sx={{ fontSize: '0.6875rem', fontWeight: 700, color: COLORS.accent, px: 0.75, minWidth: 0 }}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>

        {/* ── Toast ──────────────────────────────────────────────────────── */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={() => setSnackbar((p) => ({ ...p, open: false }))}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert severity={snackbar.severity} onClose={() => setSnackbar((p) => ({ ...p, open: false }))}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </PageContainer>
  );
}
