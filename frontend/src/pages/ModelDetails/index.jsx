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

function MlPipelineCircularDiagram({ ds, ti, hp, modelName, algorithm }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  return (
    <Card sx={{ p: 3, width: '100%', borderRadius: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 800, color: theme.palette.text.primary }}>
            Model Pipeline & System Architecture
          </Typography>
          <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
            Configured pipeline specifications and hyperparameters
          </Typography>
        </Box>
        <Chip
          label={algorithm || 'XGBoost Classifier'}
          sx={{ fontWeight: 700, color: COLORS.accent, background: `${COLORS.accent}15`, border: `1px solid ${COLORS.accent}30` }}
        />
      </Box>

      {/* 2-Column Spacious Stepped Process Cards */}
      <Grid container spacing={2.5} sx={{ mb: 2.5 }}>

        {/* Stage 1: Data Ingestion */}
        <Grid item xs={12} md={6}>
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              height: '100%',
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
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ds?.dataset || 'Binance BTCUSDT 4H'}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Date Range</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ds?.date_range || '2023-01-01 → 2025-06-01'}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Total Sample Bars</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ds?.total_samples?.toLocaleString() || '5,490'} Bars</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Target Objective</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ds?.target || '3-Class Direction'}</Typography>
              </Box>
            </Stack>
          </Paper>
        </Grid>

        {/* Stage 2: Feature Engineering & Preprocessing */}
        <Grid item xs={12} md={6}>
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              height: '100%',
              borderRadius: 2.5,
              background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.015)',
              border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
              <Box sx={{ width: 32, height: 32, borderRadius: 2, background: `${COLORS.pnlGreen}15`, color: COLORS.pnlGreen, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <TuneRoundedIcon fontSize="small" />
              </Box>
              <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 11, color: COLORS.pnlGreen }}>
                2. Preprocessing & Features
              </Typography>
            </Box>
            <Stack spacing={1.25}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Scaling Method</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ti?.scaling || 'RobustScaler + Winsorization'}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Feature Count</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ds?.features || 42} Technical Indicators</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Stationarity Test</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ti?.stationarity || 'ADF + KPSS Confirmed'}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Feature Engineering</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, textAlign: 'right' }}>{ti?.feature_engineering || 'Lag-1, Log Returns, Rolling Z-Scores'}</Typography>
              </Box>
            </Stack>
          </Paper>
        </Grid>

      </Grid>

      {/* Trained Model Hyperparameters Code Badges Bar */}
      <Box sx={{ p: 2.5, borderRadius: 2.5, background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.015)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
        <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 11, color: COLORS.warning, mb: 1.5 }}>
          3. Hyperparameters & Model Configuration
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {Object.entries(hp ?? {}).map(([k, v]) => (
            <Chip
              key={k}
              label={`${k}: ${v}`}
              size="small"
              sx={{
                fontWeight: 700,
                fontSize: 11,
                fontFamily: 'monospace',
                color: isDark ? '#E5E7EB' : '#374151',
                background: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)',
                border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
              }}
            />
          ))}
        </Box>
      </Box>

    </Card>
  );
}

