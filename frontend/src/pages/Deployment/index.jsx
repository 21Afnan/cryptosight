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
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatusChip from '../../components/ui/StatusChip';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import SearchBar from '../../components/ui/SearchBar';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getDeployments } from '../../api/deploymentApi';
import { COLORS } from '../../theme/theme';

import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

export default function Deployment() {
  const navigate = useNavigate();
  const theme = useTheme();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [toastMsg, setToastMsg] = useState('');
  const { data, loading, error } = useMockFetch(
    () => getDeployments({ search }),
    [search],
  );
  const deployments = data?.data ?? [];

  return (
    <PageContainer title="Execution & Live Deployments">
      <Box sx={{ pt: 3 }}>
        <Snackbar
          open={Boolean(toastMsg)}
          autoHideDuration={4000}
          onClose={() => setToastMsg('')}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert severity="warning" onClose={() => setToastMsg('')} sx={{ width: '100%' }}>
            {toastMsg}
          </Alert>
        </Snackbar>

        <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search strategy, exchange, or symbol..."
            sx={{ maxWidth: 360 }}
          />
        </Box>

        {loading ? (
          <LoadingSkeleton variant="table" />
        ) : error ? (
          <EmptyState
            icon={ErrorOutlineRoundedIcon}
            title="Failed to load deployments"
            description={error}
          />
        ) : !deployments.length ? (
          <EmptyState
            icon={PlayArrowRoundedIcon}
            title="No deployments running"
            description="Active trading strategies deployed to live or paper exchanges will appear here."
          />
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
                      <TableCell>Timeframe</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Position</TableCell>
                      <TableCell align="right">Total Trades</TableCell>
                      <TableCell align="right">Win Rate</TableCell>
                      <TableCell align="right">Net PnL ($)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {deployments.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((d) => (
                      <TableRow
                        key={d.execution_id}
                        hover
                        onClick={() => {
                          if (d.has_ledger === false) {
                            setToastMsg(`Execution details unavailable: No trade ledger table exists in database for ${d.strategy_name} yet.`);
                          } else {
                            navigate(`/deployment/${d.execution_id}`);
                          }
                        }}
                        sx={{ cursor: d.has_ledger === false ? 'not-allowed' : 'pointer', opacity: d.has_ledger === false ? 0.75 : 1 }}
                      >
                        <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>{d.strategy_name}</Typography></TableCell>
                        <TableCell><Typography variant="body2" sx={{ color: COLORS.accent, fontWeight: 700 }}>{d.symbol}</Typography></TableCell>
                        <TableCell>{d.exchange}</TableCell>
                        <TableCell><Chip label={d.timeframe || '15m'} size="small" variant="outlined" sx={{ height: 20, fontSize: 10 }} /></TableCell>
                        <TableCell><StatusChip status={d.status} /></TableCell>
                        <TableCell>
                          {d.active_position ? <StatusChip status={d.active_position.side} /> : <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>None</Typography>}
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                            {d.total_trades ?? 0}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: COLORS.pnlGreen, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                            {(d.win_rate ?? 0).toFixed(1)}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: (d.net_pnl ?? d.current_pnl ?? 0) >= 0 ? COLORS.pnlGreen : COLORS.pnlRed, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                            {(d.net_pnl ?? d.current_pnl ?? 0) >= 0 ? '+' : ''}${(d.net_pnl ?? d.current_pnl ?? 0).toFixed(2)}
                          </Typography>
                        </TableCell>
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
