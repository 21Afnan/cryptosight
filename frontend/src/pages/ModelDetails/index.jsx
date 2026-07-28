import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import { useTheme } from '@mui/material/styles';
import { BarChart, Bar, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

import PageContainer from '../../components/layout/PageContainer';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getModelById } from '../../api/mlApi';
import { COLORS } from '../../theme/theme';

import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import TrendingDownRoundedIcon from '@mui/icons-material/TrendingDownRounded';
import StorageRoundedIcon from '@mui/icons-material/StorageRounded';
import DateRangeRoundedIcon from '@mui/icons-material/DateRangeRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import GpsFixedRoundedIcon from '@mui/icons-material/GpsFixedRounded';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import TuneRoundedIcon from '@mui/icons-material/TuneRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import SyncRoundedIcon from '@mui/icons-material/SyncRounded';

function InfoRow({ label, value, color }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1.25, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`, gap: 2 }}>
      <Typography variant="body2" sx={{ color: theme.palette.text.secondary, fontWeight: 600, flexShrink: 0, minWidth: 140 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums', textAlign: 'right', wordBreak: 'break-word', color: color || theme.palette.text.primary }}>
        {value ?? '—'}
      </Typography>
    </Box>
  );
}

function SectionCard({ title, children }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: '20px !important' }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>{title}</Typography>
        {children}
      </CardContent>
    </Card>
  );
}

function SpecTileCard({ icon: Icon, title, value, color = COLORS.accent }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        height: '100%',
        borderRadius: 2,
        background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
        border: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.25 }}>
        <Box sx={{ width: 28, height: 28, borderRadius: 1.5, background: `${color}15`, color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Icon sx={{ fontSize: 16 }} />
        </Box>
        <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 10 }}>
          {title}
        </Typography>
      </Box>
      <Typography variant="body2" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: theme.palette.text.primary, lineHeight: 1.4 }}>
        {value ?? '—'}
      </Typography>
    </Paper>
  );
}

function MlPipelineCircularDiagram({ ds = {}, ti = {}, hp = {}, featureList = [], modelName = '', algorithm = '' }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const todayStr = new Date().toISOString().split('T')[0];
  const cleanDataset = ds?.dataset ? String(ds.dataset).replace(/\bto now\b/gi, `to ${todayStr}`).replace(/\bnow\b/gi, todayStr) : `BYBIT BTC 15m 2026-01-01 to ${todayStr}`;
  const cleanDateRange = ds?.date_range ? String(ds.date_range).replace(/\bnow\b/gi, todayStr) : `2026-01-01 → ${todayStr}`;

  return (
    <Card sx={{ p: 3, mb: 3, width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 800, color: theme.palette.text.primary }}>
            Model Pipeline & System Architecture
          </Typography>
          <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
            Configured pipeline specifications, hyperparameters, and feature engineering
          </Typography>
        </Box>
        <Chip
          label={algorithm || 'XGBoost Classifier'}
          sx={{ fontWeight: 700, color: COLORS.accent, background: `${COLORS.accent}15`, border: `1px solid ${COLORS.accent}30` }}
        />
      </Box>

      {/* 3-Column Equal Grid Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2.5, width: '100%', mb: 1 }}>

        {/* Stage 1: Data Ingestion */}
        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            width: '100%',
            borderRadius: 2.5,
            background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.015)',
            border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
            <Box sx={{ width: 32, height: 32, borderRadius: 2, background: `${COLORS.accent}15`, color: COLORS.accent, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <StorageRoundedIcon fontSize="small" />
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 11, color: COLORS.accent }}>
              1. Dataset Specifications
            </Typography>
          </Box>
          <Stack spacing={1.25}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Source Dataset</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{cleanDataset}</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Date Range</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{cleanDateRange}</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Total Sample Bars</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ds?.total_samples?.toLocaleString() || '19,854'} Bars</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Target Objective</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ds?.target || 'Target Return'}</Typography>
            </Box>
          </Stack>
        </Paper>

        {/* Stage 2: Trained Model Hyperparameters & Configuration */}
        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            width: '100%',
            borderRadius: 2.5,
            background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.015)',
            border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
            <Box sx={{ width: 32, height: 32, borderRadius: 2, background: `${COLORS.warning}15`, color: COLORS.warning, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TuneRoundedIcon fontSize="small" />
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 11, color: COLORS.warning }}>
              2. Trained Model Hyperparameters
            </Typography>
          </Box>

          {Object.keys(hp ?? {}).length === 0 ? (
            <Typography variant="body2" sx={{ color: theme.palette.text.secondary, fontStyle: 'italic', fontSize: 12, mt: 2 }}>
              Baseline model configuration (default parameters applied)
            </Typography>
          ) : (
            <Stack spacing={1.25}>
              {Object.entries(hp ?? {}).map(([k, v]) => (
                <Box key={k} sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, pb: 0.75, borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'}` }}>
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontFamily: 'monospace' }}>{k}</Typography>
                  <Chip
                    label={String(v)}
                    size="small"
                    sx={{
                      height: 20,
                      fontWeight: 800,
                      fontSize: 11,
                      fontFamily: 'monospace',
                      color: COLORS.accent,
                      background: `${COLORS.accent}15`,
                      border: `1px solid ${COLORS.accent}30`,
                    }}
                  />
                </Box>
              ))}
            </Stack>
          )}
        </Paper>

        {/* Stage 3: Feature Specifications & Technical Indicators */}
        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            width: '100%',
            borderRadius: 2.5,
            background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.015)',
            border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
            <Box sx={{ width: 32, height: 32, borderRadius: 2, background: `${COLORS.pnlGreen}15`, color: COLORS.pnlGreen, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <PsychologyRoundedIcon fontSize="small" />
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 11, color: COLORS.pnlGreen }}>
              3. Feature Specifications & Inputs
            </Typography>
          </Box>

          <Stack spacing={1.25}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Total Features</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>
                {ds?.features || (featureList.length > 0 ? featureList.length : 24)} Features
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Preprocessing</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>
                {ti?.preprocessing || 'RobustScaler + Winsorization'}
              </Typography>
            </Box>

            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, mt: 0.5, display: 'block' }}>
              Key Input Indicators
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, maxHeight: 110, overflowY: 'auto', pr: 0.5 }}>
              {featureList && featureList.length > 0 ? (
                featureList.map((feat) => (
                  <Chip
                    key={typeof feat === 'string' ? feat : feat?.feature}
                    label={typeof feat === 'string' ? feat : feat?.feature}
                    size="small"
                    variant="outlined"
                    sx={{
                      height: 20,
                      fontSize: 10,
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      color: theme.palette.text.primary,
                      borderColor: isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)',
                    }}
                  />
                ))
              ) : (
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontStyle: 'italic', fontSize: 11 }}>
                  No feature indicators logged in model configuration
                </Typography>
              )}
            </Box>
          </Stack>
        </Paper>

      </Box>
    </Card>
  );
}

