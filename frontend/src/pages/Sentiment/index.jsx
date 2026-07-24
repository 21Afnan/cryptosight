import React from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import EmptyState from '../../components/ui/EmptyState';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import SentimentGauge from '../../components/charts/SentimentGauge';
import SentimentTimelineChart from '../../components/charts/SentimentTimelineChart';
import FearGreedTimelineChart from '../../components/charts/FearGreedTimelineChart';
import NewsVolumeChart from '../../components/charts/NewsVolumeChart';
import NewsSentimentChart from '../../components/charts/NewsSentimentChart';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getSentimentSummary, getFearGreed, getSentimentTimeline, getNewsVolume, getNewsSentiment } from '../../api/sentimentApi';
import { COLORS } from '../../theme/theme';

import SentimentSatisfiedRoundedIcon from '@mui/icons-material/SentimentSatisfiedRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

function SectionTitle({ children }) {
  return <Typography variant="h4" sx={{ fontWeight: 700, mb: 2, mt: 1 }}>{children}</Typography>;
}

function ChartCard({ title, children, height = 240, minHeight }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: '20px !important' }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>{title}</Typography>
        <Box sx={{ height: height ?? minHeight }}>{children}</Box>
      </CardContent>
    </Card>
  );
}

export default function Sentiment() {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const { data: summary, loading: loadingSum } = useMockFetch(getSentimentSummary);
  const { data: fearGreed, loading: loadingFG } = useMockFetch(getFearGreed);
  const { data: timeline, loading: loadingTL } = useMockFetch(getSentimentTimeline);
  const { data: newsVol, loading: loadingNV } = useMockFetch(getNewsVolume);
  const { data: newsSent, loading: loadingNS } = useMockFetch(getNewsSentiment);

  const loading = loadingSum || loadingFG || loadingTL || loadingNV || loadingNS;

  const ms = summary?.market_summary;
  const perSymbol = summary?.per_symbol ?? [];
  const distribution = summary?.distribution ?? [];
  const fg = fearGreed?.current;
  const fgTimeline = fearGreed?.timeline ?? [];
  const tlData = timeline?.data ?? [];
  const nvData = newsVol?.data ?? [];
  const nsData = newsSent?.data ?? [];

  const CustomPieTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    return (
      <Box sx={{ background: isDark ? COLORS.darkSurface : COLORS.lightSurface, border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`, borderRadius: 2, p: 1.5, fontSize: 12 }}>
        <Typography variant="body2" sx={{ fontWeight: 700, color: payload[0].payload.color }}>{payload[0].name}: {payload[0].value}%</Typography>
      </Box>
    );
  };

  const renderPieLegend = ({ payload }) => (
    <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
      {payload?.map((entry) => (
        <Box key={entry.value} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', background: entry.color }} />
          <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>{entry.value}</Typography>
        </Box>
      ))}
    </Box>
  );

  if (loading) return (
    <PageContainer title="Sentiment Analysis">
      <Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box>
    </PageContainer>
  );

  return (
    <PageContainer title="Sentiment Analysis">
      <Box sx={{ pt: 3 }}>
        {/* Fear & Greed + Market Summary + Sentiment Distribution */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {/* Gauge (4 cols) */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CardContent sx={{ p: '24px !important', textAlign: 'center' }}>
                <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Fear & Greed Index</Typography>
                <SentimentGauge value={fg?.value ?? 50} size={250} />
                <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mt: 1.5 }}>
                  Last updated: {fg?.timestamp ? new Date(fg.timestamp).toLocaleString() : '—'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Market summary card (4 cols) */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: '20px !important' }}>
                <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Market Overview</Typography>
                {[
                  { label: 'Overall Score', value: ms?.overall_score, color: COLORS.pnlGreen },
                  { label: 'Overall Mood', value: ms?.overall_label },
                  { label: 'Posts Analyzed', value: ms?.total_posts_analyzed?.toLocaleString() },
                  { label: 'Bullish %', value: ms?.total_bullish_pct != null ? `${ms.total_bullish_pct.toFixed(1)}%` : '—', color: COLORS.pnlGreen },
                  { label: 'Bearish %', value: ms?.total_bearish_pct != null ? `${ms.total_bearish_pct.toFixed(1)}%` : '—', color: COLORS.pnlRed },
                  { label: 'Neutral %', value: ms?.total_neutral_pct != null ? `${ms.total_neutral_pct.toFixed(1)}%` : '—', color: COLORS.warning },
                  { label: 'Top Bullish Symbol', value: ms?.top_bullish_symbol, color: COLORS.pnlGreen },
                  { label: 'Top Bearish Symbol', value: ms?.top_bearish_symbol, color: COLORS.pnlRed },
                  { label: 'Last Updated', value: ms?.last_updated ? new Date(ms.last_updated).toLocaleString() : '—' },
                ].map(({ label, value, color }) => (
                  <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.75, borderBottom: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}` }}>
                    <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>{label}</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: color || theme.palette.text.primary }}>{value ?? '—'}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>

          {/* Distribution pie (4 cols) */}
          <Grid item xs={12} md={4}>
            <ChartCard title="Sentiment Distribution" height={300}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={distribution} cx="50%" cy="45%" outerRadius={105} innerRadius={58} dataKey="value" nameKey="name" paddingAngle={3}>
                    {distribution.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} />
                  <Legend content={renderPieLegend} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </Grid>
        </Grid>

        {/* Sentiment Timeline (Expanded Height) */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>Bullish / Neutral / Bearish Timeline (60d)</Typography>
            <Box sx={{ height: 280 }}>
              <SentimentTimelineChart data={tlData} height={280} />
            </Box>
          </CardContent>
        </Card>

        {/* News sections */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <ChartCard title="Daily News Volume (Posts)" height={260}>
              <NewsVolumeChart data={nvData} height={260} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="News Sentiment Breakdown" height={260}>
              <NewsSentimentChart data={nsData} height={260} />
            </ChartCard>
          </Grid>
        </Grid>

        {/* Per-symbol breakdown */}
        <Card>
          <CardContent sx={{ p: '20px !important' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>News Sentiment — Per Symbol</Typography>
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Subreddit</TableCell>
                    <TableCell align="right">Total Posts</TableCell>
                    <TableCell align="right">Bullish</TableCell>
                    <TableCell align="right">Bearish</TableCell>
                    <TableCell align="right">Neutral</TableCell>
                    <TableCell align="right">Bullish %</TableCell>
                    <TableCell>Last Updated</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {perSymbol.map((row) => {
                    const bullPct = row.total_posts > 0 ? (row.bullish_count / row.total_posts * 100).toFixed(1) : '—';
                    return (
                      <TableRow key={row.symbol} hover>
                        <TableCell>
                          <Chip label={row.symbol} size="small" sx={{ color: COLORS.accent, background: `${COLORS.accent}15`, fontSize: 11 }} />
                        </TableCell>
                        <TableCell><Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>{row.subreddit}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>{row.total_posts?.toLocaleString()}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: COLORS.pnlGreen, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{row.bullish_count?.toLocaleString()}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: COLORS.pnlRed, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{row.bearish_count?.toLocaleString()}</Typography></TableCell>
                        <TableCell align="right"><Typography variant="body2" sx={{ color: COLORS.warning, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{row.neutral_count?.toLocaleString()}</Typography></TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: COLORS.pnlGreen, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                            {bullPct}%
                          </Typography>
                        </TableCell>
                        <TableCell><Typography variant="body2" sx={{ fontSize: 12, color: theme.palette.text.secondary }}>{new Date(row.last_updated).toLocaleString()}</Typography></TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>
    </PageContainer>
  );
}
