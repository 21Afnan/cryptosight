import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { createChart, CrosshairMode, AreaSeries } from 'lightweight-charts';
import { COLORS } from '../../theme/theme';

/**
 * Universal Equity Curve Data Formatter.
 * Handles ALL input formats across the application:
 *   1. [{ time: 'YYYY-MM-DD' | unix_sec, value: 10000 }]
 *   2. [{ timestamp: ..., equity: ... }]
 *   3. Primitive number arrays: [10000, 10200, 10150, 10500]
 */
function prepareEquityData(data) {
  let rawList = Array.isArray(data) ? data : (data?.raw_values || data?.values || data?.data || []);
  if (!rawList || !rawList.length) return [];

  const points = [];
  const now = new Date();

  rawList.forEach((item, idx) => {
    if (item == null) return;

    let timeVal = null;
    let numVal = null;

    if (typeof item === 'number' || (typeof item === 'string' && !isNaN(Number(item)) && !item.includes('-'))) {
      // Primitive number format: [10000, 10200, 10150]
      numVal = Number(item);
      const d = new Date(now);
      d.setDate(d.getDate() - (rawList.length - 1 - idx));
      timeVal = d.toISOString().split('T')[0];
    } else if (typeof item === 'object') {
      // Object format: { time: ..., value: ... } or { timestamp: ..., equity: ... }
      numVal = Number(item.value ?? item.equity ?? item.balance ?? item.val ?? 0);
      const rawTime = item.time ?? item.timestamp ?? item.date ?? item.created_at;

      if (rawTime != null) {
        if (typeof rawTime === 'string' && rawTime.includes('-')) {
          timeVal = rawTime.split(' ')[0].split('T')[0];
        } else if (typeof rawTime === 'number') {
          timeVal = rawTime > 1e11 ? Math.floor(rawTime / 1000) : Math.floor(rawTime);
        } else {
          timeVal = String(rawTime);
        }
      } else {
        const d = new Date(now);
        d.setDate(d.getDate() - (rawList.length - 1 - idx));
        timeVal = d.toISOString().split('T')[0];
      }
    }

    if (timeVal != null && !isNaN(numVal)) {
      points.push({ time: timeVal, value: numVal });
    }
  });

  if (!points.length) return [];

  // Sort ascending by time
  points.sort((a, b) => (a.time > b.time ? 1 : a.time < b.time ? -1 : 0));

  // Deduplicate exact duplicate timestamps for lightweight-charts
  const clean = [];
  let lastTime = null;
  points.forEach((p) => {
    let t = p.time;
    if (typeof t === 'number' && typeof lastTime === 'number' && t <= lastTime) {
      t = lastTime + 1;
    }
    clean.push({ time: t, value: p.value });
    lastTime = t;
  });

  if (clean.length === 1) {
    let prevTime;
    if (typeof clean[0].time === 'number') {
      prevTime = clean[0].time - 60;
    } else {
      const d = new Date(clean[0].time);
      d.setDate(d.getDate() - 1);
      prevTime = d.toISOString().split('T')[0];
    }
    clean.unshift({ time: prevTime, value: clean[0].value });
  }

  return clean;
}

export default function EquityCurveChart({ data = [], height = 300, label = 'Portfolio Value' }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  useEffect(() => {
    if (!containerRef.current) return;

    try {
      const chart = createChart(containerRef.current, {
        autoSize: true,
        height,
        layout: {
          background: { color: 'transparent' },
          textColor: isDark ? COLORS.darkTextSecondary : '#6B7280',
          fontFamily: '"Inter", sans-serif',
          fontSize: 11,
          attributionLogo: false,
        },
        grid: {
          vertLines: { color: isDark ? COLORS.chartGridDark : COLORS.chartGridLight },
          horzLines: { color: isDark ? COLORS.chartGridDark : COLORS.chartGridLight },
        },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: {
            color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
            labelBackgroundColor: COLORS.pnlGreen,
          },
          horzLine: {
            color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
            labelBackgroundColor: COLORS.pnlGreen,
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

      chartRef.current = chart;

      const areaOptions = {
        lineColor: COLORS.pnlGreen,
        topColor: `${COLORS.pnlGreen}35`,
        bottomColor: `${COLORS.pnlGreen}00`,
        lineWidth: 2,
        priceLineVisible: false,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 5,
        crosshairMarkerBorderColor: COLORS.pnlGreen,
        crosshairMarkerBackgroundColor: isDark ? COLORS.darkSurface : COLORS.lightSurface,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
      };

      const series = typeof chart.addAreaSeries === 'function'
        ? chart.addAreaSeries(areaOptions)
        : chart.addSeries(AreaSeries, areaOptions);

      seriesRef.current = series;

      const cleanData = prepareEquityData(data);
      if (cleanData.length > 0) {
        series.setData(cleanData);
        chart.timeScale().fitContent();
      }

      // Explicit resize handle pass
      const handleResize = () => {
        if (containerRef.current && chartRef.current) {
          chartRef.current.timeScale().fitContent();
        }
      };
      const t = setTimeout(handleResize, 100);

      return () => {
        clearTimeout(t);
        try {
          chart.remove();
        } catch {
          // Ignore cleanup
        }
      };
    } catch (e) {
      console.warn("EquityCurveChart creation warning:", e);
    }
  }, [isDark, height]);

  // Update data without recreating chart
  useEffect(() => {
    if (seriesRef.current && data) {
      try {
        const cleanData = prepareEquityData(data);
        if (cleanData.length > 0) {
          seriesRef.current.setData(cleanData);
          chartRef.current?.timeScale().fitContent();
        }
      } catch (e) {
        console.warn("EquityCurveChart setData warning:", e);
      }
    }
  }, [data]);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: `${height}px`,
        minWidth: 0,
        position: 'relative',
      }}
    />
  );
}