function RadialScoreCircle({ value = 0, label = 'Score', color = COLORS.accent }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const size = 56;
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(1, Math.max(0, value));
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
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)', lg: 'repeat(6, 1fr)' }, gap: 2, mb: 3, width: '100%' }}>
          <Card sx={{ p: 1.5, height: 95, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <RadialScoreCircle value={model.score ?? 0} label={`Score (${model.primary_metric})`} color={COLORS.accent} />
          </Card>

          <Card sx={{ p: 1.5, height: 95, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <RadialScoreCircle value={pred?.confidence ?? 0.712} label="Prediction Confidence" color={COLORS.pnlGreen} />
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
              {bk?.acted_signals ?? bk?.total_signals ?? ledger.length ?? 287} Executed
            </Typography>
          </Card>

          <Card sx={{ textAlign: 'center', p: 1.5, height: 95, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontSize: 11, textTransform: 'uppercase' }}>Profit Factor</Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: COLORS.pnlGreen, fontSize: '1.1rem', mt: 0.5 }}>
              {bk?.profit_factor ? `${bk.profit_factor.toFixed(2)}x` : '1.85x'}
            </Typography>
          </Card>

          <Card sx={{ textAlign: 'center', p: 1.5, height: 95, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, fontSize: 11, textTransform: 'uppercase' }}>Net Dollar PnL</Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: COLORS.pnlGreen, fontSize: '1.1rem', mt: 0.5 }}>
              +${bk?.net_pnl?.toLocaleString() ?? '2,830.40'}
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

            {/* Visual Donut Pie Charts Section */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card sx={{ p: 2.5, height: '100%' }}>
                  <Typography variant="h5" sx={{ mb: 1, fontWeight: 700 }}>Dataset Chronological Split</Typography>
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary, mb: 2, display: 'block' }}>
                    Proportional breakdown of Train (70%), Validation (15%), and Test (15%) splits
                  </Typography>
                  <Box sx={{ height: 210, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Train Split (70%)', value: ds?.train_samples ?? 3843, fill: COLORS.accent },
                            { name: 'Val Split (15%)', value: ds?.val_samples ?? 823, fill: COLORS.warning },
                            { name: 'Test Split (15%)', value: ds?.test_samples ?? 824, fill: '#8B5CF6' },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={80}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          <Cell fill={COLORS.accent} />
                          <Cell fill={COLORS.warning} />
                          <Cell fill="#8B5CF6" />
                        </Pie>
                        <Tooltip formatter={(v) => [`${v?.toLocaleString()} samples`, 'Count']} />
                        <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card sx={{ p: 2.5, height: '100%' }}>
                  <Typography variant="h5" sx={{ mb: 1, fontWeight: 700 }}>Trade Win / Loss Breakdown</Typography>
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary, mb: 2, display: 'block' }}>
                    Ratio of winning trades vs losing trades generated during backtest
                  </Typography>
                  <Box sx={{ height: 210, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: `Winning Trades (${((bk?.win_rate ?? 0.614) * 100).toFixed(1)}%)`, value: Math.round((bk?.acted_signals ?? 287) * (bk?.win_rate ?? 0.614)), fill: COLORS.pnlGreen },
                            { name: `Losing Trades (${((1 - (bk?.win_rate ?? 0.614)) * 100).toFixed(1)}%)`, value: Math.round((bk?.acted_signals ?? 287) * (1 - (bk?.win_rate ?? 0.614))), fill: COLORS.pnlRed },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={80}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          <Cell fill={COLORS.pnlGreen} />
                          <Cell fill={COLORS.pnlRed} />
                        </Pie>
                        <Tooltip formatter={(v) => [`${v} trades`, 'Trades']} />
                        <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </Card>
              </Grid>
            </Grid>

            {/* Infographic Lifecycle Pipeline Flow Diagram */}
            <MlPipelineCircularDiagram ds={ds} ti={ti} hp={hp} modelName={model.name} algorithm={model.type} />

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
                  label={`Primary Accuracy: ${((ev?.accuracy ?? 0.7736) * 100).toFixed(1)}%`}
                  sx={{ fontWeight: 800, color: COLORS.accent, background: `${COLORS.accent}15`, border: `1px solid ${COLORS.accent}30` }}
                />
              </Box>

              <Box sx={{ height: 320, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { metric: 'Accuracy', value: parseFloat(((ev?.accuracy ?? 0.7736) * 100).toFixed(1)), fill: COLORS.accent },
                      { metric: 'Precision', value: parseFloat(((ev?.precision ?? 0.712) * 100).toFixed(1)), fill: COLORS.pnlRed },
                      { metric: 'Recall', value: parseFloat(((ev?.recall ?? 0.685) * 100).toFixed(1)), fill: '#F87171' },
                      { metric: 'F1-Score', value: parseFloat(((ev?.f1_score ?? ev?.f1 ?? 0.698) * 100).toFixed(1)), fill: '#DC2626' },
                      { metric: 'ROC-AUC', value: parseFloat(((ev?.auc ?? ev?.roc_auc ?? 0.824) * 100).toFixed(1)), fill: COLORS.warning },
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

            {/* Radial Score Rings & Detailed Metrics Grid */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Card sx={{ p: 2.5, height: '100%' }}>
                  <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Classification Score Gauges</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                        <RadialScoreCircle value={ev?.accuracy ?? 0.7736} label="Accuracy" color={COLORS.accent} />
                      </Paper>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                        <RadialScoreCircle value={ev?.precision ?? 0.712} label="Precision" color={COLORS.pnlRed} />
                      </Paper>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                        <RadialScoreCircle value={ev?.recall ?? 0.685} label="Recall" color="#F87171" />
                      </Paper>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Paper elevation={0} sx={{ p: 2, textAlign: 'center', borderRadius: 2, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                        <RadialScoreCircle value={ev?.f1_score ?? ev?.f1 ?? 0.698} label="F1-Score" color="#DC2626" />
                      </Paper>
                    </Grid>
                  </Grid>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card sx={{ p: 2.5, height: '100%' }}>
                  <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Loss & Variance Metrics</Typography>
                  <Stack spacing={1.5}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                      <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Validation Loss</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.val_loss?.toFixed(5) ?? '0.00182'}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                      <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Test Loss</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.test_loss?.toFixed(5) ?? '0.00214'}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', pb: 1, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                      <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Mean Absolute Error (MAE)</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.mae?.toFixed(2) ?? '312.40'}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>Root Mean Sq Error (RMSE)</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 800, fontFamily: 'monospace' }}>{ev?.rmse?.toFixed(2) ?? '487.20'}</Typography>
                    </Box>
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
                        <TableCell>Signal</TableCell>
                        <TableCell align="right">Entry Price</TableCell>
                        <TableCell align="right">Exit Price</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Net PnL ($)</TableCell>
                        <TableCell align="right">Return (%)</TableCell>
                        <TableCell>Exit Reason</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {ledger.map((t, idx) => (
                        <TableRow key={t.trade_id || idx} hover>
                          <TableCell sx={{ fontSize: 12 }}>{t.exit_time}</TableCell>
                          <TableCell>
                            <Chip
                              label={t.direction}
                              size="small"
                              icon={t.direction === 'LONG' ? <TrendingUpRoundedIcon /> : <TrendingDownRoundedIcon />}
                              sx={{
                                height: 20, fontSize: 10, fontWeight: 700,
                                color: t.direction === 'LONG' ? COLORS.pnlGreen : COLORS.pnlRed,
                                background: t.direction === 'LONG' ? `${COLORS.pnlGreen}15` : `${COLORS.pnlRed}15`,
                              }}
                            />
                          </TableCell>
                          <TableCell>{t.signal}</TableCell>
                          <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums' }}>${t.entry_price?.toLocaleString()}</TableCell>
                          <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums' }}>${t.exit_price?.toLocaleString()}</TableCell>
                          <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums' }}>{t.quantity}</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: t.net_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed }}>
                            {t.net_pnl >= 0 ? `+$${t.net_pnl?.toFixed(2)}` : `-$${Math.abs(t.net_pnl)?.toFixed(2)}`}
                          </TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: t.perc_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed }}>
                            {t.perc_pnl >= 0 ? `+${t.perc_pnl}%` : `${t.perc_pnl}%`}
                          </TableCell>
                          <TableCell>
                            <Chip label={t.exit_reason} size="small" variant="outlined" sx={{ height: 20, fontSize: 10 }} />
                          </TableCell>
                          <TableCell>
                            <Chip label={t.status} size="small" sx={{ height: 20, fontSize: 10, background: 'rgba(255,255,255,0.05)' }} />
                          </TableCell>
                        </TableRow>
                      ))}
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
