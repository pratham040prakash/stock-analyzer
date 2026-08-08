import { fetchStockData } from "@/services/market/stockData";

export type MarketStructure = {
  supportLevels: number[];
  resistanceLevels: number[];
};

export type StructureAnalysis = {
  structureScore: number;
  supportLevels: number[];
  resistanceLevels: number[];
  nearestSupportDistancePct: number | null;
  nearestResistanceDistancePct: number | null;
  breakoutAboveResistance: boolean;
  breakdownBelowSupport: boolean;
};

const NEUTRAL_SCORE = 50;
const MIN_CANDLES = 10;
const MAX_CANDLES = 100;
const LOCAL_EXTREMA_WINDOW = 2;
const CLUSTER_TOLERANCE_PCT = 0.015;
const PROXIMITY_THRESHOLD_PCT = 2;
const NEAR_SUPPORT_BONUS = 20;
const NEAR_RESISTANCE_PENALTY = 20;
const BREAKOUT_BONUS = 30;
const BREAKDOWN_PENALTY = 30;

function clampScore(score: number): number {
  return Math.min(100, Math.max(0, Math.round(score)));
}

function sliceRecentPrices(prices: number[]): number[] {
  if (prices.length <= MAX_CANDLES) {
    return prices;
  }

  return prices.slice(-MAX_CANDLES);
}

function findLocalHighs(prices: number[]): number[] {
  const highs: number[] = [];

  for (
    let index = LOCAL_EXTREMA_WINDOW;
    index < prices.length - LOCAL_EXTREMA_WINDOW;
    index += 1
  ) {
    const value = prices[index];
    let isHigh = true;

    for (let offset = 1; offset <= LOCAL_EXTREMA_WINDOW; offset += 1) {
      if (
        value <= prices[index - offset] ||
        value <= prices[index + offset]
      ) {
        isHigh = false;
        break;
      }
    }

    if (isHigh) {
      highs.push(value);
    }
  }

  return highs;
}

function findLocalLows(prices: number[]): number[] {
  const lows: number[] = [];

  for (
    let index = LOCAL_EXTREMA_WINDOW;
    index < prices.length - LOCAL_EXTREMA_WINDOW;
    index += 1
  ) {
    const value = prices[index];
    let isLow = true;

    for (let offset = 1; offset <= LOCAL_EXTREMA_WINDOW; offset += 1) {
      if (
        value >= prices[index - offset] ||
        value >= prices[index + offset]
      ) {
        isLow = false;
        break;
      }
    }

    if (isLow) {
      lows.push(value);
    }
  }

  return lows;
}

function clusterLevels(levels: number[]): number[] {
  if (levels.length === 0) {
    return [];
  }

  const sorted = [...levels].sort((a, b) => a - b);
  const clusters: number[] = [];
  let clusterSum = sorted[0];
  let clusterCount = 1;
  let clusterAnchor = sorted[0];

  for (let index = 1; index < sorted.length; index += 1) {
    const level = sorted[index];
    const tolerance = clusterAnchor * CLUSTER_TOLERANCE_PCT;

    if (Math.abs(level - clusterAnchor) <= tolerance) {
      clusterSum += level;
      clusterCount += 1;
    } else {
      clusters.push(clusterSum / clusterCount);
      clusterSum = level;
      clusterCount = 1;
      clusterAnchor = level;
    }
  }

  clusters.push(clusterSum / clusterCount);

  return clusters.sort((a, b) => a - b);
}

export function detectSupportResistance(prices: number[]): MarketStructure {
  const recent = sliceRecentPrices(prices);

  if (recent.length < MIN_CANDLES) {
    return { supportLevels: [], resistanceLevels: [] };
  }

  return {
    supportLevels: clusterLevels(findLocalLows(recent)),
    resistanceLevels: clusterLevels(findLocalHighs(recent)),
  };
}

