import { calculateMA } from "@/services/market/indicators";
import { fetchIndexPrices } from "@/services/market/stockData";
import type { MarketTrend } from "@/types/decision";

export type SignalWeights = {
  trend: number;
  momentum: number;
  volume: number;
};

const CACHE_MS = 5 * 60 * 1000;
let cachedRegime: { trend: MarketTrend; at: number } | null = null;

/** Normalized 0–1 volatility estimate from recent index returns. */
export function computeVolatilityFromPrices(prices: number[]): number {
  if (prices.length < 21) {
    return 0.5;
  }

  const window = prices.slice(-21);
  const returns: number[] = [];

  for (let index = 1; index < window.length; index += 1) {
    const previous = window[index - 1];
    if (previous <= 0) {
      continue;
    }

    returns.push((window[index] - previous) / previous);
  }

  if (returns.length === 0) {
    return 0.5;
  }

  const mean = returns.reduce((sum, value) => sum + value, 0) / returns.length;
  const variance =
    returns.reduce((sum, value) => sum + (value - mean) ** 2, 0) /
    returns.length;
  const stdDev = Math.sqrt(variance);

  return Math.min(1, Math.max(0, stdDev / 0.04));
}

export async function getMarketVolatility(): Promise<number> {
  const indexPrices = await fetchIndexPrices();
  return computeVolatilityFromPrices(indexPrices);
}

export async function getMarketVolatilitySafe(): Promise<number> {
  try {
    return await getMarketVolatility();
  } catch (error) {
    console.error("Market volatility lookup failed:", error);
    return 0.5;
  }
}

export function detectMarketTrend(indexPrices: number[]): MarketTrend {
  if (indexPrices.length < 200) {
    return "sideways";
  }

  const price = indexPrices[indexPrices.length - 1];
  const ma50 = calculateMA(indexPrices, 50);
  const ma200 = calculateMA(indexPrices, 200);

  if (price > ma50 && ma50 > ma200) {
    return "bullish";
  }
  if (price < ma50 && ma50 < ma200) {
    return "bearish";
  }
  return "sideways";
}

export function getDynamicWeights(trend: MarketTrend): SignalWeights {
  if (trend === "bullish") {
    return { trend: 0.5, momentum: 0.3, volume: 0.2 };
  }
  if (trend === "bearish") {
    return { trend: 0.3, momentum: 0.2, volume: 0.5 };
  }
  return { trend: 0.4, momentum: 0.3, volume: 0.3 };
}

export async function getMarketRegime(): Promise<MarketTrend> {
  if (cachedRegime && Date.now() - cachedRegime.at < CACHE_MS) {
    return cachedRegime.trend;
  }

  const indexPrices = await fetchIndexPrices();
  const trend =
    indexPrices.length >= 200
      ? detectMarketTrend(indexPrices)
      : "sideways";

  cachedRegime = { trend, at: Date.now() };
  return trend;
}
