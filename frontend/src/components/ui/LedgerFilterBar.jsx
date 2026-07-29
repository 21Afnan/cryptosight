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

/**
 * LedgerFilterBar — shared filter control for trade ledger & signal tables.
 * Used on Strategy Details, Execution Details, and Backtest Details.
 *
 * @param {Function} onChange - Callback receiving { startDate, endDate, side, symbol, pnlFilter, minPnl, maxPnl }
 * @param {Array<string>} symbols - Optional array of symbol options for dropdown
 * @param {boolean} showSymbolFilter - Whether to show symbol filter input/dropdown
 * @param {boolean} showPnlFilter - Whether to show PnL outcome & range filters
 */
export default function LedgerFilterBar({
  onChange,
  symbols = [],
  showSymbolFilter = false,
  showPnlFilter = true,
}) {
  const theme = useTheme();
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [side, setSide] = useState('all');
  const [symbol, setSymbol] = useState('');
  const [pnlFilter, setPnlFilter] = useState('all');
  const [minPnl, setMinPnl] = useState('');
  const [maxPnl, setMaxPnl] = useState('');
  const [minEntryPrice, setMinEntryPrice] = useState('');
  const [maxEntryPrice, setMaxEntryPrice] = useState('');
  const [minExitPrice, setMinExitPrice] = useState('');
  const [maxExitPrice, setMaxExitPrice] = useState('');
  const [minReturn, setMinReturn] = useState('');
  const [maxReturn, setMaxReturn] = useState('');

  const handleChange = (field, val) => {
    const updated = {
      startDate: field === 'startDate' ? val : startDate,
      endDate: field === 'endDate' ? val : endDate,
      side: field === 'side' ? val : side,
      symbol: field === 'symbol' ? val : symbol,
      pnlFilter: field === 'pnlFilter' ? val : pnlFilter,
      minPnl: field === 'minPnl' ? val : minPnl,
      maxPnl: field === 'maxPnl' ? val : maxPnl,
      minEntryPrice: field === 'minEntryPrice' ? val : minEntryPrice,
      maxEntryPrice: field === 'maxEntryPrice' ? val : maxEntryPrice,
      minExitPrice: field === 'minExitPrice' ? val : minExitPrice,
      maxExitPrice: field === 'maxExitPrice' ? val : maxExitPrice,
      minReturn: field === 'minReturn' ? val : minReturn,
      maxReturn: field === 'maxReturn' ? val : maxReturn,
    };

    if (field === 'startDate') setStartDate(val);
    if (field === 'endDate') setEndDate(val);
    if (field === 'side') setSide(val);
    if (field === 'symbol') setSymbol(val);
    if (field === 'pnlFilter') setPnlFilter(val);
    if (field === 'minPnl') setMinPnl(val);
    if (field === 'maxPnl') setMaxPnl(val);
    if (field === 'minEntryPrice') setMinEntryPrice(val);
    if (field === 'maxEntryPrice') setMaxEntryPrice(val);
    if (field === 'minExitPrice') setMinExitPrice(val);
    if (field === 'maxExitPrice') setMaxExitPrice(val);
    if (field === 'minReturn') setMinReturn(val);
    if (field === 'maxReturn') setMaxReturn(val);

    if (onChange) onChange(updated);
  };

  const handleReset = () => {
    setStartDate('');
    setEndDate('');
    setSide('all');
    setSymbol('');
    setPnlFilter('all');
    setMinPnl('');
    setMaxPnl('');
    setMinEntryPrice('');
    setMaxEntryPrice('');
    setMinExitPrice('');
    setMaxExitPrice('');
    setMinReturn('');
    setMaxReturn('');
    if (onChange) {
      onChange({
        startDate: '',
        endDate: '',
        side: 'all',
        symbol: '',
        pnlFilter: 'all',
        minPnl: '',
        maxPnl: '',
        minEntryPrice: '',
        maxEntryPrice: '',
        minExitPrice: '',
        maxExitPrice: '',
        minReturn: '',
        maxReturn: '',
      });
    }
  };

  const hasActiveFilters =
    startDate ||
    endDate ||
    side !== 'all' ||
    symbol ||
    pnlFilter !== 'all' ||
    minPnl ||
    maxPnl ||
    minEntryPrice ||
    maxEntryPrice ||
    minExitPrice ||
    maxExitPrice ||
    minReturn ||
    maxReturn;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
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
          FILTERS:
        </Typography>
      </Box>

      {/* Date range (Start Time / End Time) */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <OutlinedInput
          type="date"
          size="small"
          value={startDate}
          onChange={(e) => handleChange('startDate', e.target.value)}
          sx={{ width: 145, fontSize: 12, height: 34 }}
          inputProps={{ aria_label: 'Start date' }}
        />
        <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
          to
        </Typography>
        <OutlinedInput
          type="date"
          size="small"
          value={endDate}
          onChange={(e) => handleChange('endDate', e.target.value)}
          sx={{ width: 145, fontSize: 12, height: 34 }}
          inputProps={{ aria_label: 'End date' }}
        />
      </Box>

      {/* Side filter */}
      <FormControl size="small" sx={{ minWidth: 110 }}>
        <Select
          value={side}
          onChange={(e) => handleChange('side', e.target.value)}
          sx={{ height: 34, fontSize: 12 }}
        >
          <MenuItem value="all">All Sides</MenuItem>
          <MenuItem value="long">Long / Buy</MenuItem>
          <MenuItem value="short">Short / Sell</MenuItem>
        </Select>
      </FormControl>

      {/* PnL Outcome Filter */}
      {showPnlFilter && (
        <FormControl size="small" sx={{ minWidth: 125 }}>
          <Select
            value={pnlFilter}
            onChange={(e) => handleChange('pnlFilter', e.target.value)}
            sx={{ height: 34, fontSize: 12 }}
          >
            <MenuItem value="all">All PnL</MenuItem>
            <MenuItem value="profit">Profitable (&gt; $0)</MenuItem>
            <MenuItem value="loss">Loss (&lt; $0)</MenuItem>
          </Select>
        </FormControl>
      )}



      {/* Symbol filter */}
      {showSymbolFilter && (
        symbols.length > 0 ? (
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <Select
              value={symbol}
              onChange={(e) => handleChange('symbol', e.target.value)}
              displayEmpty
              sx={{ height: 34, fontSize: 12 }}
            >
              <MenuItem value="">All Symbols</MenuItem>
              {symbols.map((s) => (
                <MenuItem key={s} value={s}>{s}</MenuItem>
              ))}
            </Select>
          </FormControl>
        ) : (
          <OutlinedInput
            size="small"
            placeholder="Symbol (e.g. BTC)"
            value={symbol}
            onChange={(e) => handleChange('symbol', e.target.value)}
            sx={{ width: 120, height: 34, fontSize: 12 }}
          />
        )
      )}

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
 * Shared filter execution helper for trade arrays.
 * Handles side, symbol, start/end dates, PnL outcome, and PnL min/max filters.
 */
export function filterLedgerRows(rows = [], filters = {}) {
  if (!rows || !rows.length) return [];
  const {
    startDate,
    endDate,
    side,
    symbol,
    pnlFilter,
    minPnl,
    maxPnl,
    minEntryPrice,
    maxEntryPrice,
    minExitPrice,
    maxExitPrice,
    minReturn,
    maxReturn,
  } = filters;

  return rows.filter((row) => {
    // 1. Side / Direction filter
    if (side && side !== 'all') {
      const rowSide = (row.side || row.direction || '').toLowerCase();
      const targetSide = side.toLowerCase();

      if (targetSide === 'long' && !['long', 'buy'].includes(rowSide)) return false;
      if (targetSide === 'short' && !['short', 'sell'].includes(rowSide)) return false;
    }

    // 2. Symbol filter
    if (symbol) {
      const rowSymbol = (row.symbol || '').toLowerCase();
      if (!rowSymbol.includes(symbol.toLowerCase())) return false;
    }

    // 3. Date range filter
    const rowTime = row.entry_time || row.timestamp || row.exit_time || row.time;
    if (rowTime) {
      const timeMs = new Date(rowTime).getTime();

      if (startDate) {
        const startMs = new Date(startDate).getTime();
        if (timeMs < startMs) return false;
      }

      if (endDate) {
        const endMs = new Date(endDate).getTime() + (24 * 60 * 60 * 1000 - 1);
        if (timeMs > endMs) return false;
      }
    }

    // 4. PnL Outcome Filter (Profitable > 0 vs Loss < 0)
    const pnlVal = row.net_pnl ?? row.gross_pnl ?? row.pnl ?? row.unrealized_pnl;
    if (pnlFilter && pnlFilter !== 'all' && pnlVal != null) {
      if (pnlFilter === 'profit' && pnlVal <= 0) return false;
      if (pnlFilter === 'loss' && pnlVal >= 0) return false;
    }

    // 5. Min / Max PnL Range Filter
    if (minPnl !== '' && minPnl != null && pnlVal != null) {
      if (pnlVal < parseFloat(minPnl)) return false;
    }
    if (maxPnl !== '' && maxPnl != null && pnlVal != null) {
      if (pnlVal > parseFloat(maxPnl)) return false;
    }

    // 6. Min / Max Entry Price Range Filter
    const entryPriceVal = row.entry_price ?? row.price;
    if (minEntryPrice !== '' && minEntryPrice != null && entryPriceVal != null) {
      if (entryPriceVal < parseFloat(minEntryPrice)) return false;
    }
    if (maxEntryPrice !== '' && maxEntryPrice != null && entryPriceVal != null) {
      if (entryPriceVal > parseFloat(maxEntryPrice)) return false;
    }

    // 7. Min / Max Exit Price Range Filter
    const exitPriceVal = row.exit_price;
    if (minExitPrice !== '' && minExitPrice != null && exitPriceVal != null) {
      if (exitPriceVal < parseFloat(minExitPrice)) return false;
    }
    if (maxExitPrice !== '' && maxExitPrice != null && exitPriceVal != null) {
      if (exitPriceVal > parseFloat(maxExitPrice)) return false;
    }

    // 8. Min / Max Return % Range Filter
    const returnVal = row.return_pct ?? row.perc_pnl ?? row.return_percent;
    if (minReturn !== '' && minReturn != null && returnVal != null) {
      if (returnVal < parseFloat(minReturn)) return false;
    }
    if (maxReturn !== '' && maxReturn != null && returnVal != null) {
      if (returnVal > parseFloat(maxReturn)) return false;
    }

    return true;
  });
}
