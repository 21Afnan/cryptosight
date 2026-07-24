import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
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

const MODEL_TYPE_COLORS = {
  XGBoost: COLORS.accent,
  LightGBM: COLORS.pnlGreen,
  RandomForest: COLORS.warning,
  LSTM: '#8B5CF6',
};

export default function MachineLearning() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const { data, loading, error } = useMockFetch(
    () => getModels({ search }),
    [search],
  );
  const models = data?.data ?? [];

  const formatScore = (m) => {
    if (m.primary_metric === 'Val Loss') return m.score?.toFixed(5);
    return `${(m.score * 100).toFixed(1)}%`;
  };

  return (
    <PageContainer title="Machine Learning Models">
      <Box sx={{ pt: 3 }}>
        <Box sx={{ mb: 2 }}>
          <SearchBar onSearch={setSearch} placeholder="Search models…" />
        </Box>

        {error && <EmptyState icon={ErrorOutlineRoundedIcon} title="Failed to load models" description={error} />}
        {loading ? <LoadingSkeleton variant="table" /> : models.length === 0 ? (
          <EmptyState icon={PsychologyRoundedIcon} title="No models found" description="No ML models match your search." />
        ) : (
          <Card>
            <CardContent sx={{ p: '20px !important' }}>
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Model Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Timeframe</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Primary Metric</TableCell>
                      <TableCell align="right">Score</TableCell>
                      <TableCell>Training Date</TableCell>
                      <TableCell align="right">Sharpe</TableCell>
                      <TableCell align="right">Win Rate</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {models.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((m) => (
                      <TableRow
                        key={m.model_id}
                        hover
                        onClick={() => navigate(`/ml/${m.model_id}`)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>{m.name}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={m.type}
                            size="small"
                            sx={{
                              fontSize: 11, height: 22,
                              color: MODEL_TYPE_COLORS[m.type] ?? COLORS.accent,
                              background: `${MODEL_TYPE_COLORS[m.type] ?? COLORS.accent}15`,
                              border: `1px solid ${MODEL_TYPE_COLORS[m.type] ?? COLORS.accent}30`,
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: COLORS.accent, fontWeight: 500 }}>{m.symbol}</Typography>
                        </TableCell>
                        <TableCell>{m.timeframe}</TableCell>
                        <TableCell>
                          <Chip
                            label={m.status?.charAt(0).toUpperCase() + m.status?.slice(1)}
                            size="small"
                            sx={{
                              height: 20, fontSize: 11,
                              color: m.status === 'trained' ? COLORS.pnlGreen : COLORS.warning,
                              background: m.status === 'trained' ? `${COLORS.pnlGreen}15` : `${COLORS.warning}15`,
                            }}
                          />
                        </TableCell>
                        <TableCell>{m.primary_metric}</TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: COLORS.accent }}>
                            {formatScore(m)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontSize: 12, color: theme.palette.text.secondary }}>
                            {new Date(m.training_date).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                            {m.backtest_metrics?.sharpe?.toFixed(2) ?? '—'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                            {m.backtest_metrics?.win_rate != null ? `${(m.backtest_metrics.win_rate * 100).toFixed(1)}%` : '—'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={models.length}
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
