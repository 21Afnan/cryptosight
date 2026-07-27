/**
 * sentimentMock.js
 * Primary symbols: BTC & ADA (scraped from r/Bitcoin, r/cardano, r/CryptoCurrency)
 * Processed via Hugging Face ModernFinBERT model (tabularisai/ModernFinBERT)
 */

// metadata.sentiment_data shape for active symbols in DB
export const SENTIMENT_DATA = [
  {
    symbol: 'BTC',
    total_posts: 1240,
    bullish_count: 815,
    bearish_count: 245,
    neutral_count: 180,
    last_updated: '2026-07-27T12:00:00Z',
    subreddit: 'r/Bitcoin',
  },
  {
    symbol: 'ADA',
    total_posts: 890,
    bullish_count: 512,
    bearish_count: 218,
    neutral_count: 160,
    last_updated: '2026-07-27T11:45:00Z',
    subreddit: 'r/cardano',
  },
];

// Current Fear & Greed Index
export const FEAR_GREED_CURRENT = {
  value: 69,
  label: 'Greed',
  timestamp: '2026-07-27T12:00:00Z',
};

// Fear & Greed timeline (last 90 days)
export const FEAR_GREED_TIMELINE = (() => {
  const data = [];
  let date = new Date('2026-04-27');
  let value = 54;
  for (let i = 0; i < 91; i++) {
    value += (Math.random() - 0.46) * 7;
    value = Math.max(15, Math.min(92, value));
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
  let date = new Date('2026-05-27');
  for (let i = 0; i < 62; i++) {
    const bull = 50 + Math.random() * 25;
    const bear = 15 + Math.random() * 20;
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
  let date = new Date('2026-06-27');
  for (let i = 0; i < 30; i++) {
    data.push({
      date: date.toISOString().split('T')[0],
      posts: Math.floor(60 + Math.random() * 120),
    });
    date.setDate(date.getDate() + 1);
  }
  return data;
})();

// News sentiment breakdown per day (last 30 days)
export const NEWS_SENTIMENT_DAILY = (() => {
  const data = [];
  let date = new Date('2026-06-27');
  for (let i = 0; i < 30; i++) {
    const total = Math.floor(60 + Math.random() * 120);
    const bullish = Math.floor(total * (0.55 + Math.random() * 0.2));
    const bearish = Math.floor(total * (0.15 + Math.random() * 0.15));
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
  { name: 'Bullish', value: 62.3, color: '#22C55E' },
  { name: 'Bearish', value: 21.7, color: '#EE5D5D' },
  { name: 'Neutral', value: 16.0, color: '#F0B90B' },
];

// Overall market sentiment summary
export const MARKET_SENTIMENT_SUMMARY = {
  overall_score: 69,
  overall_label: 'Bullish',
  total_posts_analyzed: 2130,
  total_bullish_pct: 62.3,
  total_bearish_pct: 21.7,
  total_neutral_pct: 16.0,
  last_updated: '2026-07-27T12:00:00Z',
  top_bullish_symbol: 'BTC',
  top_bearish_symbol: 'ADA',
  active_model: 'tabularisai/ModernFinBERT',
};

// Reddit Posts & AI FinBERT Classifications (BTC & ADA)
export const REDDIT_POSTS = [
  {
    post_id: 'btc_001',
    symbol: 'BTC',
    subreddit: 'r/Bitcoin',
    title: 'Bitcoin breaks key resistance level as institutional spot ETF inflows surge',
    body: 'On-chain signals and exchange reserve data indicate significant accumulation by long-term holders over the past 48 hours.',
    author: 'satoshi_quant',
    score: 1420,
    upvote_ratio: 0.94,
    num_comments: 184,
    sentiment: 'Bullish',
    confidence: 0.9624,
    created_utc: '2026-07-27T10:15:00Z',
    comments: [
      'ETF inflows are breaking records again!',
      'Solid support holding at the 21-day EMA.',
      'Institutional order book depth is super strong.'
    ]
  },
  {
    post_id: 'ada_001',
    symbol: 'ADA',
    subreddit: 'r/cardano',
    title: 'Cardano Hydra scaling upgrade milestone achieved with zero downtime',
    body: 'The developer team successfully validated state channels across testnet nodes, demonstrating throughput upgrades.',
    author: 'ada_dev_node',
    score: 890,
    upvote_ratio: 0.91,
    num_comments: 96,
    sentiment: 'Bullish',
    confidence: 0.9180,
    created_utc: '2026-07-27T09:40:00Z',
    comments: [
      'Hydra progress is looking really solid for DeFi protocols.',
      'Great milestone for the ecosystem.'
    ]
  },
  {
    post_id: 'btc_002',
    symbol: 'BTC',
    subreddit: 'r/CryptoCurrency',
    title: 'Macro uncertainty causes short-term leverage flush across perpetual futures',
    body: 'Over $120M in long positions liquidated as funding rates reset back to neutral levels.',
    author: 'macro_trader',
    score: 540,
    upvote_ratio: 0.85,
    num_comments: 112,
    sentiment: 'Bearish',
    confidence: 0.8845,
    created_utc: '2026-07-27T08:20:00Z',
    comments: [
      'Standard leverage flush before the next leg up.',
      'Keep an eye on open interest ratios.'
    ]
  },
  {
    post_id: 'ada_002',
    symbol: 'ADA',
    subreddit: 'r/CryptoCurrency',
    title: 'Cardano governance voting proposal opens for community treasury allocation',
    body: 'SPO nodes and CIP delegates begin voting on multi-sig treasury distribution parameters.',
    author: 'gov_observer',
    score: 310,
    upvote_ratio: 0.89,
    num_comments: 42,
    sentiment: 'Neutral',
    confidence: 0.8410,
    created_utc: '2026-07-27T07:00:00Z',
    comments: [
      'Voting delegates should check the proposal breakdown.',
      'Treasury governance is crucial.'
    ]
  },
  {
    post_id: 'btc_003',
    symbol: 'BTC',
    subreddit: 'r/Bitcoin',
    title: 'Lightning Network total capacity reaches new all-time high in BTC terms',
    body: 'Public channel capacity exceeded key threshold today with payment routing reliability improving across nodes.',
    author: 'lightning_fan',
    score: 1150,
    upvote_ratio: 0.96,
    num_comments: 135,
    sentiment: 'Bullish',
    confidence: 0.9450,
    created_utc: '2026-07-26T22:30:00Z',
    comments: [
      'Layer 2 adoption is compounding exponentially.',
      'Lower fees and instant settlement.'
    ]
  },
  {
    post_id: 'ada_003',
    symbol: 'ADA',
    subreddit: 'r/cardano',
    title: 'Cardano DeFi total value locked (TVL) climbs 15% month-over-month',
    body: 'DEX volume and synthetic asset protocols drive renewed user activity on mainnet.',
    author: 'defi_analyst',
    score: 670,
    upvote_ratio: 0.92,
    num_comments: 78,
    sentiment: 'Bullish',
    confidence: 0.9025,
    created_utc: '2026-07-26T18:15:00Z',
    comments: [
      'TVL growth without collateral liquidations is impressive.',
      'DeFi protocols are maturing nicely.'
    ]
  }
];
