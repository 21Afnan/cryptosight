import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { createChart, CrosshairMode, LineSeries } from 'lightweight-charts';
import { COLORS } from '../../theme/theme';

/**
 * TradeHistoryChart — lightweight-charts line + trade markers overlay (v4 & v5 compatible).
 * Used in Execution Details page.
 *
 * @param {Array}  equityData  - [{ time: 'YYYY-MM-DD', value: number }]
 * @param {Array}  markers     - [{ time, position: 'belowBar'|'aboveBar', color, shape, text }]
 * @param {number} height
 */
function cleanSeriesData(data) {
  if (!Array.isArray(data) || !data.length) return [];
  const map = new Map();
  data.forEach((item) => {
    if (!item || item.time == null) return;
    const timeStr = String(item.time).split(' ')[0].split('T')[0];
    const val = Number(item.value ?? item.equity ?? item.balance ?? 0);
    if (timeStr && !isNaN(val)) map.set(timeStr, val);
  });
  const clean = [];
  map.forEach((val, timeStr) => clean.push({ time: timeStr, value: val }));
  clean.sort((a, b) => (a.time > b.time ? 1 : a.time < b.time ? -1 : 0));
  if (clean.length === 1) {
    const dt = new Date(clean[0].time);
    dt.setDate(dt.getDate() - 1);
    clean.unshift({ time: dt.toISOString().split('T')[0], value: clean[0].value });
  }
  return clean;
}

export default function TradeHistoryChart({ equityData = [], markers = [], height = 300 }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
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
        crosshair: { mode: CrosshairMode.Normal },
        rightPriceScale: {
          borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
          textColor: isDark ? COLORS.darkTextSecondary : '#6B7280',
          scaleMargins: { top: 0.15, bottom: 0.15 },
        },
        timeScale: { borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder, timeVisible: true },
      });
      chartRef.current = chart;

      const lineOptions = {
        color: COLORS.accent,
        lineWidth: 2,
        priceLineVisible: false,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
        priceFormat: { type: 'price', precision: 0, minMove: 1 },
      };

      const series = typeof chart.addLineSeries === 'function'
        ? chart.addLineSeries(lineOptions)
        : chart.addSeries(LineSeries, lineOptions);

      seriesRef.current = series;

      const clean = cleanSeriesData(equityData);
      if (clean.length > 0) {
        series.setData(clean);
        if (markers.length > 0) {
          try { series.setMarkers(markers); } catch { /* ignore */ }
        }
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
      console.warn("TradeHistoryChart creation warning:", e);
    }
  }, [isDark, height]);

  useEffect(() => {
    if (seriesRef.current && equityData) {
      try {
        const clean = cleanSeriesData(equityData);
        if (clean.length > 0) {
          seriesRef.current.setData(clean);
          if (markers.length > 0) {
            try { seriesRef.current.setMarkers(markers); } catch { /* ignore */ }
          }
          chartRef.current?.timeScale().fitContent();
        }
      } catch (e) {
        console.warn("TradeHistoryChart setData warning:", e);
      }
    }
  }, [equityData, markers]);


  return <Box ref={containerRef} sx={{ width: '100%', height }} />;
}
