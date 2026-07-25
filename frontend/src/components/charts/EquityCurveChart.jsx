import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { createChart, CrosshairMode, AreaSeries } from 'lightweight-charts';
import { COLORS } from '../../theme/theme';

/**
 * EquityCurveChart — lightweight-charts area chart for equity curves (v4 & v5 compatible).
 * Used on Strategy Details, Execution Details, Backtest Details, Account Overview.
 *
 * @param {Array}  data     - [{ time: 'YYYY-MM-DD', value: number }]
 * @param {number} height
 * @param {string} label    - Legend label
 */
export default function EquityCurveChart({ data = [], height = 300, label = 'Portfolio Value' }) {
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
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: {
            color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
            labelBackgroundColor: COLORS.accent,
          },
          horzLine: {
            color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
            labelBackgroundColor: COLORS.accent,
          },
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
        handleScroll: { mouseWheel: true, pressedMouseMove: true },
        handleScale: { mouseWheel: true, pinch: true },
      });

      chart.timeScale().fitContent();
      chartRef.current = chart;

      const areaOptions = {
        lineColor: COLORS.accent,
        topColor: `${COLORS.accent}30`,
        bottomColor: `${COLORS.accent}00`,
        lineWidth: 2,
        priceLineVisible: false,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 5,
        crosshairMarkerBorderColor: COLORS.accent,
        crosshairMarkerBackgroundColor: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        priceFormat: { type: 'price', precision: 0, minMove: 1 },
      };

      const series = typeof chart.addAreaSeries === 'function'
        ? chart.addAreaSeries(areaOptions)
        : chart.addSeries(AreaSeries, areaOptions);

      seriesRef.current = series;

      // Deduplicate by time and keep last value per day, then sort strictly ascending
      const cleanData = [];
      const map = new Map();
      (data || []).forEach((item) => {
        if (!item || item.time == null) return;
        const timeStr = String(item.time).split(' ')[0].split('T')[0];
        const val = Number(item.value ?? 0);
        if (timeStr && !isNaN(val)) {
          map.set(timeStr, val);
        }
      });

      map.forEach((val, timeStr) => {
        cleanData.push({ time: timeStr, value: val });
      });

      cleanData.sort((a, b) => (a.time > b.time ? 1 : a.time < b.time ? -1 : 0));

      if (cleanData.length > 0) {
        series.setData(cleanData);
        chart.timeScale().fitContent();
      }

      // Resize observer
      const ro = new ResizeObserver(() => {
        if (containerRef.current && chartRef.current) {
          chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
        }
      });
      ro.observe(containerRef.current);

      return () => {
        ro.disconnect();
        try {
          chart.remove();
        } catch {
          // Ignore cleanup errors on unmount
        }
      };
    } catch (e) {
      console.warn("EquityCurveChart creation warning:", e);
    }
  }, [isDark, height]);

  // Update data without recreating chart
  useEffect(() => {
    if (seriesRef.current && data.length > 0) {
      try {
        seriesRef.current.setData(data);
        chartRef.current?.timeScale().fitContent();
      } catch (e) {
        console.warn("EquityCurveChart setData warning:", e);
      }
    }
  }, [data]);

  return <Box ref={containerRef} sx={{ width: '100%', height }} />;
}
