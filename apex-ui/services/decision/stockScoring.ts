import { calculateMA, calculateRSI } from "@/services/market/indicators";
import {
  getDynamicWeights,
  getMarketRegime,
  type SignalWeights,
} from "@/services/market/regime";
import { resolveScoringWeights } from "@/services/decision/selfLearning";
import { fetchStockData } from "@/services/market/stockData";
import { buildEntryInputFromMarketData } from "@/services/execution/entryTiming";
import { getFilteredShortlist } from "@/services/decision/opportunityEngine";
import { normalizeSymbol, sectorForSymbol } from "@/lib/stockPool";
import type { RecommendationPortfolio } from "@/lib/recommendations";
import type { Signals, StockPick } from "@/types/decision";

export { STOCK_UNIVERSE } from "@/services/decision/nifty50";
export { getStockUniverse, NIFTY_50_UNIVERSE } from "@/services/decision/nifty50";

export type PortfolioHoldingWeight = {
  stock: string;
  weight: number;
  sector?: string;
};

export type PortfolioScoringContext = {
  holdings: PortfolioHoldingWeight[];
  holdingsCount: number;
};

const NEUTRAL_SIGNALS: Signals = { trend: 50, momentum: 50, volume: 50 };

function calculateVolumeScore(volumes: number[]): number {
  if (volumes.length === 0) {
    return 50;
  }

  const avg = volumes.reduce((a, b) => a + b, 0) / volumes.length;
  const latest = volumes[volumes.length - 1];

  if (latest > avg * 1.5) {
    return 80;
  }
  if (latest > avg) {
    return 65;
  }
  return 50;
}

export function portfolioScoringContextFromRecommendation(
  portfolio?: RecommendationPortfolio | null,
): PortfolioScoringContext | null {
  const holdings = portfolio?.holdings ?? [];

  if (holdings.length === 0) {
    return null;
  }

  return {
    holdings: holdings.map((holding) => ({
      stock: normalizeSymbol(holding.symbol),
      weight: holding.allocation_pct ?? 0,
      sector: sectorForSymbol(holding.symbol) ?? undefined,
    })),
    holdingsCount: holdings.length,
  };
}

export function getPortfolioFitScore(
  stock: string,
  portfolio: PortfolioScoringContext,
): number {
  let score = 100;
  const normalized = normalizeSymbol(stock);
  const holding = portfolio.holdings.find(
    (entry) => normalizeSymbol(entry.stock) === normalized,
  );

  if (holding && holding.weight > 25) {
    score -= 40;
  }

  if (holding) {
    score -= 20;
  }

  if (!holding) {
    score += 10;
  }

  return Math.max(0, Math.min(100, score));
}

export async function getSignalsForStock(stock: string): Promise<Signals> {
  const data = await fetchStockData(stock);

  if (!data || data.prices.length < 50) {
    return NEUTRAL_SIGNALS;
  }

  const price = data.prices[data.prices.length - 1];
  const ma50 = calculateMA(data.prices, 50);
  const rsi = calculateRSI(data.prices);
  const volumeScore = calculateVolumeScore(data.volumes);

  return {
    trend: price > ma50 ? 80 : 40,
    momentum: Math.round(rsi),
    volume: volumeScore,
  };
}

export async function scoreStock(
  stock: string,
  weights: SignalWeights = getDynamicWeights("sideways"),
  portfolio?: PortfolioScoringContext | null,
): Promise<StockPick> {
  const data = await fetchStockData(stock);
  const signals =
    data && data.prices.length >= 50
      ? (() => {
          const price = data.prices[data.prices.length - 1];
          const ma50 = calculateMA(data.prices, 50);
          const rsi = calculateRSI(data.prices);
          const volumeScore = calculateVolumeScore(data.volumes);
          return {
            trend: price > ma50 ? 80 : 40,
            momentum: Math.round(rsi),
            volume: volumeScore,
          };
        })()
      : NEUTRAL_SIGNALS;
  const entryInput =
    data && data.prices.length >= 21
      ? buildEntryInputFromMarketData(data.prices, data.volumes)
      : null;

  const marketScore =
    signals.trend * weights.trend +
    signals.momentum * weights.momentum +
    signals.volume * weights.volume;

  let finalScore = marketScore;

  if (portfolio) {
    const portfolioScore = getPortfolioFitScore(stock, portfolio);
    finalScore = marketScore * 0.7 + portfolioScore * 0.3;
  }

  return {
    stock,
    score: Math.round(finalScore),
    signals,
    price: entryInput?.price,
    activationLevel: entryInput?.recentHigh,
  };
}

export async function rankStocks(
  portfolio?: PortfolioScoringContext | null,
  adaptiveWeights?: SignalWeights | null,
): Promise<StockPick[]> {
  const regime = await getMarketRegime();
  const weights = resolveScoringWeights(regime, adaptiveWeights);
  const shortlist = await getFilteredShortlist();
  const results = await Promise.all(
    shortlist.map((stock) => scoreStock(stock, weights, portfolio)),
  );
  return results.sort((a, b) => b.score - a.score);
}

export async function getTopPicks(
  limit = 5,
  portfolio?: PortfolioScoringContext | null,
  adaptiveWeights?: SignalWeights | null,
): Promise<StockPick[]> {
  const ranked = await rankStocks(portfolio, adaptiveWeights);
  return ranked.slice(0, limit);
}

export { getMarketRegime } from "@/services/market/regime";
