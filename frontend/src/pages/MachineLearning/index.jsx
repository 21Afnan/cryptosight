import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
import TablePagination from '@mui/material/TablePagination';
import Stack from '@mui/material/Stack';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import SearchBar from '../../components/ui/SearchBar';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getModels } from '../../api/mlApi';
import { COLORS } from '../../theme/theme';

import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';

const MODEL_TYPE_COLORS = {
  XGBoost: COLORS.accent,
  LightGBM: COLORS.pnlGreen,
  RandomForest: COLORS.warning,
  LSTM: '#8B5CF6',
  LinearRegression: '#EC4899',
};

function ExecutiveKpiCard({ title, value, subtitle, icon: Icon, color = COLORS.accent }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  return (
    <Card sx={{ height: 130, width: '100%', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ p: '16px 20px !important', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 11 }}>
            {title}
          </Typography>
          <Box sx={{ width: 34, height: 34, borderRadius: '50%', background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', color, flexShrink: 0 }}>
            <Icon fontSize="small" />
          </Box>
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: theme.palette.text.primary, fontSize: '1.5rem', lineHeight: 1.2, my: 0.5 }}>
          {value}
        </Typography>
        <Typography
          variant="caption"
          noWrap
          sx={{
            color: color,
            fontWeight: 700,
            fontSize: 11,
            textTransform: 'uppercase',
            display: 'block',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {subtitle}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function MachineLearning() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const [search, setSearch] = useState('');
  const [taskFilter, setTaskFilter] = useState('ALL');
  const [algoFilter, setAlgoFilter] = useState('ALL');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const { data, loading, error } = useMockFetch(
    () => getModels({ search }),
    [search],
  );
  const allModels = data?.data ?? [];
  const kpis = data?.kpis ?? {};

  // Filtered models
  const filteredModels = allModels.filter((m) => {
    if (taskFilter === 'CLASSIFICATION' && m.type?.toLowerCase() !== 'classification') return false;
    if (taskFilter === 'REGRESSION' && m.type?.toLowerCase() !== 'regression') return false;
    if (algoFilter !== 'ALL' && m.type?.toLowerCase() !== algoFilter.toLowerCase()) return false;
    return true;
  });

  const totalModelsCount = kpis.total_models ?? allModels.length;
  const classificationCount = kpis.classification_models ?? allModels.filter(m => m.type?.toLowerCase() === 'classification').length;
  const regressionCount = kpis.regression_models ?? allModels.filter(m => m.type?.toLowerCase() === 'regression').length;
  const topModelName = kpis.top_performer ?? (allModels[0]?.name || 'N/A');

  const formatScore = (m) => {
    if (!m || m.score == null) return '—';
    if (m.primary_metric === 'R2 Score' || m.primary_metric === 'R² Score' || m.type?.toLowerCase() === 'regression') {
      return Number(m.score).toFixed(4);
    }
    const scoreNum = Number(m.score);
    return `${(scoreNum <= 1.0 ? scoreNum * 100 : scoreNum).toFixed(1)}%`;
  };

  return (
    <PageContainer title="Machine Learning Models" breadcrumbs="Quantitative Catalog">
      <Box sx={{ pt: 3 }}>

        {/* Executive KPI Summary Header Cards — CSS Grid 4-column 100% width layout */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2, mb: 3, width: '100%' }}>
          <ExecutiveKpiCard
            title="Total Models"
            value={totalModelsCount}
            subtitle="Active ML Catalog"
            icon={PsychologyRoundedIcon}
            color={COLORS.accent}
          />
          <ExecutiveKpiCard
            title="Classification"
            value={classificationCount}
            subtitle="Directional Classifiers"
            icon={AutoAwesomeRoundedIcon}
            color={COLORS.pnlGreen}
          />
          <ExecutiveKpiCard
            title="Regression"
            value={regressionCount}
            subtitle="Continuous Return Estimators"
            icon={ShowChartRoundedIcon}
            color="#8B5CF6"
          />
          <ExecutiveKpiCard
            title="Top Performer"
            value={allModels[0] ? (allModels[0].primary_metric === 'Val Loss' ? allModels[0].score?.toFixed(4) : `${(allModels[0].score * 100).toFixed(1)}%`) : '—'}
            subtitle={topModelName}
            icon={AutoAwesomeRoundedIcon}
            color={COLORS.warning}
          />
        </Box>

        {/* Filter Controls & Search */}
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: { xs: 'stretch', md: 'center' }, justifyContent: 'space-between', gap: 2, mb: 3 }}>
          <Box sx={{ width: { xs: '100%', md: 320 } }}>
            <SearchBar onSearch={setSearch} placeholder="Search models by name or symbol…" />
          </Box>

          <Stack direction="row" spacing={1} sx={{ overflowX: 'auto', pb: 0.5 }}>
            {['ALL', 'CLASSIFICATION', 'REGRESSION'].map((t) => (
              <Chip
                key={t}
                label={t}
                size="small"
                onClick={() => setTaskFilter(t)}
                sx={{
                  fontWeight: 700,
                  fontSize: 11,
                  px: 1,
                  cursor: 'pointer',
                  color: taskFilter === t ? '#FFF' : theme.palette.text.secondary,
                  background: taskFilter === t ? COLORS.accent : isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                  '&:hover': { background: taskFilter === t ? COLORS.accent : isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)' },
                }}
              />
            ))}
          </Stack>
        </Box>

        {loading ? (
          <LoadingSkeleton variant="table" />
        ) : filteredModels.length === 0 ? (
          <EmptyState icon={PsychologyRoundedIcon} title="No models found" description="No ML models match your search or filters." />
        ) : (
          <Card>
            <CardContent sx={{ p: '20px !important' }}>
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Model Name</TableCell>
                      <TableCell>Algorithm</TableCell>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Timeframe</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Primary Metric</TableCell>
                      <TableCell align="right">Score</TableCell>
                      <TableCell align="right">Sharpe</TableCell>
                      <TableCell align="right">Win Rate</TableCell>
                      <TableCell>Training Date</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredModels.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((m) => (
                      <TableRow
                        key={m.model_id}
                        hover
                        onClick={() => navigate(`/ml/${m.model_id}`)}
                        sx={{ cursor: 'pointer', transition: 'background-color 0.15s ease' }}
                      >
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 700, color: theme.palette.text.primary }}>
                            {m.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={m.type}
                            size="small"
                            sx={{
                              fontSize: 11,
                              height: 22,
                              fontWeight: 600,
                              color: MODEL_TYPE_COLORS[m.type] ?? COLORS.accent,
                              background: `${MODEL_TYPE_COLORS[m.type] ?? COLORS.accent}15`,
                              border: `1px solid ${MODEL_TYPE_COLORS[m.type] ?? COLORS.accent}30`,
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: COLORS.accent, fontWeight: 700 }}>
                            {m.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={m.timeframe} size="small" variant="outlined" sx={{ height: 20, fontSize: 10 }} />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={m.status?.toUpperCase()}
                            size="small"
                            sx={{
                              height: 20,
                              fontSize: 10,
                              fontWeight: 700,
                              color: m.status === 'trained' ? COLORS.pnlGreen : COLORS.warning,
                              background: m.status === 'trained' ? `${COLORS.pnlGreen}15` : `${COLORS.warning}15`,
                            }}
                          />
                        </TableCell>
                        <TableCell>{m.primary_metric}</TableCell>
                        <TableCell align="right">
                          {(() => {
                            const val = m.score;
                            if (val == null) return <Typography variant="body2">—</Typography>;
                            const num = Number(val);
                            const isReg = m.primary_metric === 'R2 Score' || m.primary_metric === 'R² Score' || m.type?.toLowerCase() === 'regression';
                            const formattedText = isReg ? num.toFixed(4) : `${(num <= 1.0 ? num * 100 : num).toFixed(1)}%`;
                            const color = num < 0 ? COLORS.pnlRed : COLORS.accent;
                            return (
                              <Typography variant="body2" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums', color }}>
                                {formattedText}
                              </Typography>
                            );
                          })()}
                        </TableCell>
                        <TableCell align="right">
                          {(() => {
                            const val = m.sharpe ?? m.metrics?.quant_stats?.sharpe;
                            if (val == null) return <Typography variant="body2">—</Typography>;
                            const num = Number(val);
                            const color = num < 0 ? COLORS.pnlRed : (num >= 1.0 ? COLORS.pnlGreen : theme.palette.text.primary);
                            return (
                              <Typography variant="body2" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color }}>
                                {num.toFixed(2)}
                              </Typography>
                            );
                          })()}
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: COLORS.pnlGreen }}>
                            {(m.win_rate ?? m.metrics?.quant_stats?.win_rate) != null ? `${Number(m.win_rate ?? m.metrics?.quant_stats?.win_rate).toFixed(1)}%` : '—'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontSize: 12, color: theme.palette.text.secondary }}>
                            {m.updated_at ? new Date(m.updated_at).toISOString().split('T')[0] : (m.training_date ? new Date(m.training_date).toISOString().split('T')[0] : 'Today')}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={filteredModels.length}
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
    </PageContainer>
  );
}