export function getProximity(price: number, levels: number[]): number | null {
  if (!Number.isFinite(price) || price <= 0 || levels.length === 0) {
    return null;
  }

  let minDistancePct = Number.POSITIVE_INFINITY;

  for (const level of levels) {
    if (!Number.isFinite(level) || level <= 0) {
      continue;
    }

    const distancePct = (Math.abs(price - level) / price) * 100;

    if (distancePct < minDistancePct) {
      minDistancePct = distancePct;
    }
  }

  return Number.isFinite(minDistancePct) ? minDistancePct : null;
}

function levelsBelow(price: number, levels: number[]): number[] {
  return levels.filter((level) => level < price);
}

function levelsAbove(price: number, levels: number[]): number[] {
  return levels.filter((level) => level > price);
}

function isBreakoutAboveResistance(
  currentPrice: number,
  previousPrice: number,
  resistanceLevels: number[],
): boolean {
  const resistanceBelow = levelsBelow(currentPrice, resistanceLevels);

  if (resistanceBelow.length === 0) {
    return false;
  }

  const crossedLevel = Math.max(...resistanceBelow);

  return previousPrice <= crossedLevel && currentPrice > crossedLevel;
}

function isBreakdownBelowSupport(
  currentPrice: number,
  previousPrice: number,
  supportLevels: number[],
): boolean {
  const supportAbove = levelsAbove(currentPrice, supportLevels);

  if (supportAbove.length === 0) {
    return false;
  }

  const crossedLevel = Math.min(...supportAbove);

  return previousPrice >= crossedLevel && currentPrice < crossedLevel;
}

export function computeStructureScore(prices: number[]): StructureAnalysis {
  const recent = sliceRecentPrices(prices);

  if (recent.length < MIN_CANDLES) {
    return {
      structureScore: NEUTRAL_SCORE,
      supportLevels: [],
      resistanceLevels: [],
      nearestSupportDistancePct: null,
      nearestResistanceDistancePct: null,
      breakoutAboveResistance: false,
      breakdownBelowSupport: false,
    };
  }

  const currentPrice = recent[recent.length - 1];
  const previousPrice = recent[recent.length - 2] ?? currentPrice;
  const { supportLevels, resistanceLevels } = detectSupportResistance(recent);

  const nearestSupportDistancePct = getProximity(currentPrice, supportLevels);
  const nearestResistanceDistancePct = getProximity(
    currentPrice,
    resistanceLevels,
  );

  const breakoutAboveResistance = isBreakoutAboveResistance(
    currentPrice,
    previousPrice,
    resistanceLevels,
  );
  const breakdownBelowSupport = isBreakdownBelowSupport(
    currentPrice,
    previousPrice,
    supportLevels,
  );

  let score = NEUTRAL_SCORE;

  if (breakoutAboveResistance) {
    score += BREAKOUT_BONUS;
  }

  if (breakdownBelowSupport) {
    score -= BREAKDOWN_PENALTY;
  }

  if (
    nearestSupportDistancePct !== null &&
    nearestSupportDistancePct < PROXIMITY_THRESHOLD_PCT
  ) {
    score += NEAR_SUPPORT_BONUS;
  }

  if (
    nearestResistanceDistancePct !== null &&
    nearestResistanceDistancePct < PROXIMITY_THRESHOLD_PCT
  ) {
    score -= NEAR_RESISTANCE_PENALTY;
  }

  return {
    structureScore: clampScore(score),
    supportLevels,
    resistanceLevels,
    nearestSupportDistancePct,
    nearestResistanceDistancePct,
    breakoutAboveResistance,
    breakdownBelowSupport,
  };
}

export function computeStructureScoreFromPrices(prices: number[]): number {
  return computeStructureScore(prices).structureScore;
}

export async function analyzeMarketStructureSafe(
  stock?: string,
): Promise<StructureAnalysis> {
  try {
    if (!stock) {
      return computeStructureScore([]);
    }

    const data = await fetchStockData(stock);

    return computeStructureScore(data.prices);
  } catch (error) {
    console.error("Market structure analysis failed:", error);
    return computeStructureScore([]);
  }
}

export async function computeStructureScoreSafe(stock?: string): Promise<number> {
  const analysis = await analyzeMarketStructureSafe(stock);
  return analysis.structureScore;
}
