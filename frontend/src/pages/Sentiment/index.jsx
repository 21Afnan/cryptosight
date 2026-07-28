import React, { useState, useMemo, useEffect } from 'react';
import Box from '@mui/material/Box';
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
import TableSortLabel from '@mui/material/TableSortLabel';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Stack from '@mui/material/Stack';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatCard from '../../components/ui/StatCard';
import StatusChip from '../../components/ui/StatusChip';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import EmptyState from '../../components/ui/EmptyState';
import { getSentimentSummary, getRedditPosts } from '../../api/sentimentApi';
import { COLORS } from '../../theme/theme';

// MUI Icons
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import ForumRoundedIcon from '@mui/icons-material/ForumRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import CheckCircleOutlineRoundedIcon from '@mui/icons-material/CheckCircleOutlineRounded';
import KeyboardArrowDownRoundedIcon from '@mui/icons-material/KeyboardArrowDownRounded';
import KeyboardArrowUpRoundedIcon from '@mui/icons-material/KeyboardArrowUpRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import CommentRoundedIcon from '@mui/icons-material/CommentRounded';
import ThumbUpAltRoundedIcon from '@mui/icons-material/ThumbUpAltRounded';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import SwapVertRoundedIcon from '@mui/icons-material/SwapVertRounded';

// Standard Financial Trading Palette (Vivid Green & Red)
const TRADING_PALETTE = {
  bullish: COLORS.pnlGreen,  // #22C55E (Standard Bullish Green)
  bearish: COLORS.pnlRed,    // #EE5D5D (Standard Bearish Red)
  neutral: COLORS.warning,   // #F59E0B (Standard Neutral Amber)
};

function formatTs(ts) {
  if (!ts) return '—';
  let s = String(ts).replace('T', ' ');
  if (s.includes('+00:00')) s = s.replace('+00:00', '');
  else if (s.includes('+00') && s.endsWith(':00')) s = s.split('+')[0];
  return s.trim();
}

// ─── Ultra-Clean Top 10 Post Table Row ───────────────────────────────────────
function CleanPostTableRow({ post, isDark, theme }) {
  const [open, setOpen] = useState(false);

  const isBullish = post.sentiment === 'Bullish';
  const isBearish = post.sentiment === 'Bearish';
  const chipColor = isBullish ? TRADING_PALETTE.bullish : isBearish ? TRADING_PALETTE.bearish : TRADING_PALETTE.neutral;
  const isBtc = post.symbol === 'BTC';

  return (
    <>
      <TableRow hover onClick={() => setOpen(!open)} sx={{ cursor: 'pointer' }}>
        <TableCell width={75}>
          <Chip
            label={post.symbol}
            size="small"
            sx={{
              fontWeight: 800,
              fontSize: 11,
              color: isBtc ? '#F7931A' : COLORS.accent,
              background: isBtc ? 'rgba(247, 147, 26, 0.15)' : 'rgba(94, 139, 110, 0.15)',
              border: `1px solid ${isBtc ? '#F7931A40' : '#5E8B6E40'}`,
            }}
          />
        </TableCell>
        <TableCell width={110}>
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary, fontSize: 12, fontWeight: 500 }}>
            {post.subreddit}
          </Typography>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: theme.palette.text.primary,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 320,
            }}
          >
            {post.title}
          </Typography>
        </TableCell>
        <TableCell align="right" width={95}>
          <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
            <ThumbUpAltRoundedIcon sx={{ fontSize: 13, color: theme.palette.text.secondary }} />
            <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontWeight: 700 }}>
              {post.score?.toLocaleString() ?? 0}
            </Typography>
          </Box>
        </TableCell>
        <TableCell align="center" width={110}>
          <StatusChip label={post.sentiment || 'Neutral'} status={post.sentiment || 'Neutral'} />
        </TableCell>
        <TableCell align="right" width={110}>
          <Typography variant="body2" sx={{ color: chipColor, fontWeight: 800, fontVariantNumeric: 'tabular-nums' }}>
            {(post.confidence * 100).toFixed(1)}%
          </Typography>
        </TableCell>
        <TableCell width={150} sx={{ whiteSpace: 'nowrap' }}>
          <Typography variant="body2" sx={{ fontSize: 12, color: theme.palette.text.secondary, fontVariantNumeric: 'tabular-nums' }}>
            {formatTs(post.created_utc)}
          </Typography>
        </TableCell>
        <TableCell width={100} align="center">
          <Button
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setOpen(!open);
            }}
            endIcon={open ? <KeyboardArrowUpRoundedIcon /> : <KeyboardArrowDownRoundedIcon />}
            sx={{ fontSize: 11, fontWeight: 700, textTransform: 'none', px: 1, color: COLORS.accent }}
          >
            {open ? 'Hide' : 'Comments'}
          </Button>
        </TableCell>
      </TableRow>

      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0, paddingLeft: 0, paddingRight: 0 }} colSpan={8}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box
              sx={{
                my: 1.5,
                mx: 0,
                p: 2.5,
                borderRadius: 3,
                background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
                boxSizing: 'border-box',
                width: '100%',
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: COLORS.accent }}>
                Cleaned Post Text & Context
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: theme.palette.text.secondary,
                  mb: 2,
                  lineHeight: 1.6,
                  wordBreak: 'break-word',
                  overflowWrap: 'anywhere',
                  whiteSpace: 'normal',
                }}
              >
                "{post.body || post.title}"
              </Typography>

              {post.comments && post.comments.length > 0 && (
                <Box sx={{ width: '100%' }}>
                  <Typography
                    variant="caption"
                    sx={{
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      color: theme.palette.text.secondary,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                      mb: 1,
                    }}
                  >
                    <CommentRoundedIcon sx={{ fontSize: 14 }} /> Top Scraped Comments ({post.comments.length})
                  </Typography>
                  <Stack spacing={1} sx={{ width: '100%' }}>
                    {post.comments.map((c, idx) => (
                      <Typography
                        key={idx}
                        variant="caption"
                        sx={{
                          color: theme.palette.text.primary,
                          fontSize: 12,
                          lineHeight: 1.5,
                          display: 'block',
                          wordBreak: 'break-word',
                          overflowWrap: 'anywhere',
                          whiteSpace: 'normal',
                        }}
                      >
                        • {c}
                      </Typography>
                    ))}
                  </Stack>
                </Box>
              )}
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

