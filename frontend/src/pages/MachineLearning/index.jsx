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
import TableSortLabel from '@mui/material/TableSortLabel';
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
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const { data, loading, error } = useMockFetch(
    () => getModels({ search }),
    [search],
  );
  const allModels = data?.data ?? [];
  const kpis = data?.kpis ?? {};

  // Filtered models
  const filteredModels = React.useMemo(() => {
    return allModels.filter((m) => {
      // Classification/Regression filter
      if (taskFilter === 'CLASSIFICATION' && m.type?.toLowerCase() !== 'classification') return false;
      if (taskFilter === 'REGRESSION' && m.type?.toLowerCase() !== 'regression') return false;

      return true;
    });
  }, [allModels, taskFilter]);

  const [sortField, setSortField] = useState('updated_at');
  const [sortOrder, setSortOrder] = useState('desc');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const sortedModels = React.useMemo(() => {
    const list = [...filteredModels];
    if (sortField) {
      list.sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        if (sortField === 'return_pct') {
          valA = a.return_pct ?? a.metrics?.quant_stats?.total_return ?? a.metrics?.quant_stats?.net_pnl_pct ?? a.metrics?.quant_stats?.return_pct ?? -Infinity;
          valB = b.return_pct ?? b.metrics?.quant_stats?.total_return ?? b.metrics?.quant_stats?.net_pnl_pct ?? b.metrics?.quant_stats?.return_pct ?? -Infinity;
        } else if (sortField === 'sharpe') {
          valA = a.sharpe ?? a.metrics?.quant_stats?.sharpe ?? -Infinity;
          valB = b.sharpe ?? b.metrics?.quant_stats?.sharpe ?? -Infinity;
        } else if (sortField === 'win_rate') {
          valA = a.win_rate ?? a.metrics?.quant_stats?.win_rate ?? -Infinity;
          valB = b.win_rate ?? b.metrics?.quant_stats?.win_rate ?? -Infinity;
        } else if (sortField === 'updated_at') {
          valA = a.updated_at ?? a.training_date ?? '';
          valB = b.updated_at ?? b.training_date ?? '';
        }

        if (typeof valA === 'string' && isNaN(Date.parse(valA))) {
          valA = valA.toLowerCase();
          valB = valB.toLowerCase();
          if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
          if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
          return 0;
        }

        const isDateA = valA && (valA instanceof Date || !isNaN(Date.parse(valA)) && isNaN(Number(valA)));
        const isDateB = valB && (valB instanceof Date || !isNaN(Date.parse(valB)) && isNaN(Number(valB)));

        const numA = isDateA ? new Date(valA).getTime() : parseFloat(valA ?? 0);
        const numB = isDateB ? new Date(valB).getTime() : parseFloat(valB ?? 0);
        return (numA - numB) * (sortOrder === 'asc' ? 1 : -1);
      });
    }
    return list;
  }, [filteredModels, sortField, sortOrder]);

  const totalModelsCount = kpis.total_models ?? allModels.length;
  const classificationCount = kpis.classification_models ?? allModels.filter(m => m.type?.toLowerCase() === 'classification').length;
  const regressionCount = kpis.regression_models ?? allModels.filter(m => m.type?.toLowerCase() === 'regression').length;

  // Find top performer model by highest return percentage fetched from backend
  const topReturnModel = allModels.reduce((best, cur) => {
    const curRet = cur.return_pct ?? cur.metrics?.quant_stats?.total_return ?? -Infinity;
    const bestRet = best?.return_pct ?? best?.metrics?.quant_stats?.total_return ?? -Infinity;
    return curRet > bestRet ? cur : best;
  }, null);
  const topModelName = topReturnModel?.name || kpis.top_performer || (allModels[0]?.name || 'N/A');

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
            value={topReturnModel && topReturnModel.return_pct != null ? `${topReturnModel.return_pct >= 0 ? '+' : ''}${Number(topReturnModel.return_pct).toFixed(1)}%` : (allModels[0] ? `${(allModels[0].score * 100).toFixed(1)}%` : '—')}
            subtitle={topModelName}
            icon={AutoAwesomeRoundedIcon}
            color={topReturnModel && (topReturnModel.return_pct ?? 0) >= 0 ? COLORS.pnlGreen : COLORS.warning}
          />
        </Box>

        {/* Filter Controls & Search */}
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: { xs: 'stretch', md: 'center' }, justifyContent: 'space-between', gap: 2, mb: 3 }}>
          <Box sx={{ width: { xs: '100%', md: 320 } }}>
            <SearchBar onSearch={setSearch} placeholder="Search models by name or symbol…" />
          </Box>

          <Stack direction="row" spacing={1} sx={{ overflowX: 'auto', pb: 0.5, flexShrink: 0 }}>
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
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'name'}
                          direction={sortField === 'name' ? sortOrder : 'asc'}
                          onClick={() => handleSort('name')}
                        >
                          Model Name
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'type'}
                          direction={sortField === 'type' ? sortOrder : 'asc'}
                          onClick={() => handleSort('type')}
                        >
                          Algorithm
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'symbol'}
                          direction={sortField === 'symbol' ? sortOrder : 'asc'}
                          onClick={() => handleSort('symbol')}
                        >
                          Symbol
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'timeframe'}
                          direction={sortField === 'timeframe' ? sortOrder : 'asc'}
                          onClick={() => handleSort('timeframe')}
                        >
                          Timeframe
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'status'}
                          direction={sortField === 'status' ? sortOrder : 'asc'}
                          onClick={() => handleSort('status')}
                        >
                          Status
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'return_pct'}
                          direction={sortField === 'return_pct' ? sortOrder : 'desc'}
                          onClick={() => handleSort('return_pct')}
                        >
                          Return (%)
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'sharpe'}
                          direction={sortField === 'sharpe' ? sortOrder : 'desc'}
                          onClick={() => handleSort('sharpe')}
                        >
                          Sharpe
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'win_rate'}
                          direction={sortField === 'win_rate' ? sortOrder : 'desc'}
                          onClick={() => handleSort('win_rate')}
                        >
                          Win Rate
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'updated_at'}
                          direction={sortField === 'updated_at' ? sortOrder : 'desc'}
                          onClick={() => handleSort('updated_at')}
                        >
                          Training Date
                        </TableSortLabel>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sortedModels.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((m) => (
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
                        <TableCell align="right">
                          {(() => {
                            const ret = m.return_pct ?? m.metrics?.quant_stats?.total_return ?? m.metrics?.quant_stats?.net_pnl_pct ?? m.metrics?.quant_stats?.return_pct;
                            if (ret == null) return <Typography variant="body2">—</Typography>;
                            const num = Number(ret);
                            const color = num < 0 ? COLORS.pnlRed : (num > 0 ? COLORS.pnlGreen : theme.palette.text.primary);
                            const formattedText = `${num >= 0 ? '+' : ''}${num.toFixed(1)}%`;
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
                            const color = num < 0 ? COLORS.pnlRed : (num > 0 ? COLORS.pnlGreen : theme.palette.text.primary);
                            return (
                              <Typography variant="body2" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color }}>
                                {num.toFixed(2)}
                              </Typography>
                            );
                          })()}
                        </TableCell>
                        <TableCell align="right">
                          {(() => {
                            const wr = m.win_rate ?? m.metrics?.quant_stats?.win_rate;
                            if (wr == null) return <Typography variant="body2">—</Typography>;
                            const num = Number(wr);
                            const pctValue = num <= 1 ? num * 100 : num;
                            const color = pctValue >= 50 ? COLORS.pnlGreen : COLORS.pnlRed;
                            return (
                              <Typography variant="body2" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color }}>
                                {pctValue.toFixed(1)}%
                              </Typography>
                            );
                          })()}
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
                count={sortedModels.length}
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
