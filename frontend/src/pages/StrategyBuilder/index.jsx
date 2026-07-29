import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPlaybook, saveStrategy, getStrategies, runDynamicBacktest } from '../../api/strategiesApi';
import { getBacktests } from '../../api/backtestsApi';
import { getModels } from '../../api/mlApi';
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
import TablePagination from '@mui/material/TablePagination';
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
  const [filterSymbol, setFilterSymbol] = useState('ALL');
  const [strategyName, setStrategyName] = useState('');
  const [isNameEdited, setIsNameEdited] = useState(false);

  const [selectedStrategies, setSelectedStrategies] = useState([]);
  const [selectedMlModels, setSelectedMlModels] = useState([]);
  const [combineLogic, setCombineLogic] = useState('AND');

  const [symbol, setSymbol] = useState('BTC');
  const [timeframe, setTimeframe] = useState('15m');
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

  const [savedBacktests, setSavedBacktests] = useState([]);
  const [playbookItems, setPlaybookItems] = useState([]);
  const [mlModelsList, setMlModelsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Sorting & Pagination States for Saved Backtests (Section 04)
  const [tableFilterSymbol, setTableFilterSymbol] = useState('ALL');
  const [sortField, setSortField] = useState(null);
  const [sortOrder, setSortOrder] = useState('asc');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
    setPage(0);
  };

  const filteredTableBacktests = savedBacktests.filter(row => {
    if (tableFilterSymbol === 'ALL') return true;
    const baseSym = row.symbol.replace('USDT', '').replace('/', '').trim().toUpperCase();
    return baseSym === tableFilterSymbol.toUpperCase();
  });

  const sortedBacktests = [...filteredTableBacktests].sort((a, b) => {
    if (!sortField) return 0;
    let aVal = a[sortField];
    let bVal = b[sortField];
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }
    if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const startIndex = page * rowsPerPage;
  const paginatedBacktests = sortedBacktests.slice(startIndex, startIndex + rowsPerPage);

  const reloadSavedStrategies = async () => {
    try {
      const savedRes = await getBacktests();
      const savedData = Array.isArray(savedRes?.data) ? savedRes.data : [];
      const mappedSaved = savedData.map(item => {
        let dateStr = 'N/A';
        if (item.submitted_at) {
          try {
            dateStr = new Date(item.submitted_at).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'short',
              day: 'numeric'
            });
          } catch (e) {
            dateStr = String(item.submitted_at).split('T')[0];
          }
        }
        return {
          id: item.strategy_id,
          name: item.strategy_name,
          symbol: item.symbol,
          timeframe: item.timeframe,
          period: 'Live / Managed',
          totalReturn: (item.net_pnl || 0.0) / 100,
          winRate: (item.win_rate != null ? item.win_rate * 100 : 0.0),
          totalTrades: item.total_trades || 0,
          maxDrawdown: item.max_drawdown || 0.0,
          runAt: dateStr
        };
      });
      setSavedBacktests(mappedSaved);
    } catch (err) {
      console.error("Error refreshing saved strategies:", err);
    }
  };

  const reloadPlaybook = async () => {
    try {
      const playbookData = await getPlaybook();
      const resolvedPlaybook = playbookData.map(item => {
        let category = "Trend Following";
        const lowerName = item.name.toLowerCase();
        if (lowerName.includes("rsi") || lowerName.includes("reversion") || lowerName.includes("reversal")) {
          category = "Mean Reversion";
        } else if (lowerName.includes("macd") || lowerName.includes("momentum")) {
          category = "Momentum";
        } else if (lowerName.includes("breakout") || lowerName.includes("bollinger")) {
          category = "Breakout";
        }
        
        let icon = ShowChartRoundedIcon;
        if (category === "Mean Reversion") icon = TrendingUpRoundedIcon;
        if (category === "Momentum") icon = BarChartRoundedIcon;
        if (category === "Breakout") icon = ShieldRoundedIcon;
        
        return {
          ...item,
          category,
          description: `Configuration from database template`,
          icon
        };
      });
      setPlaybookItems(resolvedPlaybook);
    } catch (err) {
      console.error("Error refreshing playbook:", err);
    }
  };

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        await reloadPlaybook();
        
        const modelsRes = await getModels();
        const modelsData = Array.isArray(modelsRes?.data) ? modelsRes.data : [];
        setMlModelsList(modelsData);
        
        await reloadSavedStrategies();
      } catch (err) {
        console.error("Error loading Strategy Builder data:", err);
        setSnackbar({ open: true, message: "Error loading strategies from database", severity: "error" });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // ── Auto-generate Strategy Name ──────────────────────────────────────────
  useEffect(() => {
    if (isNameEdited) return;

    if (selectedStrategies.length === 0 && selectedMlModels.length === 0) {
      setStrategyName('');
      return;
    }

    const strategyNames = [];
    selectedStrategies.forEach(s => {
      const name = s.name.toUpperCase();
      let matched = "";
      if (name.includes("EMA")) matched = "EMA";
      else if (name.includes("RSI")) matched = "RSI";
      else if (name.includes("MACD")) matched = "MACD";
      else if (name.includes("BOLLINGER") || name.includes("BANDS")) matched = "BB";
      else if (name.includes("VWAP")) matched = "VWAP";
      else if (name.includes("ADX")) matched = "ADX";
      else if (name.includes("DONCHIAN")) matched = "DONCHIAN";
      else {
        matched = s.name.replace(/BTC|ETH|SOL|LTC|DOGE|MINA|SUI|ADA/gi, '')
                        .replace(/\d+[mhd]/gi, '')
                        .trim();
      }
      if (matched && !strategyNames.includes(matched)) {
        strategyNames.push(matched);
      }
    });

    const mlNames = [];
    selectedMlModels.forEach(m => {
      const name = m.name.toUpperCase();
      let matched = "";
      if (name.includes("LSTM")) matched = "LSTM";
      else if (name.includes("LIGHTGBM") || name.includes("LGBM")) matched = "LGBM";
      else if (name.includes("XGBOOST") || name.includes("XGB")) matched = "XGB";
      else if (name.includes("SVM")) matched = "SVM";
      else if (name.includes("RANDOM FOREST") || name.includes("FOREST")) matched = "RF";
      else if (name.includes("DECISION TREE") || name.includes("TREE")) matched = "DT";
      else if (name.includes("LOGISTIC")) matched = "LR";
      else matched = m.name;
      
      if (matched && !mlNames.includes(matched)) {
        mlNames.push(matched);
      }
    });

    const symbolPrefix = symbol.replace("USDT", "");
    const tfVal = timeframe;
    
    const partsList = [
      symbolPrefix,
      tfVal,
      ...strategyNames,
      ...mlNames
    ];

    const finalGenerated = partsList.join(" ").replace(/\s+/g, ' ').trim();
    setStrategyName(finalGenerated);
  }, [selectedStrategies, selectedMlModels, combineLogic, isNameEdited, symbol, timeframe]);

  // ── Playbook handlers ─────────────────────────────────────────────────────
  const handleToggle = (item) => {
    const exists = selectedStrategies.some((s) => s.id === item.id);
    if (!exists) {
      // Compatibility Check: Only allow combining strategies of the same asset/symbol
      const extractBaseSymbol = (name) => {
        const parts = name.toUpperCase().split(" ");
        const symbols = ['BTC', 'ETH', 'SOL', 'LTC', 'DOGE', 'MINA', 'SUI', 'ADA'];
        for (const part of parts) {
          const clean = part.trim();
          if (symbols.includes(clean)) return clean;
        }
        return null;
      };

      const itemSymbol = extractBaseSymbol(item.name);
      if (itemSymbol && selectedStrategies.length > 0) {
        const firstSelected = playbookItems.find(p => p.id === selectedStrategies[0].id);
        if (firstSelected) {
          const activeSymbol = extractBaseSymbol(firstSelected.name);
          if (activeSymbol && activeSymbol !== itemSymbol) {
            setSnackbar({
              open: true,
              message: `Conflict: You can only combine strategies for the same asset. Selected: ${activeSymbol}, tried to add: ${itemSymbol}.`,
              severity: 'warning'
            });
            return;
          }
        }
      }

      setSelectedStrategies((prev) => [...prev, { id: item.id, name: item.name, persistBars: 2 }]);
      
      // Auto-prefill parameters with the selected template settings
      const parts = item.name.split(" ");
      const symbols = ['BTC', 'ETH', 'SOL', 'LTC', 'DOGE', 'MINA', 'SUI', 'ADA'];
      const timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1H', '4H', '1D', '1W'];
      
      let foundSymbol = symbol;
      let foundTimeframe = timeframe;
      
      parts.forEach(p => {
        const clean = p.toUpperCase().trim();
        if (symbols.includes(clean)) {
          foundSymbol = clean;
        }
        const cleanTf = p.trim();
        if (timeframes.includes(cleanTf)) {
          let normTf = cleanTf;
          if (normTf.toLowerCase().endsWith('m')) {
            normTf = normTf.toLowerCase();
          } else {
            normTf = normTf.toUpperCase();
          }
          foundTimeframe = normTf;
        }
      });
      
      setSymbol(foundSymbol);
      setTimeframe(foundTimeframe);
      
      // Prefill Start and End dates
      if (item.start_time) {
        setStartDate(item.start_time.split("T")[0]);
      }
      if (item.end_time) {
        setEndDate(item.end_time.split("T")[0]);
      }
      
      // Prefill Take Profit & Stop Loss
      let config = item.strategy_config;
      if (typeof config === "string") {
        try {
          config = JSON.parse(config);
        } catch (e) {
          config = {};
        }
      }
      if (config) {
        const tp = config.take_profit;
        const sl = config.stop_loss;
        if (tp != null) setTakeProfit(parseFloat(tp).toFixed(2));
        if (sl != null) setStopLoss(parseFloat(sl).toFixed(2));

        const pst = config.position_size_type;
        const psv = config.position_size_value;
        if (pst) setPositionSizeType(pst);
        if (psv != null) setPositionSizeValue(psv.toString());
      }
      
      setStrategyName(`${item.name} Custom`);
    } else {
      setSelectedStrategies((prev) => prev.filter((s) => s.id !== item.id));
    }
  };

  const handlePersist = (id, delta) =>
    setSelectedStrategies((prev) => prev.map((s) => s.id === id ? { ...s, persistBars: Math.max(1, s.persistBars + delta) } : s));

  const handleMlPersist = (id, delta) =>
    setSelectedMlModels((prev) => prev.map((m) => m.id === id ? { ...m, persistBars: Math.max(1, m.persistBars + delta) } : m));

  const handleAddMlModel = () => {
    const next = filteredMlModels.find((m) => !selectedMlModels.some((sm) => sm.id === m.model_id));
    if (next) setSelectedMlModels((prev) => [...prev, { id: next.model_id, name: next.name, persistBars: 1 }]);
    else setSnackbar({ open: true, message: 'All matching ML models are already added.', severity: 'info' });
  };

  // ── Backtest handler ──────────────────────────────────────────────────────
  const handleRunBacktest = async () => {
    if (!selectedStrategies.length) {
      setSnackbar({ open: true, message: 'Please select at least one strategy from the playbook.', severity: 'warning' });
      return;
    }
    
    setIsBacktesting(true);
    setHasResults(false);

    // 1. Build Consolidated Indicators Configuration
    const consolidatedIndicators = {};
    selectedStrategies.forEach(s => {
      const playbookItem = playbookItems.find(p => p.id === s.id);
      if (playbookItem && playbookItem.indicators_config) {
        Object.entries(playbookItem.indicators_config).forEach(([indKey, indVal]) => {
          if (!consolidatedIndicators[indKey]) {
            consolidatedIndicators[indKey] = [];
          }
          const configs = Array.isArray(indVal) ? indVal : [indVal];
          configs.forEach(cfg => {
            const alreadyExists = consolidatedIndicators[indKey].some(
              ex => JSON.stringify(ex) === JSON.stringify(cfg)
            );
            if (!alreadyExists) {
              consolidatedIndicators[indKey].push(cfg);
            }
          });
        });
      }
    });

    // 2. Build Long and Short conditions
    const longConditions = [];
    const shortConditions = [];

    selectedStrategies.forEach(s => {
      const playbookItem = playbookItems.find(p => p.id === s.id);
      if (playbookItem && playbookItem.strategy_config) {
        const stratCfg = playbookItem.strategy_config;
        const itemLongConds = stratCfg.long?.conditions || [];
        const itemShortConds = stratCfg.short?.conditions || [];

        itemLongConds.forEach(c => {
          longConditions.push({
            ...c,
            persist_bars: s.persistBars || 0
          });
        });
        itemShortConds.forEach(c => {
          shortConditions.push({
            ...c,
            persist_bars: s.persistBars || 0
          });
        });
      }
    });

    selectedMlModels.forEach(m => {
      longConditions.push({
        left: `ml_signal_${m.id}`,
        operator: "==",
        right: 1,
        persist_bars: m.persistBars || 0
      });
      shortConditions.push({
        left: `ml_signal_${m.id}`,
        operator: "==",
        right: -1,
        persist_bars: m.persistBars || 0
      });
    });

    const consolidatedStrategy = {
      long: {
        rule: combineLogic,
        conditions: longConditions
      },
      short: {
        rule: combineLogic,
        conditions: shortConditions
      },
      stop_loss: parseFloat(stopLoss),
      take_profit: parseFloat(takeProfit),
      position_size_type: positionSizeType,
      position_size_value: parseFloat(positionSizeValue)
    };

    try {
      const payload = {
        strategy_name: strategyName.trim() || "Dynamic Backtest Run",
        exchange: 'bybit',
        symbol: symbol,
        timeframe,
        start_date: startDate,
        end_date: endDate,
        indicators_config: consolidatedIndicators,
        strategy_config: consolidatedStrategy
      };

      const res = await runDynamicBacktest(payload);
      if (res && res.success) {
        setBacktestResults({
          totalReturn: parseFloat((res.metrics.net_pnl / 100).toFixed(2)),
          winRate: parseFloat((res.metrics.win_rate * 100).toFixed(2)),
          totalTrades: res.metrics.total_trades,
          profitFactor: res.metrics.profit_factor || 1.5,
          maxDrawdown: parseFloat(res.metrics.max_drawdown.toFixed(2)),
          sharpeRatio: parseFloat(res.metrics.sharpe.toFixed(2)),
        });
        setHasResults(true);
        reloadPlaybook();
        setSnackbar({ open: true, message: 'Backtest executed successfully & saved to Playbook!', severity: 'success' });
      } else {
        setSnackbar({ open: true, message: `Backtest failed: ${res.message || 'Unknown error'}`, severity: 'error' });
      }
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || err.message || err;
      setSnackbar({ open: true, message: `Backtest failed: ${errMsg}`, severity: 'error' });
    } finally {
      setIsBacktesting(false);
    }
  };

  // ── Save handler ──────────────────────────────────────────────────────────
  const handleSave = async () => {
    if (!selectedStrategies.length) {
      setSnackbar({ open: true, message: 'Please assemble a strategy before saving.', severity: 'warning' });
      return;
    }
    if (!strategyName.trim()) {
      setSnackbar({ open: true, message: 'Please provide a strategy name.', severity: 'warning' });
      return;
    }

    // Build indicators config mapping
    const consolidatedIndicators = {};
    selectedStrategies.forEach(s => {
      const playbookItem = playbookItems.find(p => p.id === s.id);
      if (playbookItem && playbookItem.indicators_config) {
        Object.entries(playbookItem.indicators_config).forEach(([indKey, indConfigList]) => {
          if (!consolidatedIndicators[indKey]) {
            consolidatedIndicators[indKey] = [];
          }
          indConfigList.forEach(item => {
            consolidatedIndicators[indKey].push(item);
          });
        });
      }
    });

    // Build Long and Short conditions
    const longConditions = [];
    const shortConditions = [];

    selectedStrategies.forEach(s => {
      const playbookItem = playbookItems.find(p => p.id === s.id);
      if (playbookItem && playbookItem.strategy_config) {
        const stratCfg = playbookItem.strategy_config;
        const itemLongConds = stratCfg.long?.conditions || [];
        const itemShortConds = stratCfg.short?.conditions || [];

        itemLongConds.forEach(c => {
          longConditions.push({
            ...c,
            persist_bars: s.persistBars || 0
          });
        });
        itemShortConds.forEach(c => {
          shortConditions.push({
            ...c,
            persist_bars: s.persistBars || 0
          });
        });
      }
    });

    selectedMlModels.forEach(m => {
      longConditions.push({
        left: `ml_signal_${m.id}`,
        operator: "==",
        right: 1,
        persist_bars: m.persistBars || 0
      });
      shortConditions.push({
        left: `ml_signal_${m.id}`,
        operator: "==",
        right: -1,
        persist_bars: m.persistBars || 0
      });
    });

    const consolidatedStrategy = {
      long: {
        rule: combineLogic,
        conditions: longConditions
      },
      short: {
        rule: combineLogic,
        conditions: shortConditions
      },
      stop_loss: parseFloat(stopLoss),
      take_profit: parseFloat(takeProfit),
      position_size_type: positionSizeType,
      position_size_value: parseFloat(positionSizeValue)
    };

    try {
      const payload = {
        strategy_name: strategyName.trim(),
        exchange: 'bybit',
        symbol: symbol,
        timeframe,
        indicators_config: consolidatedIndicators,
        strategy_config: consolidatedStrategy
      };

      const res = await saveStrategy(payload);
      if (res && res.success) {
        setSnackbar({ open: true, message: `Strategy "${strategyName.trim()}" saved successfully!`, severity: 'success' });
        setStrategyName('');
        setIsNameEdited(false);
        await reloadSavedStrategies();
        await reloadPlaybook();
      } else {
        setSnackbar({ open: true, message: `Failed to save strategy: ${res.message || 'Unknown error'}`, severity: 'error' });
      }
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || err.message || err;
      setSnackbar({ open: true, message: `Failed to save strategy: ${errMsg}`, severity: 'error' });
    }
  };

  const filteredPlaybook = playbookItems.filter((item) => {
    return item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.category.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const filteredMlModels = mlModelsList.filter(model => {
    const selectedTf = timeframe.toLowerCase();
    const modelTf = (model.timeframe || "").toLowerCase();
    return modelTf === selectedTf;
  });

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

  const workspaceCardSx = {
    ...cardSx,
    height: '560px',
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
              variant="contained"
              startIcon={isBacktesting ? <CircularProgress size={15} sx={{ color: COLORS.accentDark }} /> : <PlayArrowRoundedIcon />}
              onClick={handleRunBacktest}
              disabled={isBacktesting}
              sx={{
                fontWeight: 700, borderRadius: '12px',
                background: '#ffffff',
                color: COLORS.accentDark,
                boxShadow: '0 4px 16px rgba(0,0,0,0.22)',
                '&:hover': { background: 'rgba(255,255,255,0.9)', boxShadow: '0 6px 22px rgba(0,0,0,0.3)' },
              }}
            >
              {isBacktesting ? 'Running…' : 'Run Backtest'}
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
            onChange={(e) => {
              setStrategyName(e.target.value);
              setIsNameEdited(e.target.value !== '');
            }}
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
          <Box sx={workspaceCardSx}>
            <Box sx={{ p: '20px 20px 16px' }}>
              <SectionHeader step="01" title="Playbook Library" isDark={isDark} />
                {/* Search */}
                <Box sx={{ display: 'flex', gap: 1.25, width: '100%' }}>
                  <Box sx={{
                    display: 'flex', alignItems: 'center', gap: 1, flex: 1,
                    background: surfaceAlt,
                    border: `1px solid ${border}`,
                    borderRadius: '12px',
                    px: 1.5, py: 0.75,
                  }}>
                    <SearchRoundedIcon sx={{ fontSize: 16, color: theme.palette.text.secondary }} />
                    <input
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search…"
                      style={{
                        background: 'transparent', border: 'none', outline: 'none',
                        fontSize: '0.8125rem', color: theme.palette.text.primary,
                        width: '100%', fontFamily: 'inherit',
                      }}
                    />
                  </Box>
                </Box>
            </Box>

            <Box sx={{
              px: 1.5, pb: 2, display: 'flex', flexDirection: 'column', gap: 0.75, flex: 1, overflowY: 'auto',
              '&::-webkit-scrollbar': { width: '5px' },
              '&::-webkit-scrollbar-thumb': { background: isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.15)', borderRadius: '4px' }
            }}>
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
                {filteredPlaybook.length} / {playbookItems.length}
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
          <Box sx={workspaceCardSx}>
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

            <Box sx={{
              px: 2, pb: 2, flex: 1, display: 'flex', flexDirection: 'column', gap: 2, overflowY: 'auto',
              '&::-webkit-scrollbar': { width: '5px' },
              '&::-webkit-scrollbar-thumb': { background: isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.15)', borderRadius: '4px' }
            }}>

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
          <Box sx={workspaceCardSx}>
            <Box sx={{ p: '20px 20px 16px' }}>
              <SectionHeader step="03" title="Backtest Configuration" isDark={isDark} />
            </Box>

            <Box sx={{ px: 2, pb: 2.5, flex: 1, display: 'flex', flexDirection: 'column', gap: 2, minHeight: 0 }}>
              <Box sx={{
                flex: 1, display: 'flex', flexDirection: 'column', gap: 2, overflowY: 'auto', pr: 0.5,
                '&::-webkit-scrollbar': { width: '5px' },
                '&::-webkit-scrollbar-thumb': { background: isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.15)', borderRadius: '4px' }
              }}>

              {/* Symbol & Timeframe */}
              <Box>
                <FieldLabel>Market Settings</FieldLabel>
                <Grid container spacing={1.5}>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Symbol</Typography>
                    <Select value={symbol} onChange={(e) => setSymbol(e.target.value)} fullWidth size="small">
                      {['BTC', 'ETH', 'SOL', 'LTC', 'DOGE', 'MINA', 'SUI', 'ADA'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                    </Select>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography sx={{ fontSize: '0.6875rem', color: theme.palette.text.secondary, mb: 0.5 }}>Target Timeframe</Typography>
                    <Select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} fullWidth size="small">
                      {['1m', '5m', '15m', '30m', '1h', '4h', '1D', '1W'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
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
                { label: 'Sharpe Ratio', value: backtestResults.sharpeRatio.toFixed(2), color: backtestResults.sharpeRatio < 0 ? COLORS.pnlRed : (backtestResults.sharpeRatio > 0 ? COLORS.pnlGreen : theme.palette.text.primary) },
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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Select
                value={tableFilterSymbol}
                onChange={(e) => { setTableFilterSymbol(e.target.value); setPage(0); }}
                size="small"
                sx={{
                  height: 22,
                  fontSize: '0.625rem',
                  fontWeight: 800,
                  minWidth: 100,
                  color: theme.palette.text.secondary,
                  background: surfaceAlt,
                  borderRadius: '10px',
                  '.MuiOutlinedInput-notchedOutline': { borderColor: 'transparent' },
                  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'transparent' },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: 'transparent' },
                  '.MuiSelect-select': { py: 0, display: 'flex', alignItems: 'center' }
                }}
              >
                <MenuItem value="ALL" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>All Coins</MenuItem>
                <MenuItem value="BTC" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>BTC</MenuItem>
                <MenuItem value="ETH" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>ETH</MenuItem>
                <MenuItem value="SOL" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>SOL</MenuItem>
                <MenuItem value="LTC" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>LTC</MenuItem>
                <MenuItem value="DOGE" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>DOGE</MenuItem>
                <MenuItem value="SUI" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>SUI</MenuItem>
                <MenuItem value="ADA" sx={{ fontSize: '0.75rem', fontWeight: 700 }}>ADA</MenuItem>
              </Select>
              <Chip label={`${filteredTableBacktests.length} records`} size="small" sx={{ height: 22, fontSize: '0.625rem', fontWeight: 800, background: surfaceAlt, color: theme.palette.text.secondary }} />
            </Box>
          </Box>

          <TableContainer sx={{ borderRadius: '0 0 20px 20px' }}>
            <Table size="small" sx={{ tableLayout: 'fixed', width: '100%' }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ width: '4%', px: 1.5 }}>#</TableCell>
                  <TableCell
                    sx={{ width: '25%', px: 1.5, cursor: 'pointer', '&:hover': { color: COLORS.accent }, userSelect: 'none' }}
                    onClick={() => handleSort('name')}
                  >
                    {sortField === 'name' ? (sortOrder === 'asc' ? '↑ ' : '↓ ') : ''}Strategy Name
                  </TableCell>
                  <TableCell
                    sx={{ width: '8%', px: 1, cursor: 'pointer', '&:hover': { color: COLORS.accent }, userSelect: 'none' }}
                    onClick={() => handleSort('symbol')}
                  >
                    {sortField === 'symbol' ? (sortOrder === 'asc' ? '↑ ' : '↓ ') : ''}Symbol
                  </TableCell>
                  <TableCell
                    sx={{ width: '8%', px: 1, cursor: 'pointer', '&:hover': { color: COLORS.accent }, userSelect: 'none' }}
                    onClick={() => handleSort('timeframe')}
                  >
                    {sortField === 'timeframe' ? (sortOrder === 'asc' ? '↑ ' : '↓ ') : ''}TF
                  </TableCell>
                  <TableCell
                    sx={{ width: '11%', px: 1.5, cursor: 'pointer', '&:hover': { color: COLORS.accent }, userSelect: 'none' }}
                    align="right"
                    onClick={() => handleSort('totalReturn')}
                  >
                    {sortField === 'totalReturn' ? (sortOrder === 'asc' ? '↑ ' : '↓ ') : ''}Return
                  </TableCell>
                  <TableCell
                    sx={{ width: '11%', px: 1.5, cursor: 'pointer', '&:hover': { color: COLORS.accent }, userSelect: 'none' }}
                    align="right"
                    onClick={() => handleSort('winRate')}
                  >
                    {sortField === 'winRate' ? (sortOrder === 'asc' ? '↑ ' : '↓ ') : ''}Win Rate
                  </TableCell>
                  <TableCell
                    sx={{ width: '10%', px: 1.5, cursor: 'pointer', '&:hover': { color: COLORS.accent }, userSelect: 'none' }}
                    align="right"
                    onClick={() => handleSort('totalTrades')}
                  >
                    {sortField === 'totalTrades' ? (sortOrder === 'asc' ? '↑ ' : '↓ ') : ''}Trades
                  </TableCell>
                  <TableCell
                    sx={{ width: '10%', px: 1.5, cursor: 'pointer', '&:hover': { color: COLORS.accent }, userSelect: 'none' }}
                    align="right"
                    onClick={() => handleSort('runAt')}
                  >
                    {sortField === 'runAt' ? (sortOrder === 'asc' ? '↑ ' : '↓ ') : ''}Date
                  </TableCell>
                  <TableCell sx={{ width: '13%', px: 0.5 }} align="center">Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedBacktests.map((row, idx) => (
                  <TableRow key={row.id} hover>
                    <TableCell sx={{ color: theme.palette.text.secondary, fontSize: '0.75rem', px: 1.5 }}>
                      {startIndex + idx + 1}
                    </TableCell>
                    <TableCell sx={{ px: 1.5 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, lineHeight: 1.2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.name}</Typography>
                    </TableCell>
                    <TableCell sx={{ px: 1 }}>
                      <Chip label={row.symbol.replace('USDT', '').replace('/', '')} size="small" sx={{ height: 19, fontSize: '0.5625rem', fontWeight: 800, background: alpha(COLORS.accent, 0.14), color: COLORS.accent }} />
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
                    <TableCell align="right" sx={{ px: 1.5 }}>
                      <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: theme.palette.text.secondary }}>
                        {row.runAt}
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

          <TablePagination
            component="div"
            count={sortedBacktests.length}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[5, 10, 25]}
            sx={{
              borderTop: `1px solid ${border}`,
              color: theme.palette.text.secondary,
              '.MuiTablePagination-selectLabel, .MuiTablePagination-displayedRows': {
                fontSize: '0.75rem',
              },
              '.MuiTablePagination-select': {
                fontSize: '0.75rem',
                fontWeight: 700,
              },
              '.MuiTablePagination-actions svg': {
                color: theme.palette.text.primary,
              }
            }}
          />
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
