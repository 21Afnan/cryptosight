/**
 * sentimentMock.js
 * Mirrors: metadata.sentiment_data
 * Also includes Fear & Greed timeline, sentiment history, news volume
 */

// metadata.sentiment_data shape
export const SENTIMENT_DATA = [
  {
    symbol: 'BTC',
    total_posts: 14820,
    bullish_count: 8234,
    bearish_count: 3812,
    neutral_count: 2774,
    last_updated: '2025-07-01T10:00:00Z',
    subreddit: 'r/Bitcoin',
  },
  {
    symbol: 'ETH',
    total_posts: 9312,
    bullish_count: 4801,
    bearish_count: 2914,
    neutral_count: 1597,
    last_updated: '2025-07-01T10:00:00Z',
    subreddit: 'r/ethereum',
  },
  {
    symbol: 'SOL',
    total_posts: 5240,
    bullish_count: 2987,
    bearish_count: 1421,
    neutral_count: 832,
    last_updated: '2025-07-01T09:30:00Z',
    subreddit: 'r/solana',
  },
  {
    symbol: 'DOGE',
    total_posts: 3890,
    bullish_count: 1824,
    bearish_count: 1340,
    neutral_count: 726,
    last_updated: '2025-07-01T09:00:00Z',
    subreddit: 'r/dogecoin',
  },
  {
    symbol: 'AVAX',
    total_posts: 2140,
    bullish_count: 1082,
    bearish_count: 712,
    neutral_count: 346,
    last_updated: '2025-07-01T08:00:00Z',
    subreddit: 'r/Avax',
  },
];

// Current Fear & Greed Index
export const FEAR_GREED_CURRENT = {
  value: 68,
  label: 'Greed',
  timestamp: '2025-07-01T10:00:00Z',
};

// Fear & Greed timeline (last 90 days)
export const FEAR_GREED_TIMELINE = (() => {
  const data = [];
  let date = new Date('2025-04-01');
  let value = 52;
  for (let i = 0; i < 91; i++) {
    value += (Math.random() - 0.46) * 8;
    value = Math.max(10, Math.min(95, value));
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(value),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
})();

// Historical sentiment timeline (last 60 days)
export const SENTIMENT_TIMELINE = (() => {
  const data = [];
  let date = new Date('2025-05-01');
  for (let i = 0; i < 62; i++) {
    const bull = 35 + Math.random() * 30;
    const bear = 15 + Math.random() * 25;
    const neutral = 100 - bull - bear;
    data.push({
      date: date.toISOString().split('T')[0],
      bullish: parseFloat(bull.toFixed(1)),
      bearish: parseFloat(Math.max(5, bear).toFixed(1)),
      neutral: parseFloat(Math.max(5, neutral).toFixed(1)),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
})();

// News / post volume (last 30 days)
export const NEWS_VOLUME = (() => {
  const data = [];
  let date = new Date('2025-06-01');
  for (let i = 0; i < 30; i++) {
    data.push({
      date: date.toISOString().split('T')[0],
      posts: Math.floor(400 + Math.random() * 800),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
})();

// News sentiment breakdown per day (last 30 days)
export const NEWS_SENTIMENT_DAILY = (() => {
  const data = [];
  let date = new Date('2025-06-01');
  for (let i = 0; i < 30; i++) {
    const total = Math.floor(400 + Math.random() * 800);
    const bullish = Math.floor(total * (0.35 + Math.random() * 0.25));
    const bearish = Math.floor(total * (0.15 + Math.random() * 0.2));
    const neutral = total - bullish - bearish;
    data.push({
      date: date.toISOString().split('T')[0],
      bullish,
      bearish,
      neutral,
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
})();

// Sentiment distribution for pie chart
export const SENTIMENT_DISTRIBUTION = [
  { name: 'Bullish', value: 55.6, color: '#22C55E' },
  { name: 'Neutral', value: 25.8, color: '#F0B90B' },
  { name: 'Bearish', value: 18.6, color: '#F43F5E' },
];

// Overall market sentiment summary
export const MARKET_SENTIMENT_SUMMARY = {
  overall_score: 68,
  overall_label: 'Bullish',
  total_posts_analyzed: 35402,
  total_bullish_pct: 55.6,
  total_bearish_pct: 18.6,
  total_neutral_pct: 25.8,
  last_updated: '2025-07-01T10:00:00Z',
  top_bullish_symbol: 'BTC',
  top_bearish_symbol: 'DOGE',
};
