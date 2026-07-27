import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { createChart, CrosshairMode, AreaSeries } from 'lightweight-charts';
import { COLORS } from '../../theme/theme';

/**
 * Robust data cleaner that converts raw points into strictly ascending, 
 * unique time points (unix timestamps in seconds or YYYY-MM-DD strings) 
 * suitable for lightweight-charts area series.
 */
function prepareEquityData(data) {
  const rawList = Array.isArray(data) ? data : (data?.raw_values || data?.values || data?.data || []);
  if (!rawList.length) return [];

  const points = [];
  rawList.forEach((item) => {
    if (!item || item.time == null) return;
    let t = item.time;
    // Check if unix timestamp (int/float) or YYYY-MM-DD string
    if (typeof t === 'string' && t.includes('-')) {
      t = t.split(' ')[0].split('T')[0];
    } else {
      t = Number(t);
    }
    const val = Number(item.value ?? 0);
    if (!isNaN(val)) {
      points.push({ time: t, value: val });
    }
  });

  if (!points.length) return [];

  // Sort ascending by time
  points.sort((a, b) => (a.time > b.time ? 1 : a.time < b.time ? -1 : 0));

  // Deduplicate exact duplicate timestamps by adding 1 second or preserving order
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

  // If only 1 point, add a baseline point 1 minute prior with identical value
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

      return () => {
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
    <Box
      ref={containerRef}
      sx={{
        width: '100%',
        height,
        minWidth: 0,
        '& .tv-lightweight-charts': { width: '100% !important' },
      }}
    />
  );
}
