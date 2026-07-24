import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
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
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import SearchBar from '../../components/ui/SearchBar';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getDeployments } from '../../api/deploymentApi';
import { COLORS } from '../../theme/theme';

import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

export default function Deployment() {
  const navigate = useNavigate();
  const theme = useTheme();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { data, loading, error } = useMockFetch(
    () => getDeployments({ search }),
    [search],
  );
  const deployments = data?.data ?? [];

  return (
    <PageContainer title="Strategy Deployment">
      <Box sx={{ pt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <SearchBar onSearch={setSearch} placeholder="Search deployments…" />
        </Box>

        {error && <EmptyState icon={ErrorOutlineRoundedIcon} title="Failed to load deployments" description={error} />}
        {loading ? <LoadingSkeleton variant="table" /> : deployments.length === 0 ? (
          <EmptyState icon={RocketLaunchRoundedIcon} title="No deployments found" description="No active deployments match your search." />
        ) : (
          <Card>
            <CardContent sx={{ p: '20px !important' }}>
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Strategy</TableCell>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Exchange</TableCell>
                      <TableCell>Wallet</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Position</TableCell>
                      <TableCell align="right">Current PnL</TableCell>
                      <TableCell align="right">Daily Return</TableCell>
                      <TableCell>Last Signal</TableCell>
                      <TableCell>Last Execution</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {deployments.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((d) => (
                      <TableRow
                        key={d.execution_id}
                        hover
                        onClick={() => navigate(`/deployment/${d.execution_id}`)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{d.strategy_name}</Typography></TableCell>
                        <TableCell><Typography variant="body2" sx={{ color: COLORS.accent, fontWeight: 500 }}>{d.symbol}</Typography></TableCell>
                        <TableCell>{d.exchange}</TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontSize: 12, fontFamily: 'monospace', color: theme.palette.text.secondary }}>{d.wallet_label}</Typography></TableCell>
                        <TableCell><StatusChip status={d.status} /></TableCell>
                        <TableCell>
                          {d.active_position ? <StatusChip status={d.active_position.side} /> : <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>None</Typography>}
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: d.current_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                            {d.current_pnl >= 0 ? '+' : ''}${d.current_pnl?.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: d.daily_return >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                            {d.daily_return >= 0 ? '+' : ''}{(d.daily_return * 100).toFixed(2)}%
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <StatusChip status={d.last_signal === 'flat' ? 'neutral' : d.last_signal} label={d.last_signal?.toUpperCase()} />
                        </TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontSize: 12, color: theme.palette.text.secondary }}>{new Date(d.last_execution_time).toLocaleString()}</Typography></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={deployments.length}
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
