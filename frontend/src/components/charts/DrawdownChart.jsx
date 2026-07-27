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
      const getContainerWidth = () => {
        if (!containerRef.current) return 600;
        const cardContent = containerRef.current.closest('.MuiCardContent-root');
        if (cardContent) {
          const cardWidth = cardContent.getBoundingClientRect().width;
          const isHalf = Boolean(containerRef.current.closest('.MuiGrid-item'));
          const calculatedWidth = isHalf ? (cardWidth - 56) / 2 : (cardWidth - 32);
          if (calculatedWidth > 200) return calculatedWidth;
        }
        const parent = containerRef.current.parentElement;
        if (parent && parent.clientWidth > 200) {
          return parent.clientWidth - 16;
        }
        return 600;
      };

      const initialWidth = getContainerWidth();

      const chart = createChart(containerRef.current, {
        width: initialWidth,
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
          vertLine: { color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)', labelBackgroundColor: COLORS.pnlRed },
          horzLine: { color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)', labelBackgroundColor: COLORS.pnlRed },
        },
        rightPriceScale: {
          borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
          textColor: isDark ? COLORS.darkTextSecondary : '#6B7280',
          scaleMargins: { top: 0.15, bottom: 0.15 },
        },
        localization: {
          timeFormatter: (time) => {
            if (typeof time === 'number') {
              const d = new Date(time * 1000);
              const m = d.toLocaleString('en-US', { month: 'short' });
              const day = String(d.getDate()).padStart(2, '0');
              const yr = String(d.getFullYear()).slice(-2);
              const hrs = String(d.getHours()).padStart(2, '0');
              const mins = String(d.getMinutes()).padStart(2, '0');
              return `${day} ${m} '${yr}, ${hrs}:${mins}`;
            }
            return String(time).replace('Z', '').replace('UTC', '').trim();
          },
        },
        timeScale: {
          borderColor: isDark ? COLORS.darkBorder : COLORS.lightBorder,
          timeVisible: true,
          secondsVisible: false,
        },
      });

      chartRef.current = chart;

      const areaOptions = {
        lineColor: COLORS.pnlRed,
        topColor: `${COLORS.pnlRed}00`,
        bottomColor: `${COLORS.pnlRed}35`,
        lineWidth: 2,
        priceLineVisible: false,
        priceFormat: {
          type: 'custom',
          formatter: (price) => `${(price * 100).toFixed(2)}%`,
        },
        autoscaleInfoProvider: (original) => {
          const res = original();
          if (res && res.priceRange) {
            const { minValue, maxValue } = res.priceRange;
            if (minValue === 0 && maxValue === 0) {
              return {
                priceRange: {
                  minValue: -0.1,
                  maxValue: 0.02,
                },
              };
            }
          }
          return res;
        },
      };

      const series = typeof chart.addAreaSeries === 'function'
        ? chart.addAreaSeries(areaOptions)
        : chart.addSeries(AreaSeries, areaOptions);

      seriesRef.current = series;

      // Deduplicate by time and keep last value per day, then sort strictly ascending
      const cleanData = [];
      const map = new Map();
      const rawList = Array.isArray(data) ? data : (data?.raw_values || data?.values || data?.data || []);
      rawList.forEach((item) => {
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

      // Guarantee at least 2 points for lightweight-charts area series rendering
      if (cleanData.length === 1) {
        const dt = new Date(cleanData[0].time);
        dt.setDate(dt.getDate() - 1);
        const prevStr = dt.toISOString().split('T')[0];
        cleanData.unshift({ time: prevStr, value: 0.0 });
      }

      if (cleanData.length > 0) {
        series.setData(cleanData);
        chart.timeScale().fitContent();
      }

      const handleResize = () => {
        if (containerRef.current && chartRef.current) {
          const w = getContainerWidth();
          if (w > 0) {
            chartRef.current.applyOptions({ width: w });
            chartRef.current.timeScale().fitContent();
          }
        }
      };

      const resizeTimer = setTimeout(handleResize, 30);
      const resizeTimer2 = setTimeout(handleResize, 150);
      const resizeTimer3 = setTimeout(handleResize, 400);

      const ro = new ResizeObserver(() => {
        handleResize();
      });

      const cardContent = containerRef.current.closest('.MuiCardContent-root');
      if (cardContent) ro.observe(cardContent);
      ro.observe(containerRef.current);

      window.addEventListener('resize', handleResize);

      return () => {
        clearTimeout(resizeTimer);
        clearTimeout(resizeTimer2);
        clearTimeout(resizeTimer3);
        window.removeEventListener('resize', handleResize);
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
    if (seriesRef.current && data) {
      try {
        const clean = [];
        const map = new Map();
        const rawList = Array.isArray(data) ? data : (data?.raw_values || data?.values || data?.data || []);
        rawList.forEach((item) => {
          if (!item || item.time == null) return;
          const timeStr = String(item.time).split(' ')[0].split('T')[0];
          const val = Number(item.value ?? 0);
          if (timeStr && !isNaN(val)) {
            map.set(timeStr, val);
          }
        });
        map.forEach((val, timeStr) => clean.push({ time: timeStr, value: val }));
        clean.sort((a, b) => (a.time > b.time ? 1 : a.time < b.time ? -1 : 0));

        if (clean.length === 1) {
          const dt = new Date(clean[0].time);
          dt.setDate(dt.getDate() - 1);
          clean.unshift({ time: dt.toISOString().split('T')[0], value: 0.0 });
        }

        if (clean.length > 0) {
          seriesRef.current.setData(clean);
          chartRef.current?.timeScale().fitContent();
        }
      } catch (e) {
        console.warn("DrawdownChart setData warning:", e);
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
