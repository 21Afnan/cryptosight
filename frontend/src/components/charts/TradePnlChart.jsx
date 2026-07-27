import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { COLORS } from '../../theme/theme';

/**
 * Format timestamp cleanly without UTC/Z noise.
 * e.g., "2026-07-20 14:30:00" -> "20 Jul '26, 14:30"
 */
function formatCleanDateTime(rawTime) {
  if (!rawTime) return '';
  const str = String(rawTime).replace('Z', '').replace('UTC', '').trim();
  if (str.includes(' ') || (str.includes('T') && str.includes(':'))) {
    const isoStr = str.replace(' ', 'T');
    const d = new Date(isoStr);
    if (!isNaN(d.getTime())) {
      const month = d.toLocaleString('en-US', { month: 'short' });
      const day = String(d.getDate()).padStart(2, '0');
      const yr = String(d.getFullYear()).slice(-2);
      const hrs = String(d.getHours()).padStart(2, '0');
      const mins = String(d.getMinutes()).padStart(2, '0');
      return `${day} ${month} '${yr}, ${hrs}:${mins}`;
    }
  }
  return str;
}

/**
 * TradePnlChart — Bar chart for Net PnL ($) per individual trade.
 * Green bars for profit, red bars for loss.
 *
 * @param {Array}  data   - Trades array [{ trade_id, net_pnl, exit_time, side, ... }] or [{ date, value }]
 * @param {number} height
 */
export default function TradePnlChart({ data = [], height = 260 }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  if (!Array.isArray(data) || !data.length) {
    return null;
  }

  // Format dataset for Recharts
  const chartData = data.map((item, idx) => {
    const pnl = Number(item.net_pnl ?? item.value ?? item.pnl ?? 0);
    const rawTime = item.exit_time ?? item.time ?? item.date ?? item.entry_time ?? `Trade #${idx + 1}`;
    const cleanTime = formatCleanDateTime(rawTime);
    const side = (item.side ?? item.direction ?? '').toUpperCase();
    const tradeId = item.trade_id ?? `#${idx + 1}`;

    return {
      index: idx + 1,
      tradeId,
      side,
      rawTime,
      displayTime: cleanTime,
      pnl,
    };
  });

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    const isProfit = d.pnl >= 0;

    return (
      <div style={{
        background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
        borderRadius: 8,
        padding: '10px 14px',
        fontSize: 12,
        fontFamily: '"Inter", sans-serif',
        boxShadow: isDark ? '0 4px 20px rgba(0,0,0,0.5)' : '0 4px 20px rgba(0,0,0,0.1)',
      }}>
        <div style={{ fontWeight: 700, marginBottom: 4, color: isDark ? '#FFFFFF' : '#111827' }}>
          Trade {d.tradeId} {d.side ? `(${d.side})` : ''}
        </div>
        <div style={{ color: isDark ? COLORS.darkTextSecondary : '#6B7280', fontSize: 11, marginBottom: 6 }}>
          {d.displayTime}
        </div>
        <div style={{
          color: isProfit ? COLORS.pnlGreen : COLORS.pnlRed,
          fontWeight: 800,
          fontSize: 14,
          fontVariantNumeric: 'tabular-nums',
        }}>
          Net PnL: {isProfit ? '+' : ''}${d.pnl.toFixed(2)}
        </div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 12, right: 12, bottom: 8, left: 12 }} barSize={Math.max(6, Math.min(24, Math.floor(600 / chartData.length)))}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? COLORS.chartGridDark : COLORS.chartGridLight} vertical={false} />
        <XAxis
          dataKey="displayTime"
          tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={(v) => `$${v}`}
          tick={{ fontSize: 10, fill: isDark ? COLORS.darkTextSecondary : '#6B7280' }}
          axisLine={false}
          tickLine={false}
          width={56}
        />
        <ReferenceLine y={0} stroke={isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'} strokeDasharray="2 2" />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="pnl" radius={[3, 3, 0, 0]}>
          {chartData.map((entry, idx) => (
            <Cell
              key={idx}
              fill={entry.pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed}
              fillOpacity={0.88}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