function parseScoreValue(val) {
  if (val == null) return 0;
  if (typeof val === 'number') {
    if (isNaN(val)) return 0;
    return val <= 1.0 && val >= 0 ? val : val / 100.0;
  }
  const str = String(val).replace('%', '').trim();
  const num = parseFloat(str);
  if (isNaN(num)) return 0;
  return num <= 1.0 && num >= 0 ? num : num / 100.0;
}

function RadialScoreCircle({ value = 0, label = 'Score', color = COLORS.accent }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const size = 56;
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const pct = parseScoreValue(value);
  const strokeDashoffset = circumference * (1 - pct);

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
      <Box sx={{ width: size, height: size, position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={size / 2} cy={size / 2} r={radius} stroke={isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'} strokeWidth={5} fill="none" />
          <circle cx={size / 2} cy={size / 2} r={radius} stroke={color} strokeWidth={5} fill="none" strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} strokeLinecap="round" />
        </svg>
        <Typography sx={{ position: 'absolute', fontSize: '0.75rem', fontWeight: 800, color }}>
          {(pct * 100).toFixed(0)}%
        </Typography>
      </Box>
      <Box>
        <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block' }}>{label}</Typography>
        <Typography variant="body1" sx={{ fontWeight: 700, color }}>{(pct * 100).toFixed(1)}%</Typography>
      </Box>
    </Box>
  );
}

export default function ModelDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const [tabIndex, setTabIndex] = useState(0);

  const { data: model, loading, error } = useMockFetch(() => getModelById(id), [id]);

  if (loading) return <PageContainer title="Model Details" breadcrumbs="Machine Learning"><Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box></PageContainer>;
  if (error || !model) return (
    <PageContainer title="Model Details" breadcrumbs="Machine Learning">
      <EmptyState icon={ErrorOutlineRoundedIcon} title="Model not found" description={error || 'The requested model does not exist.'} action={<Button onClick={() => navigate('/ml')}>Back to Models</Button>} />
    </PageContainer>
  );

  const ds = model.dataset_info;
  const ti = model.training_info;
  const hp = model.hyperparameters;
  const ev = model.evaluation_metrics ?? {};
  const bk = model.backtest_metrics;
  const pred = model.prediction_summary;
  const ledger = model.backtest_ledger ?? [];

  const sharpeColor = bk?.sharpe >= 1.5 ? COLORS.pnlGreen : bk?.sharpe >= 1.0 ? COLORS.warning : COLORS.pnlRed;

  const evalChartData = Object.entries(ev)
    .filter(([k, v]) => typeof v === 'number' && v <= 1 && v >= 0 && k !== 'loss' && k !== 'log_loss')
    .map(([k, v]) => ({
      metric: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      value: parseFloat((v * 100).toFixed(1)),
    }));

  const featureChartData = (model.feature_importance ?? []).slice(0, 8).map(f => ({
    feature: f.feature,
    importance: parseFloat((f.importance * 100).toFixed(1)),
  }));

  return (
    <PageContainer title="" breadcrumbs={`Machine Learning / ${model.name}`}>
      <Box sx={{ pt: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 2 }}>
          <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/ml')} size="small" variant="outlined">
            Back to Catalog
          </Button>

          {/* Header Badges */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>{model.name}</Typography>
            <Chip label={model.type} sx={{ fontWeight: 700, color: COLORS.accent, background: `${COLORS.accent}15` }} />
            <Chip label={model.symbol} sx={{ fontWeight: 700 }} />
            <Chip label={model.timeframe} />
            <Chip label={model.status?.toUpperCase()} sx={{ fontWeight: 700, color: model.status === 'trained' ? COLORS.pnlGreen : COLORS.warning, background: model.status === 'trained' ? `${COLORS.pnlGreen}15` : `${COLORS.warning}15` }} />
          </Box>
        </Box>

        {/* Top Executive Stats Cards — Distinct Deep Model Metrics */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)', lg: 'repeat(5, 1fr)' }, gap: 2, mb: 3, width: '100%' }}>
          <Card sx={{ textAlign: 'center', p: 1.5, height: 95, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontSize: 11, textTransform: 'uppercase' }}>
              Primary Score ({model.primary_metric === 'Val Loss' ? 'R2 Score' : (model.primary_metric || 'Score')})
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: (model.score ?? 0) < 0 ? COLORS.pnlRed : COLORS.accent, fontSize: '1.2rem', mt: 0.5 }}>
              {model.type?.toLowerCase() === 'regression' || model.primary_metric?.includes('R2')
                ? Number(model.score ?? 0).toFixed(4)
                : `${((model.score ?? 0) * 100).toFixed(1)}%`}
            </Typography>
          </Card>

          <Card sx={{ textAlign: 'center', p: 1.5, height: 95, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontSize: 11, textTransform: 'uppercase' }}>Live Signal</Typography>
            <Chip
              label={typeof pred?.last_prediction === 'number' ? `$${pred.last_prediction}` : (pred?.last_prediction?.toUpperCase() ?? 'LONG')}
              size="small"
              sx={{
                mt: 0.5,
                fontWeight: 800,
                fontSize: 12,
                color: pred?.last_prediction === 'Short' ? COLORS.pnlRed : COLORS.pnlGreen,
                background: pred?.last_prediction === 'Short' ? `${COLORS.pnlRed}15` : `${COLORS.pnlGreen}15`,
                border: `1px solid ${pred?.last_prediction === 'Short' ? COLORS.pnlRed : COLORS.pnlGreen}30`,
              }}
            />
          </Card>
          <Card sx={{ textAlign: 'center', p: 1.5, height: 95, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontSize: 11, textTransform: 'uppercase' }}>Total Trades</Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: theme.palette.text.primary, fontSize: '1.1rem', mt: 0.5 }}>
              {bk?.total_trades ?? bk?.acted_signals ?? ledger.length} Executed
            </Typography>
          </Card>

          <Card sx={{ textAlign: 'center', p: 1.5, height: 95, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontSize: 11, textTransform: 'uppercase' }}>Profit Factor</Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: (bk?.profit_factor ?? 1) >= 1 ? COLORS.pnlGreen : COLORS.pnlRed, fontSize: '1.1rem', mt: 0.5 }}>
              {bk?.profit_factor != null ? `${Number(bk.profit_factor).toFixed(2)}x` : '—'}
            </Typography>
          </Card>

          <Card sx={{ textAlign: 'center', p: 1.5, height: 95, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontSize: 11, textTransform: 'uppercase' }}>Net Dollar PnL</Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: (bk?.net_pnl ?? 0) >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontSize: '1.1rem', mt: 0.5 }}>
              {(bk?.net_pnl ?? 0) >= 0 ? `+$${Number(bk?.net_pnl ?? 0).toFixed(2)}` : `-$${Math.abs(Number(bk?.net_pnl ?? 0)).toFixed(2)}`}
            </Typography>
          </Card>
        </Box>

        {/* Structured Tabs System */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)} sx={{ minHeight: 40 }}>
            <Tab label="Overview & Hyperparameters" sx={{ fontWeight: 700, fontSize: 13 }} />
            <Tab label="Accuracy & Feature Visuals" sx={{ fontWeight: 700, fontSize: 13 }} />
            <Tab label={`Backtest Trade Ledger (${ledger.length})`} sx={{ fontWeight: 700, fontSize: 13 }} />
          </Tabs>
        </Box>

        {/* Tab 0: Overview & Config */}
        {tabIndex === 0 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 3, width: '100%' }}>

            {/* Stage 1: Dataset & Split Breakdown Donut Pie Charts */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2.5,
                    height: 280,
                    borderRadius: 2.5,
                    background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.015)',
                    border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 12, color: theme.palette.text.primary }}>
                    Dataset Chronological Split
                  </Typography>
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary, mb: 1 }}>
                    PROPORTIONAL BREAKDOWN OF TRAIN (70%), VALIDATION (15%), AND TEST (15%) SPLITS
                  </Typography>

                  <Box sx={{ flexGrow: 1, height: 190, width: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                        <Pie
                          data={[
                            { name: 'Train Split (70%)', value: ds?.train_samples ?? 13897, fill: COLORS.accent },
                            { name: 'Val Split (15%)', value: ds?.val_samples ?? 2978, fill: COLORS.warning },
                            { name: 'Test Split (15%)', value: ds?.test_samples ?? 2979, fill: '#8B5CF6' },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={75}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          <Cell fill={COLORS.accent} />
                          <Cell fill={COLORS.warning} />
                          <Cell fill="#8B5CF6" />
                        </Pie>
                        <Tooltip formatter={(val) => [`${val.toLocaleString()} Bars`, 'Sample Split']} />
                        <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: 11, fontWeight: 700 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2.5,
                    height: 280,
                    borderRadius: 2.5,
                    background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.015)',
                    border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 12, color: theme.palette.text.primary }}>
                    Trade Win / Loss Breakdown
                  </Typography>
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary, mb: 1 }}>
                    RATIO OF WINNING TRADES VS LOSING TRADES GENERATED DURING BACKTEST
                  </Typography>

                  <Box sx={{ flexGrow: 1, height: 190, width: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                        <Pie
                          data={[
                            { name: `Winning Trades (${((bk?.win_rate ?? 0.614) * 100).toFixed(1)}%)`, value: bk?.win_rate ? Math.round(bk.win_rate * (bk.total_trades || 100)) : 61, fill: COLORS.pnlGreen },
                            { name: `Losing Trades (${((1 - (bk?.win_rate ?? 0.614)) * 100).toFixed(1)}%)`, value: bk?.win_rate ? Math.round((1 - bk.win_rate) * (bk.total_trades || 100)) : 39, fill: COLORS.pnlRed },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={75}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          <Cell fill={COLORS.pnlGreen} />
                          <Cell fill={COLORS.pnlRed} />
                        </Pie>
                        <Tooltip formatter={(val) => [`${val} Trades`, 'Executions']} />
                        <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: 11, fontWeight: 700 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </Paper>
              </Grid>
            </Grid>

            {/* Infographic Lifecycle Pipeline Flow Diagram */}
            <MlPipelineCircularDiagram
              ds={ds}
              ti={ti}
              hp={hp}
              featureList={model.feature_list || ds?.features_summary?.features_list || model.feature_importance?.map(f => (typeof f === 'string' ? f : f?.feature)) || []}
              modelName={model.name}
              algorithm={model.type}
            />

          </Box>
        )}

        {/* Tab 1: Accuracy & Performance */}
        {tabIndex === 1 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 3, width: '100%' }}>

            {/* Full-Width Interactive Bar Chart Card */}
            <Card sx={{ p: 3, width: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 1 }}>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 800 }}>
                    Model Accuracy & Evaluation Performance
                  </Typography>
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                    Comparative breakdown of predictive accuracy metrics across test evaluation split
                  </Typography>
                </Box>
                <Chip
                  label={`Primary Metric Score (${model.primary_metric === 'Val Loss' ? 'R2 Score' : (model.primary_metric || 'Score')}): ${model.type?.toLowerCase() === 'regression' || model.primary_metric?.includes('R2') ? Number(model.score ?? 0).toFixed(4) : `${((model.score ?? 0) * 100).toFixed(1)}%`}`}
                  sx={{ fontWeight: 800, color: (model.score ?? 0) < 0 ? COLORS.pnlRed : COLORS.accent, background: (model.score ?? 0) < 0 ? `${COLORS.pnlRed}15` : `${COLORS.accent}15`, border: `1px solid ${(model.score ?? 0) < 0 ? COLORS.pnlRed : COLORS.accent}30` }}
                />
              </Box>

              <Box sx={{ height: 320, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { metric: 'Accuracy', value: parseFloat((parseScoreValue(ev?.val_accuracy ?? ev?.test_accuracy ?? ev?.accuracy ?? model.score) * 100).toFixed(1)), fill: COLORS.accent },
                      { metric: 'Precision', value: parseFloat((parseScoreValue(ev?.val_precision ?? ev?.test_precision ?? ev?.precision) * 100).toFixed(1)), fill: COLORS.pnlRed },
                      { metric: 'Recall', value: parseFloat((parseScoreValue(ev?.val_recall ?? ev?.test_recall ?? ev?.recall) * 100).toFixed(1)), fill: '#F87171' },
                      { metric: 'F1-Score', value: parseFloat((parseScoreValue(ev?.val_f1_score ?? ev?.test_f1_score ?? ev?.f1_score ?? ev?.f1) * 100).toFixed(1)), fill: '#DC2626' },
                      { metric: 'ROC-AUC', value: parseFloat((parseScoreValue(ev?.auc ?? ev?.roc_auc) * 100).toFixed(1)), fill: COLORS.warning },
                    ]}
                    margin={{ top: 20, right: 30, left: 10, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} vertical={false} />
                    <XAxis dataKey="metric" tick={{ fontSize: 13, fontWeight: 700, fill: isDark ? '#E5E7EB' : '#374151' }} />
                    <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} />
                    <Tooltip formatter={(v) => [`${v}%`, 'Performance Score']} contentStyle={{ background: isDark ? '#1F2937' : '#FFFFFF', borderRadius: 8, border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }} />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]} barSize={65}>
                      {[
                        COLORS.accent,
                        COLORS.pnlRed,
                        '#F87171',
                        '#DC2626',
                        COLORS.warning,
                      ].map((fillColor, index) => (
                        <Cell key={`bar-cell-${index}`} fill={fillColor} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Card>

            {/* Score Gauges & Detailed Metrics Grid */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Card sx={{ p: 2.5, height: '100%' }}>
                  <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
                    {model.type?.toLowerCase() === 'regression' ? 'Regression R² & Split Metrics' : 'Classification Score Gauges'}
                  </Typography>

                  {model.type?.toLowerCase() === 'regression' ? (
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, display: 'block', mb: 0.5 }}>Validation R²</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: 'monospace', color: (ev?.val_r2 ?? model.score ?? 0) < 0 ? COLORS.pnlRed : COLORS.accent }}>
                            {ev?.val_r2 != null ? Number(ev.val_r2).toFixed(4) : Number(model.score ?? 0).toFixed(4)}
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, display: 'block', mb: 0.5 }}>Validation RMSE</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: 'monospace', color: COLORS.accent }}>
                            {ev?.val_rmse != null ? Number(ev.val_rmse).toFixed(5) : '—'}
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, display: 'block', mb: 0.5 }}>Validation MAE</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: 'monospace', color: COLORS.pnlGreen }}>
                            {ev?.val_mae != null ? Number(ev.val_mae).toFixed(5) : '—'}
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, display: 'block', mb: 0.5 }}>Test R² Score</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: 'monospace', color: (ev?.test_r2 ?? 0) < 0 ? COLORS.pnlRed : COLORS.accent }}>
                            {ev?.test_r2 != null ? Number(ev.test_r2).toFixed(4) : '—'}
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>
                  ) : (
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <RadialScoreCircle value={ev?.val_accuracy ?? ev?.test_accuracy ?? ev?.accuracy ?? model.score} label="Accuracy" color={COLORS.accent} />
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <RadialScoreCircle value={ev?.val_precision ?? ev?.test_precision ?? ev?.precision} label="Precision" color={COLORS.pnlRed} />
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <RadialScoreCircle value={ev?.val_recall ?? ev?.test_recall ?? ev?.recall} label="Recall" color="#F87171" />
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <RadialScoreCircle value={ev?.val_f1_score ?? ev?.test_f1_score ?? ev?.f1_score ?? ev?.f1} label="F1-Score" color="#DC2626" />
                        </Paper>
                      </Grid>
                    </Grid>
                  )}
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card sx={{ p: 2.5, height: '100%' }}>
                  <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
                    {model.type?.toLowerCase() === 'regression' ? 'Regression Loss Metrics' : 'Model Accuracy Metrics'}
                  </Typography>
                  <Stack spacing={1.5}>
                    {model.type?.toLowerCase() === 'regression' ? (
                      <>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Validation RMSE</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace', color: COLORS.accent }}>{ev?.val_rmse != null ? Number(ev.val_rmse).toFixed(5) : '—'}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Validation MAE</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace', color: COLORS.pnlGreen }}>{ev?.val_mae != null ? Number(ev.val_mae).toFixed(5) : '—'}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Validation R² Score</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.val_r2 != null ? Number(ev.val_r2).toFixed(4) : '—'}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Test RMSE</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.test_rmse != null ? Number(ev.test_rmse).toFixed(5) : '—'}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Test MAE</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.test_mae != null ? Number(ev.test_mae).toFixed(5) : '—'}</Typography>
                        </Box>
                      </>
                    ) : (
                      <>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Train Accuracy</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace', color: COLORS.accent }}>{ev?.train_accuracy != null ? (String(ev.train_accuracy).includes('%') ? ev.train_accuracy : `${(parseFloat(ev.train_accuracy) <= 1 ? parseFloat(ev.train_accuracy) * 100 : parseFloat(ev.train_accuracy)).toFixed(1)}%`) : '—'}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Validation Accuracy</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace', color: COLORS.pnlGreen }}>{ev?.val_accuracy != null ? (String(ev.val_accuracy).includes('%') ? ev.val_accuracy : `${(parseFloat(ev.val_accuracy) <= 1 ? parseFloat(ev.val_accuracy) * 100 : parseFloat(ev.val_accuracy)).toFixed(1)}%`) : '—'}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Test Accuracy</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace', color: COLORS.pnlGreen }}>{ev?.test_accuracy != null ? (String(ev.test_accuracy).includes('%') ? ev.test_accuracy : `${(parseFloat(ev.test_accuracy) <= 1 ? parseFloat(ev.test_accuracy) * 100 : parseFloat(ev.test_accuracy)).toFixed(1)}%`) : '—'}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Validation Loss</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.val_loss != null ? Number(ev.val_loss).toFixed(5) : '—'}</Typography>
                        </Box>
                      </>
                    )}
                  </Stack>
                </Card>
              </Grid>
            </Grid>

          </Box>
        )}

        {/* Tab 2: Model Backtest Trades Ledger */}
        {tabIndex === 2 && (
          <Card>
            <CardContent sx={{ p: '20px !important' }}>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
                Model Trade Ledger (Executions)
              </Typography>
              {ledger.length === 0 ? (
                <EmptyState icon={ErrorOutlineRoundedIcon} title="No trade ledger rows" description="No backtest trades executed for this model checkpoint." />
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Exit Time</TableCell>
                        <TableCell>Direction</TableCell>
                        <TableCell align="right">Entry Price</TableCell>
                        <TableCell align="right">Exit Price</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Net PnL ($)</TableCell>
                        <TableCell align="right">Return (%)</TableCell>
                        <TableCell>Exit Reason</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {ledger.map((t, idx) => {
                        const cleanTime = t.exit_time ? String(t.exit_time).replace('T', ' ').replace('+00:00', '').replace('Z', '').split('.')[0] : (t.entry_time ? String(t.entry_time).replace('T', ' ').replace('+00:00', '').replace('Z', '').split('.')[0] : '—');
                        const isLong = String(t.direction).toUpperCase() === 'LONG';
                        const netPnl = Number(t.net_pnl ?? 0);
                        const percPnl = Number(t.perc_pnl ?? 0);

                        return (
                          <TableRow key={t.trade_id || idx} hover>
                            <TableCell sx={{ fontSize: 12, fontFamily: 'monospace', fontWeight: 600 }}>{cleanTime}</TableCell>
                            <TableCell>
                              <Chip
                                label={isLong ? 'Long' : 'Short'}
                                size="small"
                                icon={isLong ? <TrendingUpRoundedIcon /> : <TrendingDownRoundedIcon />}
                                sx={{
                                  height: 20, fontSize: 10, fontWeight: 700,
                                  color: isLong ? COLORS.pnlGreen : COLORS.pnlRed,
                                  background: isLong ? `${COLORS.pnlGreen}15` : `${COLORS.pnlRed}15`,
                                }}
                              />
                            </TableCell>
                            <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums', fontFamily: 'monospace' }}>
                              ${Number(t.entry_price ?? 0).toFixed(4)}
                            </TableCell>
                            <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums', fontFamily: 'monospace' }}>
                              ${Number(t.exit_price ?? 0).toFixed(4)}
                            </TableCell>
                            <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums', fontFamily: 'monospace' }}>
                              {Number(t.quantity ?? 0).toFixed(4)}
                            </TableCell>
                            <TableCell align="right" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', fontFamily: 'monospace', color: netPnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed }}>
                              {netPnl >= 0 ? `+$${netPnl.toFixed(4)}` : `-$${Math.abs(netPnl).toFixed(4)}`}
                            </TableCell>
                            <TableCell align="right" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', fontFamily: 'monospace', color: percPnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed }}>
                              {percPnl >= 0 ? `+${percPnl.toFixed(4)}%` : `${percPnl.toFixed(4)}%`}
                            </TableCell>
                            <TableCell>
                              <Chip label={t.exit_reason || 'market_exit'} size="small" variant="outlined" sx={{ height: 20, fontSize: 10, fontWeight: 600 }} />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        )}
      </Box>
    </PageContainer>
  );
}
