import { computeStructureScore } from "@/services/market/structureEngine";
import { fetchStockData } from "@/services/market/stockData";
import {
  buildEntryInputFromMarketData,
  type EntryInput,
} from "@/services/execution/entryTiming";
import { resolveExecutionPlanMarketRegime } from "@/services/execution/executionPlanEngine";
import type {
  ExecutionPlanInput,
  ExecutionPlanMarketRegime,
} from "@/services/execution/executionPlanEngine";

export type ExecutionPlanDecisionSource = {
  action?: string;
  stock?: string;
  amount?: number;
  structureScore?: number;
  confidence?: number;
  confidenceMetrics?: {
    probability?: number;
  };
};

export type BuildExecutionPlanInputOptions = {
  entryTiming?: { enter: boolean };
  marketRegime?: ExecutionPlanMarketRegime;
};

function levelsAbove(price: number, levels: number[]): number[] {
  return levels.filter((level) => level > price * 1.001);
}

function levelsBelow(price: number, levels: number[]): number[] {
  return levels.filter((level) => level < price * 0.999);
}

function pickBreakoutLevel(
  price: number,
  resistanceLevels: number[],
  entryInput: EntryInput | null,
): number {
  const above = levelsAbove(price, resistanceLevels);

  if (above.length > 0) {
    return Math.min(...above);
  }

  if (entryInput?.recentHigh && entryInput.recentHigh > price) {
    return entryInput.recentHigh;
  }

  return price * 1.02;
}

function pickSupportLevel(
  price: number,
  supportLevels: number[],
  entryInput: EntryInput | null,
): number {
  const below = levelsBelow(price, supportLevels);

  if (below.length > 0) {
    return Math.max(...below);
  }

  if (entryInput?.recentLow && entryInput.recentLow < price) {
    return entryInput.recentLow;
  }

  return price * 0.95;
}

function resolveProbability(decision: ExecutionPlanDecisionSource): number {
  if (decision.confidenceMetrics?.probability !== undefined) {
    return decision.confidenceMetrics.probability;
  }

  if (decision.confidence !== undefined) {
    return decision.confidence <= 1
      ? decision.confidence
      : decision.confidence / 100;
  }

  return 0.5;
}

/** Builds engine input from a BUY decision and live market structure. */
export async function buildExecutionPlanInput(
  decision: ExecutionPlanDecisionSource,
  options: BuildExecutionPlanInputOptions = {},
): Promise<ExecutionPlanInput | null> {
  if (!decision.stock) {
    return null;
  }

  try {
    const data = await fetchStockData(decision.stock);
    const structure = computeStructureScore(data.prices);
    const entryInput = buildEntryInputFromMarketData(data.prices, data.volumes);

    const price =
      entryInput?.price ??
      data.prices[data.prices.length - 1] ??
      0;

    if (!Number.isFinite(price) || price <= 0) {
      return null;
    }

    const marketRegime =
      options.marketRegime ??
      resolveExecutionPlanMarketRegime(decision, options.entryTiming);

    return {
      stock: decision.stock,
      currentPrice: price,
      breakoutLevel: pickBreakoutLevel(
        price,
        structure.resistanceLevels,
        entryInput,
      ),
      supportLevel: pickSupportLevel(
        price,
        structure.supportLevels,
        entryInput,
      ),
      allocationAmount: Math.max(0, decision.amount ?? 0),
      structureScore: decision.structureScore ?? structure.structureScore,
      probability: resolveProbability(decision),
      marketRegime,
    };
  } catch (error) {
    console.error("Execution plan input build failed:", error);
    return null;
  }
}
