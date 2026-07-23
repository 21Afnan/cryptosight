import React, { useState } from 'react';
import {
  Box, Paper, Typography, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow,
  Chip, TextField, InputAdornment, TableSortLabel,
  Tooltip, IconButton,
} from '@mui/material';
import SearchIcon        from '@mui/icons-material/Search';
import OpenInNewIcon     from '@mui/icons-material/OpenInNew';
import FilterListIcon    from '@mui/icons-material/FilterList';
import { useNavigate }   from 'react-router-dom';

// ─── Status Badge ─────────────────────────────────────────────────────────────
const StatusChip = ({ status }) => {
  const map = {
    Active:  { color: 'success', label: '● Active'  },
    Paused:  { color: 'warning', label: '◐ Paused'  },
    Stopped: { color: 'error',   label: '○ Stopped' },
  };
  const cfg = map[status] || { color: 'default', label: status };
  return (
    <Chip
      label={cfg.label}
      color={cfg.color}
      size="small"
      variant="outlined"
      sx={{ fontWeight: 700, fontSize: '0.7rem', letterSpacing: '0.02em' }}
    />
  );
};

// ─── Return value coloring ────────────────────────────────────────────────────
const ReturnCell = ({ value }) => {
  const color = value.startsWith('+') ? '#10B981' : '#EF4444';
  return (
    <Typography fontSize="0.875rem" fontWeight={700} sx={{ color }}>
      {value}
    </Typography>
  );
};

// ─── Exchange badge ───────────────────────────────────────────────────────────
const ExchangeChip = ({ exchange }) => {
  const bg = exchange === 'Binance' ? '#F0B90B22' : '#3D5AFE22';
  const color = exchange === 'Binance' ? '#F0B90B' : '#7986CB';
  return (
    <Box
      component="span"
      sx={{
        px: 1.2, py: 0.3,
        borderRadius: 1.5,
        background: bg,
        color, fontWeight: 700,
        fontSize: '0.75rem',
      }}
    >
      {exchange}
    </Box>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
const StrategiesTable = ({ data = [] }) => {
  const navigate  = useNavigate();
  const [search,  setSearch]  = useState('');
  const [orderBy, setOrderBy] = useState('sharpe');
  const [order,   setOrder]   = useState('desc');

  // Filter by search query — uses React JSX auto-escaping (XSS safe)
  const filtered = data.filter(row =>
    row.name.toLowerCase().includes(search.toLowerCase()) ||
    row.symbol.toLowerCase().includes(search.toLowerCase()) ||
    row.exchange.toLowerCase().includes(search.toLowerCase())
  );

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    const aVal = a[orderBy];
    const bVal = b[orderBy];
    if (typeof aVal === 'number') {
      return order === 'asc' ? aVal - bVal : bVal - aVal;
    }
    return order === 'asc'
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal));
  });

  const handleSort = (col) => {
    setOrder(orderBy === col && order === 'asc' ? 'desc' : 'asc');
    setOrderBy(col);
  };

  const columns = [
    { id: 'name',         label: 'Strategy Name' },
    { id: 'symbol',       label: 'Symbol'        },
    { id: 'exchange',     label: 'Exchange'      },
    { id: 'timeframe',    label: 'Timeframe'     },
    { id: 'status',       label: 'Status'        },
    { id: 'latestReturn', label: 'Latest Return' },
    { id: 'sharpe',       label: 'Sharpe Ratio'  },
    { id: 'winRate',      label: 'Win Rate'      },
    { id: '_actions',     label: ''              },
  ];

  return (
    <Paper elevation={0} sx={{ borderRadius: 3, overflow: 'hidden' }}>
      {/* ── Header bar ── */}
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        px={3} py={2.5}
        sx={{ borderBottom: '1px solid', borderColor: 'divider' }}
      >
        <Box>
          <Typography variant="h6" fontWeight={700}>All Strategies</Typography>
          <Typography variant="caption" color="text.secondary">
            {filtered.length} of {data.length} strategies
          </Typography>
        </Box>

        <Box display="flex" gap={1.5} alignItems="center">
          <TextField
            size="small"
            placeholder="Search strategies…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                </InputAdornment>
              ),
            }}
            sx={{
              width: 240,
              '& .MuiOutlinedInput-root': { borderRadius: 2.5 },
            }}
          />
          <Tooltip title="Filter">
            <IconButton size="small">
              <FilterListIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* ── Table ── */}
      <TableContainer sx={{ maxHeight: 480 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.id}>
                  {col.id !== '_actions' ? (
                    <TableSortLabel
                      active={orderBy === col.id}
                      direction={orderBy === col.id ? order : 'asc'}
                      onClick={() => handleSort(col.id)}
                    >
                      {col.label}
                    </TableSortLabel>
                  ) : null}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {sorted.map((row) => (
              <TableRow
                key={row.id}
                hover
                sx={{
                  cursor: 'pointer',
                  transition: 'background 0.15s',
                  '&:hover': {
                    background: 'rgba(124,58,237,0.06) !important',
                  },
                }}
                onClick={() => navigate(`/strategies/${row.id}`)}
              >
                <TableCell>
                  <Typography fontWeight={600} fontSize="0.875rem">
                    {row.name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    fontWeight={600}
                    fontSize="0.8rem"
                    color="primary.light"
                  >
                    {row.symbol}
                  </Typography>
                </TableCell>
                <TableCell><ExchangeChip exchange={row.exchange} /></TableCell>
                <TableCell>
                  <Box
                    component="span"
                    sx={{
                      px: 1, py: 0.3, borderRadius: 1,
                      background: 'rgba(6,182,212,0.12)',
                      color: '#06B6D4', fontWeight: 600, fontSize: '0.75rem',
                    }}
                  >
                    {row.timeframe}
                  </Box>
                </TableCell>
                <TableCell><StatusChip status={row.status} /></TableCell>
                <TableCell><ReturnCell value={row.latestReturn} /></TableCell>
                <TableCell>
                  <Typography
                    fontWeight={700}
                    fontSize="0.875rem"
                    color={row.sharpe >= 1.5 ? '#10B981' : row.sharpe >= 1 ? '#F59E0B' : '#EF4444'}
                  >
                    {row.sharpe.toFixed(2)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography fontWeight={600} fontSize="0.875rem">
                    {row.winRate}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Tooltip title="Open Details">
                    <IconButton size="small" onClick={(e) => { e.stopPropagation(); navigate(`/strategies/${row.id}`); }}>
                      <OpenInNewIcon sx={{ fontSize: 16, color: 'primary.light' }} />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}

            {sorted.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No strategies found</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default StrategiesTable;
