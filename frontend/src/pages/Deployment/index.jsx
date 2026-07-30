import React, { useState, useMemo } from 'react';
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
import TableSortLabel from '@mui/material/TableSortLabel';
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
  const [sortField, setSortField] = useState('strategy_name');
  const [sortOrder, setSortOrder] = useState('asc');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const { data, loading, error } = useMockFetch(
    () => getDeployments({ search }),
    [search],
  );
  const deployments = data?.data ?? [];

  const sortedDeployments = useMemo(() => {
    const list = [...deployments];
    if (sortField) {
      list.sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        if (sortField === 'win_rate') {
          valA = a.win_rate ?? 0;
          valB = b.win_rate ?? 0;
        } else if (sortField === 'net_pnl') {
          valA = a.net_pnl ?? a.current_pnl ?? 0;
          valB = b.net_pnl ?? b.current_pnl ?? 0;
        } else if (sortField === 'total_trades') {
          valA = a.total_trades ?? 0;
          valB = b.total_trades ?? 0;
        } else if (sortField === 'active_position') {
          valA = a.active_position?.side ?? '';
          valB = b.active_position?.side ?? '';
        }

        if (typeof valA === 'string') {
          valA = valA.toLowerCase();
          valB = valB.toLowerCase();
          if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
          if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
          return 0;
        }

        const numA = parseFloat(valA ?? 0);
        const numB = parseFloat(valB ?? 0);
        return (numA - numB) * (sortOrder === 'asc' ? 1 : -1);
      });
    }
    return list;
  }, [deployments, sortField, sortOrder]);

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

        <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <SearchBar
            value={search}
            onChange={(val) => { setSearch(val); setPage(0); }}
            placeholder="Search strategy, exchange, or symbol..."
            sx={{ maxWidth: 320 }}
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
            title={search ? "No matching deployments found" : "No deployments running"}
            description={search ? "No running deployments match your search criteria. Try a different term." : "Active trading strategies deployed to live or paper exchanges will appear here."}
          />
        ) : (
          <Card>
            <CardContent sx={{ p: '20px !important' }}>
              <TableContainer>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'strategy_name'}
                          direction={sortField === 'strategy_name' ? sortOrder : 'asc'}
                          onClick={() => handleSort('strategy_name')}
                        >
                          Strategy
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
                          active={sortField === 'exchange'}
                          direction={sortField === 'exchange' ? sortOrder : 'asc'}
                          onClick={() => handleSort('exchange')}
                        >
                          Exchange
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
                      <TableCell>
                        <TableSortLabel
                          active={sortField === 'active_position'}
                          direction={sortField === 'active_position' ? sortOrder : 'asc'}
                          onClick={() => handleSort('active_position')}
                        >
                          Position
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'total_trades'}
                          direction={sortField === 'total_trades' ? sortOrder : 'desc'}
                          onClick={() => handleSort('total_trades')}
                        >
                          Total Trades
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
                      <TableCell align="right">
                        <TableSortLabel
                          active={sortField === 'net_pnl'}
                          direction={sortField === 'net_pnl' ? sortOrder : 'desc'}
                          onClick={() => handleSort('net_pnl')}
                        >
                          Net PnL ($)
                        </TableSortLabel>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sortedDeployments.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((d) => (
                      <TableRow
                        key={d.execution_id}
                        hover
                        onClick={() => {
                          const hasNoTrades = (d.total_trades || 0) === 0 && d.has_ledger === false;
                          if (hasNoTrades) {
                            setToastMsg(`No trades executed yet for ${d.strategy_name}. Details will open once trades occur.`);
                          } else {
                            navigate(`/deployment/${d.execution_id}`);
                          }
                        }}
                        sx={{ cursor: ((d.total_trades || 0) === 0 && d.has_ledger === false) ? 'not-allowed' : 'pointer', opacity: ((d.total_trades || 0) === 0 && d.has_ledger === false) ? 0.8 : 1 }}
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
                count={sortedDeployments.length}
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
