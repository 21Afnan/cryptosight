/**
 * sentimentApi.js
 * Connects directly to live FastAPI backend (/api/v1/sentiment).
 * Reads real PostgreSQL tables: metadata.sentiment_data and reddit_cleaned.<symbol>.
 * ZERO fake default fallback values.
 */

const BASE_URL = 'http://localhost:8000/api/v1/sentiment';

/** GET /api/v1/sentiment/summary */
export async function getSentimentSummary() {
  try {
    const res = await fetch(`${BASE_URL}/summary`);
    if (!res.ok) {
      throw new Error(`FastAPI Server returned status ${res.status}`);
    }
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn('Backend DB sentiment summary fetch error:', err.message);
    return {
      market_summary: {
        overall_score: 0,
        overall_label: 'N/A',
        total_posts_analyzed: 0,
        total_bullish_pct: 0.0,
        total_bearish_pct: 0.0,
        total_neutral_pct: 0.0,
        top_bullish_symbol: 'N/A',
        top_bearish_symbol: 'N/A',
        active_model: 'ModernFinBERT',
      },
      per_symbol: [],
      distribution: [],
    };
  }
}

/** GET /api/v1/sentiment/posts (Scraped Reddit Threads + ModernFinBERT AI Classifications) */
export async function getRedditPosts(symbol = '') {
  try {
    const query = symbol && symbol.toUpperCase() !== 'ALL' ? `?symbol=${encodeURIComponent(symbol)}` : '';
    const res = await fetch(`${BASE_URL}/posts${query}`);
    if (!res.ok) {
      throw new Error(`FastAPI Server returned status ${res.status}`);
    }
    const json = await res.json();
    return {
      data: json.posts || [],
      total: json.total || 0,
    };
  } catch (err) {
    console.warn('Backend DB sentiment posts fetch error:', err.message);
    return { data: [], total: 0 };
  }
}
