/**
 * sentimentApi.js
 * Mirrors: GET /sentiment/summary, GET /sentiment/fear-greed, GET /sentiment/timeline
 */
import {
  SENTIMENT_DATA,
  FEAR_GREED_CURRENT,
  FEAR_GREED_TIMELINE,
  SENTIMENT_TIMELINE,
  NEWS_VOLUME,
  NEWS_SENTIMENT_DAILY,
  SENTIMENT_DISTRIBUTION,
  MARKET_SENTIMENT_SUMMARY,
} from '../mock/sentimentMock';

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

/** GET /sentiment/summary */
export async function getSentimentSummary() {
  await delay(300 + Math.random() * 150);
  return {
    market_summary: { ...MARKET_SENTIMENT_SUMMARY },
    per_symbol: [...SENTIMENT_DATA],
    distribution: [...SENTIMENT_DISTRIBUTION],
  };
}

/** GET /sentiment/fear-greed */
export async function getFearGreed() {
  await delay(200 + Math.random() * 100);
  return {
    current: { ...FEAR_GREED_CURRENT },
    timeline: [...FEAR_GREED_TIMELINE],
  };
}

/** GET /sentiment/timeline */
export async function getSentimentTimeline() {
  await delay(250 + Math.random() * 100);
  return {
    data: [...SENTIMENT_TIMELINE],
    total: SENTIMENT_TIMELINE.length,
    page: 1,
    pageSize: SENTIMENT_TIMELINE.length,
  };
}

/** GET /sentiment/news-volume */
export async function getNewsVolume() {
  await delay(200 + Math.random() * 100);
  return { data: [...NEWS_VOLUME], total: NEWS_VOLUME.length, page: 1, pageSize: NEWS_VOLUME.length };
}

/** GET /sentiment/news-sentiment */
export async function getNewsSentiment() {
  await delay(200 + Math.random() * 100);
  return { data: [...NEWS_SENTIMENT_DAILY], total: NEWS_SENTIMENT_DAILY.length, page: 1, pageSize: NEWS_SENTIMENT_DAILY.length };
}
