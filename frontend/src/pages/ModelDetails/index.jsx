import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import { useTheme } from '@mui/material/styles';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

import PageContainer from '../../components/layout/PageContainer';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getModelById } from '../../api/mlApi';
import { COLORS } from '../../theme/theme';

import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

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

// Compact radial score indicator for Score & Confidence
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

  const formatScore = (m) => m.primary_metric === 'Val Loss' ? m.score?.toFixed(5) : `${(m.score * 100).toFixed(1)}%`;

  // Sharpe color logic
  const sharpeColor = bk?.sharpe >= 1.5 ? COLORS.pnlGreen : bk?.sharpe >= 1.0 ? COLORS.warning : COLORS.pnlRed;

  // Prepare evaluation metrics for recharts horizontal bar chart (metrics 0-1)
  const evalChartData = Object.entries(ev)
    .filter(([k, v]) => typeof v === 'number' && v <= 1 && v >= 0 && k !== 'loss' && k !== 'log_loss')
    .map(([k, v]) => ({
      metric: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      value: parseFloat((v * 100).toFixed(1)),
    }));

  const CustomChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <Box sx={{ background: isDark ? COLORS.darkSurface : COLORS.lightSurface, border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`, borderRadius: 2, p: 1.25, fontSize: 12 }}>
        <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>{label}</Typography>
        <Typography variant="body2" sx={{ fontWeight: 700, color: COLORS.accent }}>{payload[0].value}%</Typography>
      </Box>
    );
  };

  return (
    <PageContainer title={model.name} breadcrumbs="Machine Learning">
      <Box sx={{ pt: 3 }}>
        <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate('/ml')} size="small" sx={{ mb: 2 }}>Back</Button>

        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Typography variant="h2" sx={{ fontWeight: 700 }}>{model.name}</Typography>
          <Chip label={model.type} sx={{ color: COLORS.accent, background: `${COLORS.accent}15` }} />
          <Chip label={model.symbol} />
          <Chip label={model.timeframe} />
          <Chip label={model.status} sx={{ color: model.status === 'trained' ? COLORS.pnlGreen : COLORS.warning, background: model.status === 'trained' ? `${COLORS.pnlGreen}15` : `${COLORS.warning}15` }} />
        </Box>

        {/* Score + Prediction + Visual Gauges */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {/* Visual Gauge Pill for Score */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RadialScoreCircle value={model.score ?? 0} label={`Score (${model.primary_metric})`} color={COLORS.accent} />
            </Card>
          </Grid>
          {/* Visual Gauge Pill for Confidence */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RadialScoreCircle value={pred?.confidence ?? 0} label="Prediction Confidence" color={COLORS.pnlGreen} />
            </Card>
          </Grid>

          {[
            { label: 'Last Prediction', value: typeof pred?.last_prediction === 'number' ? `$${pred.last_prediction?.toLocaleString()}` : pred?.last_prediction },
            { label: 'Backtest Sharpe', value: bk?.sharpe?.toFixed(2), color: sharpeColor },
            { label: 'Backtest Win Rate', value: bk?.win_rate != null ? `${(bk.win_rate * 100).toFixed(1)}%` : '—', color: COLORS.pnlGreen },
            { label: 'Max Drawdown', value: bk?.max_drawdown != null ? `${(bk.max_drawdown * 100).toFixed(1)}%` : '—', color: COLORS.pnlRed },
            { label: 'Net PnL %', value: bk?.net_pnl_pct != null ? `${(bk.net_pnl_pct * 100).toFixed(1)}%` : '—', color: COLORS.pnlGreen },
          ].map(({ label, value, color }) => (
            <Grid item xs={6} sm={4} md={2} lg={1.2} key={label}>
              <Card sx={{ textAlign: 'center', p: 1.5, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>{label}</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: color || theme.palette.text.primary, fontSize: '0.95rem', mt: 0.5 }}>{value ?? '—'}</Typography>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Config cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <SectionCard title="Dataset Info">
              <InfoRow label="Dataset" value={ds?.dataset} />
              <InfoRow label="Date Range" value={ds?.date_range} />
              <InfoRow label="Total Samples" value={ds?.total_samples?.toLocaleString()} />
              <InfoRow label="Features" value={ds?.features} />
              <InfoRow label="Target" value={ds?.target} />
              <InfoRow label="Train / Val / Test" value={`${(ds?.train_split * 100).toFixed(0)}% / ${(ds?.val_split * 100).toFixed(0)}% / ${(ds?.test_split * 100).toFixed(0)}%`} />
              <InfoRow label="Train Samples" value={ds?.train_samples?.toLocaleString()} />
              <InfoRow label="Val Samples" value={ds?.val_samples?.toLocaleString()} />
              <InfoRow label="Test Samples" value={ds?.test_samples?.toLocaleString()} />
            </SectionCard>
          </Grid>

          <Grid item xs={12} md={4}>
            <SectionCard title="Training Config">
              <InfoRow label="Algorithm" value={ti?.algorithm} />
              <InfoRow label="Preprocessing" value={ti?.preprocessing} />
              <InfoRow label="Feature Engineering" value={ti?.feature_engineering} />
              <InfoRow label="Scaling" value={ti?.scaling} />
              <InfoRow label="Stationarity" value={ti?.stationarity} />
              <InfoRow label="Early Stopping" value={ti?.early_stopping ? 'Yes' : 'No'} />
              <InfoRow label="CV Folds" value={ti?.cv_folds} />
              {ti?.epochs && <InfoRow label="Epochs Trained" value={hp?.epochs_trained ?? ti?.epochs} />}
              {ti?.batch_size && <InfoRow label="Batch Size" value={ti?.batch_size} />}
            </SectionCard>
          </Grid>

          {/* Evaluation Metrics Card with Recharts Horizontal Bar Chart Visual */}
          <Grid item xs={12} md={4}>
            <SectionCard title="Evaluation Metrics & Performance">
              {evalChartData.length > 0 && (
                <Box sx={{ mb: 2, height: 160 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={evalChartData} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 60 }} barSize={12}>
                      <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} horizontal={false} />
                      <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="metric" tick={{ fontSize: 10, fill: isDark ? '#A0AEC0' : '#374151' }} axisLine={false} tickLine={false} width={55} />
                      <Tooltip content={<CustomChartTooltip />} />
                      <Bar dataKey="value" radius={[0, 3, 3, 0]}>
                        {evalChartData.map((_, idx) => (
                          <Cell key={idx} fill={COLORS.accent} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              )}

              {Object.entries(ev).filter(([k]) => k !== 'confusion_matrix' && k !== 'per_class').map(([k, v]) => (
                <InfoRow key={k} label={k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} value={typeof v === 'number' ? (v < 0.01 ? v.toFixed(5) : (v <= 1 ? `${(v * 100).toFixed(1)}%` : v.toFixed(4))) : String(v)} />
              ))}
            </SectionCard>
          </Grid>
        </Grid>

        {/* Hyperparameters */}
        <Card>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Hyperparameters</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {Object.entries(hp ?? {}).map(([k, v]) => (
                <Chip
                  key={k}
                  label={`${k}: ${v}`}
                  size="small"
                  sx={{ fontSize: 11, fontFamily: 'monospace', background: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)', border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      </Box>
    </PageContainer>
  );
}
