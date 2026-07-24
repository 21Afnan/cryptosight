import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { createChart, CrosshairMode, CandlestickSeries } from 'lightweight-charts';
import { COLORS } from '../../theme/theme';

/**
 * PriceChart — lightweight-charts candlestick chart for OHLCV data (v4 & v5 compatible).
 *
 * @param {Array}  data   - [{ time, open, high, low, close, volume? }]
 * @param {number} height
 */
export default function PriceChart({ data = [], height = 400 }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  useEffect(() => {
    if (!containerRef.current) return;

    try {
      const initialWidth = containerRef.current.clientWidth || 320;

      const chart = createChart(containerRef.current, {
        width: initialWidth,
        height,
        layout: {
          background: { color: 'transparent' },
          textColor: isDark ? COLORS.darkTextSecondary : '#6B7280',
          fontFamily: '"Inter", sans-serif',
          fontSize: 11,
          attributionLogo: false, // Removes overlapping watermark
        },
        grid: {
          vertLines: { color: isDark ? COLORS.chartGridDark : COLORS.chartGridLight },
          horzLines: { color: isDark ? COLORS.chartGridDark : COLORS.chartGridLight },
        },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: { color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)', labelBackgroundColor: COLORS.accent },
          horzLine: { color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)', labelBackgroundColor: COLORS.accent },
        },
        rightPriceScale: {
          borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
          textColor: isDark ? COLORS.darkTextSecondary : '#6B7280',
          scaleMargins: { top: 0.15, bottom: 0.15 },
        },
        timeScale: {
          borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
          timeVisible: true,
          secondsVisible: false,
        },
      });

      chart.timeScale().fitContent();
      chartRef.current = chart;

      const candleOptions = {
        upColor: COLORS.pnlGreen,
        downColor: COLORS.pnlRed,
        borderVisible: false,
        wickUpColor: COLORS.pnlGreen,
        wickDownColor: COLORS.pnlRed,
        priceFormat: { type: 'price', precision: 0, minMove: 1 },
      };

      const candlestickSeries = typeof chart.addCandlestickSeries === 'function'
        ? chart.addCandlestickSeries(candleOptions)
        : chart.addSeries(CandlestickSeries, candleOptions);

      if (data.length > 0) {
        candlestickSeries.setData(data);
        chart.timeScale().fitContent();
      }

      const ro = new ResizeObserver(() => {
        if (containerRef.current && chartRef.current) {
          chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
        }
      });
      ro.observe(containerRef.current);

      return () => {
        ro.disconnect();
        try { chart.remove(); } catch { /* ignore */ }
      };
    } catch (e) {
      console.warn("PriceChart creation warning:", e);
    }
  }, [isDark, data, height]);

  return <Box ref={containerRef} sx={{ width: '100%', height }} />;
}
