import { formatInr } from "@/lib/funds";

export type ExecutionPlanInput = {
  stock: string;
  price: number;
  breakoutLevel: number;
  supportLevel: number;
  allocationAmount: number;
  structureScore: number;
  /** Success probability — accepts 0–1 or 0–100. */
  probability: number;
};

export type ExecutionPlanOutput = {
  steps: string[];
  riskNote: string;
  confidenceNote: string;
  firstTranchePercent: number;
  secondTranchePercent: number;
};

const CAUTIOUS_STRUCTURE_THRESHOLD = 60;
const STRONG_PROBABILITY_THRESHOLD = 75;

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function normalizeProbability(probability: number): number {
  if (!Number.isFinite(probability)) {
    return 50;
  }

  return probability <= 1 ? clampPercent(probability * 100) : clampPercent(probability);
}

function roundPrice(value: number): number {
  if (!Number.isFinite(value) || value <= 0) {
    return 0;
  }

  return value >= 1000 ? Math.round(value) : Math.round(value * 100) / 100;
}

function formatLevel(value: number): string {
  const rounded = roundPrice(value);
  return rounded > 0 ? formatInr(rounded) : "your stop level";
}

function trancheSplit(
  structureScore: number,
  probabilityPct: number,
): { first: number; second: number } {
  const cautious = structureScore < CAUTIOUS_STRUCTURE_THRESHOLD;
  const strong = probabilityPct > STRONG_PROBABILITY_THRESHOLD;

  if (cautious && strong) {
    return { first: 40, second: 60 };
  }

  if (cautious) {
    return { first: 40, second: 60 };
  }

  if (strong) {
    return { first: 55, second: 45 };
  }

  return { first: 50, second: 50 };
}

function formatEntryStep(allocationAmount: number, percent: number): string {
  if (allocationAmount <= 0) {
    return `Enter ${percent}% position`;
  }

  const amount = Math.round((allocationAmount * percent) / 100);
  return `Enter ${percent}% position (${formatInr(amount)})`;
}

function formatAddStep(allocationAmount: number, percent: number): string {
  if (allocationAmount <= 0) {
    return `Add remaining ${percent}% on continuation`;
  }

  const amount = Math.round((allocationAmount * percent) / 100);
  return `Add remaining ${percent}% (${formatInr(amount)}) on continuation`;
}

function buildRiskNote(structureScore: number, supportLevel: number): string {
  const stop = formatLevel(supportLevel);

  if (structureScore < CAUTIOUS_STRUCTURE_THRESHOLD) {
    return `Structure is still forming — keep size small and exit below ${stop} without hesitation.`;
  }

  return `Protect capital first. If price closes below ${stop}, exit the position.`;
}

function buildConfidenceNote(probabilityPct: number, structureScore: number): string {
  const strong = probabilityPct > STRONG_PROBABILITY_THRESHOLD;
  const cautious = structureScore < CAUTIOUS_STRUCTURE_THRESHOLD;

  if (strong && !cautious) {
    return "Strong conviction — edge is clear, but scale in. Never deploy everything at once.";
  }

  if (strong && cautious) {
    return "Probability is high, but structure needs confirmation — stay patient and sized down.";
  }

  if (cautious) {
    return "Patience matters more than speed here. Wait for price to prove the setup.";
  }

  return "Moderate edge — follow the steps and let price confirm before adding size.";
}

/**
 * Converts a BUY decision into human-readable execution steps.
 * Never suggests full capital deployment in a single entry.
 */
export function generateExecutionPlan(input: ExecutionPlanInput): ExecutionPlanOutput {
  const probabilityPct = normalizeProbability(input.probability);
  const structureScore = clampPercent(input.structureScore);
  const { first, second } = trancheSplit(structureScore, probabilityPct);

  const breakout = formatLevel(input.breakoutLevel);
  const support = formatLevel(input.supportLevel);

  const steps: string[] = [];

  if (structureScore < CAUTIOUS_STRUCTURE_THRESHOLD) {
    steps.push(
      `Wait for a clean breakout above ${breakout} — don't chase early`,
    );
  } else {
    steps.push(`Wait for breakout above ${breakout}`);
  }

  steps.push(formatEntryStep(input.allocationAmount, first));
  steps.push(formatAddStep(input.allocationAmount, second));
  steps.push(`Exit below ${support}`);

  return {
    steps,
    riskNote: buildRiskNote(structureScore, input.supportLevel),
    confidenceNote: buildConfidenceNote(probabilityPct, structureScore),
    firstTranchePercent: first,
    secondTranchePercent: second,
  };
}
