import React, { useState } from 'react';
import Box from '@mui/material/Box';
import OutlinedInput from '@mui/material/OutlinedInput';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { useTheme } from '@mui/material/styles';

import FilterListRoundedIcon from '@mui/icons-material/FilterListRounded';
import RestartAltRoundedIcon from '@mui/icons-material/RestartAltRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';

/**
 * StrategyFilterBar — filter bar for Strategy tables (Dashboard & Strategy List page).
 * Filters by Search query (Name/Symbol), Exchange, Status, Timeframe (TF), and PnL / Return outcome.
 *
 * @param {Function} onChange - Callback receiving { search, exchange, status, timeframe, pnl }
 */
export default function StrategyFilterBar({ onChange }) {
  const theme = useTheme();
  const [search, setSearch] = useState('');
  const [exchange, setExchange] = useState('all');
  const [status, setStatus] = useState('all');
  const [timeframe, setTimeframe] = useState('all');
  const [pnl, setPnl] = useState('all');

  const handleChange = (field, val) => {
    const updated = {
      search: field === 'search' ? val : search,
      exchange: field === 'exchange' ? val : exchange,
      status: field === 'status' ? val : status,
      timeframe: field === 'timeframe' ? val : timeframe,
      pnl: field === 'pnl' ? val : pnl,
    };

    if (field === 'search') setSearch(val);
    if (field === 'exchange') setExchange(val);
    if (field === 'status') setStatus(val);
    if (field === 'timeframe') setTimeframe(val);
    if (field === 'pnl') setPnl(val);

    if (onChange) onChange(updated);
  };

  const handleReset = () => {
    setSearch('');
    setExchange('all');
    setStatus('all');
    setTimeframe('all');
    setPnl('all');
    if (onChange) {
      onChange({ search: '', exchange: 'all', status: 'all', timeframe: 'all', pnl: 'all' });
    }
  };

  const hasActiveFilters = search || exchange !== 'all' || status !== 'all' || timeframe !== 'all' || pnl !== 'all';

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.25,
        flexWrap: 'wrap',
        mb: 2,
        p: 1.5,
        borderRadius: '16px',
        background: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
        boxShadow: 'inset 0 0 0 1px rgba(94, 139, 110, 0.12)',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, color: theme.palette.text.secondary }}>
        <FilterListRoundedIcon sx={{ fontSize: 18 }} />
        <Typography variant="caption" sx={{ fontWeight: 700, letterSpacing: '0.06em' }}>
          STRATEGY FILTERS:
        </Typography>
      </Box>

      {/* Search by Strategy Name or Symbol */}
      <OutlinedInput
        size="small"
        placeholder="Search strategy or symbol…"
        value={search}
        onChange={(e) => handleChange('search', e.target.value)}
        startAdornment={<SearchRoundedIcon sx={{ fontSize: 16, mr: 0.75, color: 'text.secondary' }} />}
        sx={{ width: 190, height: 34, fontSize: 12 }}
      />

      {/* Exchange Filter */}
      <FormControl size="small" sx={{ minWidth: 125 }}>
        <Select
          value={exchange}
          onChange={(e) => handleChange('exchange', e.target.value)}
          sx={{ height: 34, fontSize: 12 }}
        >
          <MenuItem value="all">All Exchanges</MenuItem>
          <MenuItem value="Binance">Binance</MenuItem>
          <MenuItem value="Bybit">Bybit</MenuItem>
        </Select>
      </FormControl>

      {/* Status Filter */}
      <FormControl size="small" sx={{ minWidth: 115 }}>
        <Select
          value={status}
          onChange={(e) => handleChange('status', e.target.value)}
          sx={{ height: 34, fontSize: 12 }}
        >
          <MenuItem value="all">All Statuses</MenuItem>
          <MenuItem value="active">Active</MenuItem>
          <MenuItem value="paused">Paused</MenuItem>
          <MenuItem value="stopped">Stopped</MenuItem>
        </Select>
      </FormControl>

      {/* Timeframe Filter */}
      <FormControl size="small" sx={{ minWidth: 95 }}>
        <Select
          value={timeframe}
          onChange={(e) => handleChange('timeframe', e.target.value)}
          sx={{ height: 34, fontSize: 12 }}
        >
          <MenuItem value="all">All TFs</MenuItem>
          <MenuItem value="15m">15m</MenuItem>
          <MenuItem value="1h">1h</MenuItem>
          <MenuItem value="2h">2h</MenuItem>
          <MenuItem value="4h">4h</MenuItem>
        </Select>
      </FormControl>

      {/* PnL / Return Filter Dropdown */}
      <FormControl size="small" sx={{ minWidth: 145 }}>
        <Select
          value={pnl}
          onChange={(e) => handleChange('pnl', e.target.value)}
          sx={{
            height: 34,
            fontSize: 12,
            fontWeight: pnl !== 'all' ? 700 : 400,
            color: pnl === 'profitable' || pnl === 'high' ? theme.palette.success.main : pnl === 'loss' ? theme.palette.error.main : 'inherit',
          }}
          startAdornment={<TrendingUpRoundedIcon sx={{ fontSize: 16, mr: 0.5, opacity: 0.8 }} />}
        >
          <MenuItem value="all">All PnL / Return</MenuItem>
          <MenuItem value="profitable">Profitable (&gt; 0%)</MenuItem>
          <MenuItem value="high">High Return (&gt; +10%)</MenuItem>
          <MenuItem value="loss">Loss Only (&lt; 0%)</MenuItem>
        </Select>
      </FormControl>

      {/* Reset button */}
      {hasActiveFilters && (
        <Button
          size="small"
          startIcon={<RestartAltRoundedIcon sx={{ fontSize: 16 }} />}
          onClick={handleReset}
          sx={{ height: 34, fontSize: 11, ml: 'auto' }}
        >
          Reset
        </Button>
      )}
    </Box>
  );
}

/**
 * Filter helper for strategy summary objects.
 */
export function filterStrategies(strategies = [], filters = {}) {
  if (!strategies || !strategies.length) return [];
  const { search, exchange, status, timeframe, pnl } = filters;

  return strategies.filter((item) => {
    // Search
    if (search) {
      const q = search.toLowerCase();
      const name = (item.strategy_name || '').toLowerCase();
      const sym = (item.symbol || '').toLowerCase();
      if (!name.includes(q) && !sym.includes(q)) return false;
    }

    // Exchange
    if (exchange && exchange !== 'all') {
      if ((item.exchange || '').toLowerCase() !== exchange.toLowerCase()) return false;
    }

    // Status
    if (status && status !== 'all') {
      if ((item.status || '').toLowerCase() !== status.toLowerCase()) return false;
    }

    // Timeframe
    if (timeframe && timeframe !== 'all') {
      const itemTf = (item.timeframe || item.target_timeframe || '').toLowerCase();
      if (itemTf !== timeframe.toLowerCase()) return false;
    }

    // PnL / Return Filter
    const ret = item.latest_return ?? item.total_return ?? item.pnl_pct ?? 0;
    if (pnl === 'profitable' && ret <= 0) return false;
    if (pnl === 'high' && ret < 0.10) return false;
    if (pnl === 'loss' && ret >= 0) return false;

    return true;
  });
}
