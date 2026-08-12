import { computeStructureScore } from "@/services/market/structureEngine";
import type { JourneyHorizon } from "@/types/investmentJourney";

export type ChartBackedJourneyPlan = {
  symbol: string;
  horizon: JourneyHorizon;
  swingWeeks?: number;
  entryPriceInr: number;
  targetPriceInr: number;
  supportLevelInr: number | null;
  resistanceLevelInr: number | null;
  lookbackDays: number;
  structureScore: number;
  backtraceSummary: string;
  pathRationale: string;
  activationLevelInr?: number;
};

export type BuildChartBackedJourneyPlanInput = {
  symbol: string;
  prices: number[];
  currentPriceInr?: number | null;
  activationLevelInr?: number;
  preferSwing?: boolean;
};

function roundInr(value: number): number {
  return Math.round(value);
}

function nearestSupportBelow(price: number, levels: number[]): number | null {
  const below = levels.filter((level) => level < price);
  if (below.length === 0) {
    return null;
  }

  return Math.max(...below);
}

function nearestResistanceAbove(price: number, levels: number[]): number | null {
  const above = levels.filter((level) => level > price);
  if (above.length === 0) {
    return null;
  }

  return Math.min(...above);
}

function recentHigh(prices: number[]): number | null {
  if (prices.length === 0) {
    return null;
  }

  return Math.max(...prices);
}

function formatLevel(value: number): string {
  return `₹${roundInr(value).toLocaleString("en-IN")}`;
}

export function buildChartBackedJourneyPlan(
  input: BuildChartBackedJourneyPlanInput,
): ChartBackedJourneyPlan | null {
  const prices = input.prices.filter(
    (price) => typeof price === "number" && Number.isFinite(price) && price > 0,
  );

  if (prices.length < 10) {
    return null;
  }

  const current =
    input.currentPriceInr && input.currentPriceInr > 0
      ? input.currentPriceInr
      : prices[prices.length - 1];

  const structure = computeStructureScore(prices);
  const support = nearestSupportBelow(current, structure.supportLevels);
  const resistance = nearestResistanceAbove(current, structure.resistanceLevels);
  const high = recentHigh(prices);

  let target =
    resistance ??
    (input.activationLevelInr && input.activationLevelInr > current
      ? input.activationLevelInr
      : null) ??
    high;

  if (!target || target <= current) {
    target = roundInr(current * 1.08);
  } else {
    target = roundInr(target);
  }

  const entry = roundInr(support ?? current);

  if (target <= entry) {
    target = roundInr(entry * 1.06);
  }

  const horizon: JourneyHorizon = input.preferSwing ? "swing" : "long_term";
  const swingWeeks = horizon === "swing" ? 4 : undefined;

  const lookbackDays = prices.length;
  const monthsLabel = lookbackDays >= 60 ? "3 months" : `${lookbackDays} sessions`;

  const facts: string[] = [
    `FACT · Read ${lookbackDays} daily closes (${monthsLabel}).`,
  ];

  if (support !== null) {
    facts.push(`Support near ${formatLevel(support)} from recent lows.`);
  }

  if (resistance !== null) {
    facts.push(`Resistance near ${formatLevel(resistance)} from recent highs.`);
  } else if (high !== null && high > current) {
    facts.push(`Recent range high ${formatLevel(high)}.`);
  }

  if (input.activationLevelInr && input.activationLevelInr > current) {
    facts.push(`Activation level ${formatLevel(input.activationLevelInr)}.`);
  }

  const pathRationale =
    horizon === "swing"
      ? "Swing path: entry zone to nearest resistance from the backtrace — not a forecast."
      : "Long-term path: accumulate near support, target prior resistance — thesis-led, not guaranteed.";

  return {
    symbol: input.symbol.trim().toUpperCase(),
    horizon,
    swingWeeks,
    entryPriceInr: entry,
    targetPriceInr: target,
    supportLevelInr: support !== null ? roundInr(support) : null,
    resistanceLevelInr: resistance !== null ? roundInr(resistance) : null,
    lookbackDays,
    structureScore: structure.structureScore,
    backtraceSummary: facts.join(" "),
    pathRationale,
    activationLevelInr: input.activationLevelInr,
  };
}

export function runBuildChartBackedJourneyPlanSelfCheck(): void {
  const prices = [
    100, 102, 101, 99, 98, 97, 96, 98, 100, 102, 104, 103, 105, 107, 106,
    108, 110, 109, 111, 113,
  ];

  const plan = buildChartBackedJourneyPlan({
    symbol: "TEST",
    prices,
    currentPriceInr: 113,
    preferSwing: true,
  });

  if (!plan || plan.targetPriceInr <= plan.entryPriceInr) {
    throw new Error("Chart-backed journey plan self-check failed: target/entry");
  }

  if (!plan.backtraceSummary.includes("FACT")) {
    throw new Error("Chart-backed journey plan self-check failed: backtrace");
  }
}
