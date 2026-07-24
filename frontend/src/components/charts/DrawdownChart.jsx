import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { createChart, CrosshairMode, AreaSeries } from 'lightweight-charts';
import { COLORS } from '../../theme/theme';

/**
 * DrawdownChart — lightweight-charts area chart for drawdown over time (v4 & v5 compatible).
 * Values should be negative percentages (e.g., -0.15 = -15%).
 *
 * @param {Array}  data   - [{ time: 'YYYY-MM-DD', value: number }]
 * @param {number} height
 */
export default function DrawdownChart({ data = [], height = 220 }) {
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
          vertLine: { color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)', labelBackgroundColor: COLORS.pnlRed },
          horzLine: { color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)', labelBackgroundColor: COLORS.pnlRed },
        },
        rightPriceScale: {
          borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
          textColor: isDark ? COLORS.darkTextSecondary : '#6B7280',
          scaleMargins: { top: 0.15, bottom: 0.15 },
        },
        timeScale: {
          borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
          timeVisible: true,
        },
      });

      chart.timeScale().fitContent();
      chartRef.current = chart;

      const areaOptions = {
        lineColor: COLORS.pnlRed,
        topColor: `${COLORS.pnlRed}00`,
        bottomColor: `${COLORS.pnlRed}35`,
        lineWidth: 1.5,
        priceLineVisible: false,
        priceFormat: { type: 'price', precision: 1, minMove: 0.1 },
      };

      const series = typeof chart.addAreaSeries === 'function'
        ? chart.addAreaSeries(areaOptions)
        : chart.addSeries(AreaSeries, areaOptions);

      seriesRef.current = series;

      if (data.length > 0) {
        series.setData(data);
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
        try {
          chart.remove();
        } catch {
          // Ignore cleanup
        }
      };
    } catch (e) {
      console.warn("DrawdownChart creation warning:", e);
    }
  }, [isDark, height]);

  useEffect(() => {
    if (seriesRef.current && data.length > 0) {
      try {
        seriesRef.current.setData(data);
        chartRef.current?.timeScale().fitContent();
      } catch (e) {
        console.warn("DrawdownChart setData warning:", e);
      }
    }
  }, [data]);

  return <Box ref={containerRef} sx={{ width: '100%', height }} />;
}