// ─── Main De-cluttered Live Sentiment Page Component ─────────────────────────
export default function Sentiment() {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  const [summaryData, setSummaryData] = useState(null);
  const [postsData, setPostsData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters, Sorting & Dynamic Symbol Selector
  const [selectedSymbol, setSelectedSymbol] = useState('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState('desc'); // 'desc' or 'asc'

  // Fetch real PostgreSQL data directly from FastAPI backend
  const fetchData = async () => {
    setLoading(true);
    try {
      const targetSym = selectedSymbol === 'ALL' ? '' : selectedSymbol;
      const [sumRes, postsRes] = await Promise.all([
        getSentimentSummary(),
        getRedditPosts(targetSym),
      ]);
      setSummaryData(sumRes);
      setPostsData(postsRes.data || []);
    } catch (err) {
      console.error('Error loading sentiment DB data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedSymbol]);

  const ms = summaryData?.market_summary;

  // Filter perSymbol to ONLY show active database symbols with total_posts > 0
  const perSymbol = useMemo(() => {
    return (summaryData?.per_symbol ?? []).filter((s) => s.total_posts > 0);
  }, [summaryData]);

  // Extract unique active symbols dynamically from PostgreSQL DB
  const availableSymbols = useMemo(() => {
    const symbolsFromDb = (perSymbol ?? []).map((s) => s.symbol.toUpperCase());
    const symbolsFromPosts = (postsData ?? []).map((p) => (p.symbol || '').toUpperCase()).filter(Boolean);
    const set = new Set([...symbolsFromDb, ...symbolsFromPosts]);
    return Array.from(set).sort();
  }, [perSymbol, postsData]);

  // Distribution chart data using standard trading Red/Green colors
  const distribution = useMemo(() => {
    const orig = summaryData?.distribution ?? [];
    return orig.map((item) => {
      let col = TRADING_PALETTE.neutral;
      if (item.name === 'Bullish') col = TRADING_PALETTE.bullish;
      if (item.name === 'Bearish') col = TRADING_PALETTE.bearish;
      return { ...item, color: col };
    });
  }, [summaryData]);

  // Strictly Top 10 Posts filtered by selected symbol, search & sorted by Upvotes (asc/desc)
  const top10Posts = useMemo(() => {
    let filtered = [...postsData];
    if (selectedSymbol !== 'ALL') {
      filtered = filtered.filter((p) => (p.symbol || '').toUpperCase() === selectedSymbol.toUpperCase());
    }

    if (selectedSentiment !== 'ALL') {
      filtered = filtered.filter((p) => (p.sentiment || '').toLowerCase() === selectedSentiment.toLowerCase());
    }

    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          (p.title && p.title.toLowerCase().includes(q)) ||
          (p.body && p.body.toLowerCase().includes(q))
      );
    }

    // Sort by Upvotes (score) according to sortOrder (desc vs asc)
    filtered.sort((a, b) => {
      const sA = Number(a.score || 0);
      const sB = Number(b.score || 0);
      return sortOrder === 'desc' ? sB - sA : sA - sB;
    });

    // Strictly slice Top 10
    return filtered.slice(0, 10);
  }, [postsData, selectedSymbol, selectedSentiment, searchTerm, sortOrder]);

  // Chart data: BTC vs ADA Comparison Bar Chart
  const comparisonChartData = useMemo(() => {
    return perSymbol.map((item) => ({
      symbol: item.symbol,
      Bullish: item.bullish_count,
      Bearish: item.bearish_count,
      Neutral: item.neutral_count,
    }));
  }, [perSymbol]);

  // Custom Theme Tooltip for Recharts
  const CustomChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    return (
      <Box
        sx={{
          background: isDark ? COLORS.darkSurface : COLORS.lightSurface,
          border: `1px solid ${isDark ? COLORS.darkBorder : COLORS.lightBorder}`,
          boxShadow: isDark ? '0 8px 32px rgba(0,0,0,0.6)' : '0 8px 24px rgba(94,139,110,0.15)',
          borderRadius: '14px',
          p: 1.5,
          minWidth: 140,
        }}
      >
        {label && (
          <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1, color: theme.palette.text.primary }}>
            {label}
          </Typography>
        )}
        {payload.map((entry) => (
          <Box key={entry.name || entry.dataKey} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, my: 0.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: entry.fill || entry.color }} />
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary, fontWeight: 600 }}>
                {entry.name || entry.dataKey}
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 800, color: entry.fill || entry.color, fontVariantNumeric: 'tabular-nums' }}>
              {entry.value}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  };

  if (loading) {
    return (
      <PageContainer title="Sentiment Analysis & Reddit NLP Engine">
        <Box sx={{ pt: 3 }}>
          <LoadingSkeleton variant="detail" />
        </Box>
      </PageContainer>
    );
  }

  return (
    <PageContainer title="Sentiment Analysis & Reddit NLP Engine" maxWidth="100%">
      <Box sx={{ pt: 1, width: '100%' }}>
        {/* Top Header Row */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
            PostgreSQL Sentiment Analytics (BTC & ADA)
          </Typography>
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
            Live NLP classifications powered by Hugging Face <Chip label="ModernFinBERT" size="small" sx={{ fontSize: 11, height: 22, fontWeight: 700 }} /> on active database symbols
          </Typography>
        </Box>

        {/* Top Executive Stat Cards (100% Full-Width Flexbox Row) */}
        <Box sx={{ display: 'flex', gap: 2.5, width: '100%', mb: 3.5, flexDirection: { xs: 'column', sm: 'row' } }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="Overall Mood"
              value={ms?.overall_label || 'N/A'}
              subtitle={`${ms?.total_bullish_pct ?? 0}% Bullish Ratio`}
              icon={<TrendingUpRoundedIcon />}
              bubbleColor={TRADING_PALETTE.bullish}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="Scraped Reddit Posts"
              value={ms?.total_posts_analyzed?.toLocaleString() || '0'}
              subtitle="Database Total Posts"
              icon={<ForumRoundedIcon />}
              bubbleColor={COLORS.accent}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="Top Bullish Symbol"
              value={ms?.top_bullish_symbol || 'N/A'}
              subtitle="Highest Bullish Ratio"
              icon={<CheckCircleOutlineRoundedIcon />}
              bubbleColor={TRADING_PALETTE.bullish}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <StatCard
              title="NLP AI Classifier"
              value="ModernFinBERT"
              subtitle="Hugging Face Transformer"
              icon={<PsychologyRoundedIcon />}
              bubbleColor="#93C5FD"
            />
          </Box>
        </Box>

        {/* Section 1: Visual Charts Showcase (Guaranteed 50/50 Full Width Flexbox Layout) */}
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <BarChartRoundedIcon sx={{ color: COLORS.accent }} /> Visual Sentiment Analytics & Comparison
        </Typography>

        <Box sx={{ display: 'flex', gap: 3, width: '100%', mb: 4, flexDirection: { xs: 'column', md: 'row' } }}>
          {/* Chart 1: BTC vs ADA Grouped Bar Chart (50% Width Flex) */}
          <Card sx={{ flex: 1, minWidth: 0 }}>
            <CardContent sx={{ p: '24px !important' }}>
              <Typography variant="h5" sx={{ mb: 2.5, fontWeight: 700 }}>
                BTC vs ADA Sentiment Breakdown Comparison
              </Typography>
              <Box sx={{ height: 290, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={isDark ? 0.08 : 0.15} />
                    <XAxis dataKey="symbol" tick={{ fill: theme.palette.text.secondary, fontWeight: 700, fontSize: 13 }} />
                    <YAxis tick={{ fill: theme.palette.text.secondary, fontSize: 12 }} />
                    <RechartsTooltip
                      content={<CustomChartTooltip />}
                      cursor={{ fill: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: 10, fontSize: 12 }} />
                    <Bar dataKey="Bullish" fill={TRADING_PALETTE.bullish} radius={[6, 6, 0, 0]} />
                    <Bar dataKey="Bearish" fill={TRADING_PALETTE.bearish} radius={[6, 6, 0, 0]} />
                    <Bar dataKey="Neutral" fill={TRADING_PALETTE.neutral} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>

          {/* Chart 2: Distribution Pie Chart (50% Width Flex) */}
          <Card sx={{ flex: 1, minWidth: 0 }}>
            <CardContent sx={{ p: '24px !important' }}>
              <Typography variant="h5" sx={{ mb: 2.5, fontWeight: 700 }}>
                Overall Sentiment Distribution Ratio
              </Typography>
              <Box sx={{ height: 290, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distribution}
                      cx="50%"
                      cy="45%"
                      outerRadius={105}
                      innerRadius={60}
                      dataKey="value"
                      nameKey="name"
                      paddingAngle={5}
                    >
                      {distribution.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip content={<CustomChartTooltip />} />
                    <Legend wrapperStyle={{ paddingTop: 10, fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Section 2: Top 10 High-Impact Reddit Posts Table */}
        <Card sx={{ mb: 4, width: '100%' }}>
          <CardContent sx={{ p: '24px !important' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5, flexWrap: 'wrap', gap: 2 }}>
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 800, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AutoAwesomeRoundedIcon sx={{ color: COLORS.accent }} /> Top 10 High-Impact Scraped Reddit Posts
                </Typography>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mt: 0.5 }}>
                  Clean, structured ranking by upvote score & ModernFinBERT AI confidence
                </Typography>
              </Box>

              {/* Filter Tabs, Search & Sort Toggle */}
              <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField
                  placeholder="Search titles..."
                  size="small"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchRoundedIcon sx={{ fontSize: 18, color: theme.palette.text.secondary }} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ width: 180 }}
                />

                {/* Upvotes Asc/Desc Quick Button */}
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<SwapVertRoundedIcon />}
                  onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                  sx={{ fontWeight: 700, fontSize: 11, textTransform: 'none', borderRadius: '8px', height: 36 }}
                >
                  Upvotes: {sortOrder === 'desc' ? 'High → Low' : 'Low → High'}
                </Button>

                {/* Dynamic Symbol Selector Dropdown */}
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel id="symbol-select-label" sx={{ fontSize: 12, fontWeight: 700 }}>Symbol</InputLabel>
                  <Select
                    labelId="symbol-select-label"
                    value={selectedSymbol}
                    label="Symbol"
                    onChange={(e) => setSelectedSymbol(e.target.value)}
                    sx={{ height: 36, borderRadius: '8px', fontSize: 12, fontWeight: 700 }}
                  >
                    <MenuItem value="ALL">All Active Symbols</MenuItem>
                    {availableSymbols.map((sym) => (
                      <MenuItem key={sym} value={sym}>
                        {sym} Top 10
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </Box>

            {/* Posts Showcase Table */}
            {top10Posts.length === 0 ? (
              <EmptyState title="No Top Posts Found" description="No scraped Reddit posts match the selected criteria in PostgreSQL." />
            ) : (
              <TableContainer sx={{ overflowX: 'auto', width: '100%' }}>
                <Table size="small" sx={{ width: '100%', minWidth: 780, tableLayout: 'fixed' }}>
                  <TableHead>
                    <TableRow>
                      <TableCell width={75}>Symbol</TableCell>
                      <TableCell width={110}>Subreddit</TableCell>
                      <TableCell>Post Title</TableCell>
                      <TableCell align="right" width={95}>
                        <TableSortLabel
                          active={true}
                          direction={sortOrder}
                          onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                        >
                          Upvotes
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="center" width={110}>AI Sentiment</TableCell>
                      <TableCell align="right" width={110}>FinBERT Score</TableCell>
                      <TableCell width={150} sx={{ whiteSpace: 'nowrap' }}>Post Date & Time</TableCell>
                      <TableCell width={100} align="center">Details</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {top10Posts.map((post, idx) => (
                      <CleanPostTableRow
                        key={post.post_id || idx}
                        post={post}
                        isDark={isDark}
                        theme={theme}
                      />
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Box>
    </PageContainer>
  );
}
