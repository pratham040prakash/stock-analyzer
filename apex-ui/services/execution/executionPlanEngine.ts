import { formatInr } from "@/lib/funds";

export type ExecutionPlanInput = {
  stock: string;
  currentPrice: number;
  breakoutLevel: number;
  supportLevel: number;
  allocationAmount: number;
  structureScore: number;
  /** Success probability — accepts 0–1 or 0–100. */
  probability: number;
};

export type ExecutionPlanEntryType = "aggressive" | "confirmed";

export type ExecutionPlanOutput = {
  steps: string[];
  stopLoss: number;
  entryType: ExecutionPlanEntryType;
  riskNote: string;
  confidenceNote: string;
};

export type ExecutionPlanSafeOutput = {
  steps: string[];
  stopLoss: number | null;
  entryType: ExecutionPlanEntryType;
  riskNote: string;
  confidenceNote: string;
};

const WEAK_STRUCTURE_THRESHOLD = 60;
const AGGRESSIVE_STRUCTURE_THRESHOLD = 70;
const HIGH_PROBABILITY_THRESHOLD = 75;
const MODERATE_PROBABILITY_THRESHOLD = 60;
const FIRST_ENTRY_PERCENT = 50;
const SECOND_ENTRY_PERCENT = 50;

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function normalizeProbability(probability: number): number {
  if (!Number.isFinite(probability)) {
    return 0;
  }

  return probability <= 1
    ? clampPercent(probability * 100)
    : clampPercent(probability);
}

function roundPrice(value: number): number {
  if (!Number.isFinite(value) || value <= 0) {
    return 0;
  }

  return value >= 1000 ? Math.round(value) : Math.round(value * 100) / 100;
}

function formatPrice(value: number): string {
  const rounded = roundPrice(value);
  return rounded > 0 ? formatInr(rounded) : "—";
}

function halfAllocation(allocationAmount: number): string {
  if (!Number.isFinite(allocationAmount) || allocationAmount <= 0) {
    return "your planned half";
  }

  return formatInr(Math.round(allocationAmount / 2));
}

function resolveEntryType(
  structureScore: number,
  probabilityPct: number,
): ExecutionPlanEntryType {
  if (
    structureScore >= AGGRESSIVE_STRUCTURE_THRESHOLD &&
    probabilityPct >= HIGH_PROBABILITY_THRESHOLD
  ) {
    return "aggressive";
  }

  return "confirmed";
}

function buildConfirmedSteps(input: ExecutionPlanInput): string[] {
  return [
    `Wait for breakout above ${formatPrice(input.breakoutLevel)}`,
    `Enter ${FIRST_ENTRY_PERCENT}% (${halfAllocation(input.allocationAmount)}) after breakout`,
    `Add remaining ${SECOND_ENTRY_PERCENT}% on continuation`,
    `Exit if price falls below ${formatPrice(input.supportLevel)}`,
  ];
}

function buildAggressiveSteps(input: ExecutionPlanInput): string[] {
  return [
    `Enter ${FIRST_ENTRY_PERCENT}% near current price ${formatPrice(input.currentPrice)}`,
    `Add remaining ${SECOND_ENTRY_PERCENT}% on breakout above ${formatPrice(input.breakoutLevel)}`,
    `Exit if price falls below ${formatPrice(input.supportLevel)}`,
  ];
}

function buildRiskNote(structureScore: number): string {
  if (structureScore < WEAK_STRUCTURE_THRESHOLD) {
    return "Structure is weak — reduce position size";
  }

  return "Risk is controlled with defined exit";
}

function buildConfidenceNote(probabilityPct: number): string {
  if (probabilityPct > HIGH_PROBABILITY_THRESHOLD) {
    return "High probability setup with momentum";
  }

  if (probabilityPct > MODERATE_PROBABILITY_THRESHOLD) {
    return "Moderate probability — wait for confirmation";
  }

  return "Low conviction — trade cautiously";
}

function assertValidInput(input: ExecutionPlanInput): void {
  if (
    !input.stock ||
    !Number.isFinite(input.currentPrice) ||
    input.currentPrice <= 0 ||
    !Number.isFinite(input.breakoutLevel) ||
    !Number.isFinite(input.supportLevel) ||
    !Number.isFinite(input.allocationAmount) ||
    !Number.isFinite(input.structureScore) ||
    !Number.isFinite(input.probability)
  ) {
    throw new Error("Invalid execution plan input");
  }
}

/**
 * Converts a BUY decision into a staged, human-readable execution plan.
 * Never suggests full capital deployment in a single entry.
 */
export function generateExecutionPlan(
  input: ExecutionPlanInput,
): ExecutionPlanOutput {
  assertValidInput(input);

  const structureScore = clampPercent(input.structureScore);
  const probabilityPct = normalizeProbability(input.probability);
  const entryType = resolveEntryType(structureScore, probabilityPct);
  const stopLoss = roundPrice(input.supportLevel);

  const steps =
    entryType === "aggressive"
      ? buildAggressiveSteps(input)
      : buildConfirmedSteps(input);

  return {
    steps,
    stopLoss,
    entryType,
    riskNote: buildRiskNote(structureScore),
    confidenceNote: buildConfidenceNote(probabilityPct),
  };
}

export function generateExecutionPlanSafe(
  input: ExecutionPlanInput,
): ExecutionPlanSafeOutput {
  try {
    return generateExecutionPlan(input);
  } catch {
    return {
      steps: [],
      stopLoss: null,
      entryType: "confirmed",
      riskNote: "Execution unavailable",
      confidenceNote: "",
    };
  }
}
