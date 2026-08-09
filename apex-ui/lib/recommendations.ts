import {
  normalizeSymbol,
  sectorForSymbol,
  STOCK_POOL,
  type StockProfile,
} from "@/lib/stockPool";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type { DecisionOpportunity } from "@/types/decision";
import type { Intent } from "@/types/intent";
import type { Portfolio } from "@/types/portfolio";

export type Recommendation = {
  name: string;
  type: string;
  reason: string;
};

export type RecommendationPortfolio = {
  holdings?: { symbol: string; allocation_pct?: number }[];
  top_symbol?: string;
  top_allocation_pct?: number;
};

type ScoredStock = {
  stock: StockProfile;
  score: number;
};

export const RECOMMENDATION_TOP_COUNT = 3;

function dailyJitter(symbol: string): number {
  const day = tradingDateKey();
  let hash = 0;

  for (const char of `${symbol}:${day}`) {
    hash = (hash * 31 + char.charCodeAt(0)) % 997;
  }

  return hash / 997;
}

function toRecommendation(stock: StockProfile): Recommendation {
  return {
    name: stock.name,
    type: stock.type,
    reason: stock.reason,
  };
}

function portfolioSectors(portfolio: RecommendationPortfolio): Set<string> {
  const sectors = new Set<string>();

  for (const holding of portfolio.holdings ?? []) {
    const sector = sectorForSymbol(holding.symbol);
    if (sector) {
      sectors.add(sector);
    }
  }

  const topSector = sectorForSymbol(portfolio.top_symbol);
  if (topSector) {
    sectors.add(topSector);
  }

  return sectors;
}

function heldSymbols(portfolio: RecommendationPortfolio): Set<string> {
  const symbols = new Set<string>();

  for (const holding of portfolio.holdings ?? []) {
    symbols.add(normalizeSymbol(holding.symbol));
  }

  if (portfolio.top_symbol) {
    symbols.add(normalizeSymbol(portfolio.top_symbol));
  }

  return symbols;
}

function scoreStock(
  stock: StockProfile,
  intent: Intent,
  risk: PortfolioRiskLevel,
  portfolio: RecommendationPortfolio,
): number {
  const topPct = portfolio.top_allocation_pct ?? 0;
  const concentrated = topPct > 50;
  const topSector = sectorForSymbol(portfolio.top_symbol);
  const held = heldSymbols(portfolio);
  const sectors = portfolioSectors(portfolio);

  let score = dailyJitter(stock.symbol);

  if (held.has(stock.symbol)) {
    score -= 4;
  }

  if (concentrated && topSector && stock.sector === topSector) {
    score -= 10;
  }

  if (intent === "grow") {
    score += stock.stability * 1.6;
    if (stock.cap === "large" || stock.cap === "etf") {
      score += 4;
    }
    if (concentrated && stock.cap === "etf") {
      score += 5;
    }
  }

  if (intent === "explore") {
    score += stock.growth * 1.6;
    if (!sectors.has(stock.sector)) {
      score += 4;
    }
  }

  if (risk === "High") {
    score += stock.stability * 0.8;
    if (stock.cap === "etf") {
      score += 3;
    }
  }

  return score;
}

function rankStocks(
  intent: Intent,
  risk: PortfolioRiskLevel,
  portfolio: RecommendationPortfolio,
): ScoredStock[] {
  return STOCK_POOL.map((stock) => ({
    stock,
    score: scoreStock(stock, intent, risk, portfolio),
  })).sort((a, b) => b.score - a.score);
}

function pickDiverseTop(
  ranked: ScoredStock[],
  limit: number,
): Recommendation[] {
  const picked: ScoredStock[] = [];
  const usedSectors = new Set<string>();

  for (const item of ranked) {
    if (picked.length >= limit) {
      break;
    }

    if (picked.length < limit - 1 && usedSectors.has(item.stock.sector)) {
      continue;
    }

    picked.push(item);
    usedSectors.add(item.stock.sector);
  }

  if (picked.length < limit) {
    for (const item of ranked) {
      if (picked.length >= limit) {
        break;
      }
      if (!picked.some((entry) => entry.stock.symbol === item.stock.symbol)) {
        picked.push(item);
      }
    }
  }

  return picked.slice(0, limit).map(({ stock }) => toRecommendation(stock));
}

export function portfolioContextFromHoldings(
  holdings: Portfolio["holdings"],
): RecommendationPortfolio {
  const totalValue = holdings.reduce(
    (sum, holding) => sum + holding.quantity * holding.currentPrice,
    0,
  );

  const enriched = holdings
    .map((holding) => {
      const value = holding.quantity * holding.currentPrice;
      return {
        symbol: holding.symbol,
        allocation_pct: totalValue > 0 ? (value / totalValue) * 100 : 0,
      };
    })
    .sort((a, b) => (b.allocation_pct ?? 0) - (a.allocation_pct ?? 0));

  const top = enriched[0];

  return {
    holdings: enriched,
    top_symbol: top?.symbol,
    top_allocation_pct: top?.allocation_pct,
  };
}

export function getAllRecommendations(
  intent: Intent,
  risk: PortfolioRiskLevel,
  portfolio: RecommendationPortfolio = {},
): Recommendation[] {
  if (intent !== "grow" && intent !== "explore") {
    return [];
  }

  const ranked = rankStocks(intent, risk, portfolio);

  if (intent === "explore") {
    const top = pickDiverseTop(ranked, ranked.length);
    return top;
  }

  return ranked.map(({ stock }) => toRecommendation(stock));
}

export function getRecommendations(
  intent: Intent,
  risk: PortfolioRiskLevel,
  portfolio: RecommendationPortfolio = {},
  limit = RECOMMENDATION_TOP_COUNT,
): Recommendation[] {
  if (intent !== "grow" && intent !== "explore") {
    return [];
  }

  const ranked = rankStocks(intent, risk, portfolio);

  if (intent === "explore") {
    return pickDiverseTop(ranked, limit);
  }

  return ranked.slice(0, limit).map(({ stock }) => toRecommendation(stock));
}

export function getOpportunities(
  intent: Intent,
  risk: PortfolioRiskLevel = "Low",
  portfolio: RecommendationPortfolio = {},
  limit = RECOMMENDATION_TOP_COUNT,
): DecisionOpportunity[] {
  return getRecommendations(intent, risk, portfolio, limit).map(
    ({ name, type }) => ({
      name,
      type,
    }),
  );
}
