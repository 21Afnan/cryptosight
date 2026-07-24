import React, { useState, useEffect } from 'react';
import InputAdornment from '@mui/material/InputAdornment';
import OutlinedInput from '@mui/material/OutlinedInput';
import IconButton from '@mui/material/IconButton';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import ClearRoundedIcon from '@mui/icons-material/ClearRounded';

/**
 * SearchBar — controlled search input with 300ms debounce.
 * @param {Function} onSearch — called with debounced search string
 * @param {string}   placeholder
 * @param {string}   value — controlled value (optional)
 */
export default function SearchBar({
  onSearch,
  placeholder = 'Search…',
  value: controlledValue,
  sx = {},
}) {
  const [localValue, setLocalValue] = useState(controlledValue ?? '');

  // Debounce: fire onSearch 300ms after user stops typing
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch?.(localValue);
    }, 300);
    return () => clearTimeout(timer);
  }, [localValue, onSearch]);

  const handleClear = () => {
    setLocalValue('');
    onSearch?.('');
  };

  return (
    <OutlinedInput
      id="search-bar-input"
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      placeholder={placeholder}
      size="small"
      startAdornment={
        <InputAdornment position="start">
          <SearchRoundedIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
        </InputAdornment>
      }
      endAdornment={
        localValue ? (
          <InputAdornment position="end">
            <IconButton size="small" onClick={handleClear} edge="end" aria-label="Clear search">
              <ClearRoundedIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </InputAdornment>
        ) : null
      }
      sx={{ minWidth: 240, ...sx }}
    />
  );
}
