export type AllocationInput = {
  probability: number;
  expectedReturn: number;
  expectedDrawdown: number;
  edgeScore: number;
  structureScore: number;
  portfolioValue: number;
};

export type AllocationResult = {
  allocationPercent: number;
  amount: number;
  reason: string;
};

const MAX_ALLOCATION_PCT = 0.2;
const MIN_ALLOCATION_PCT = 0.02;
const NEUTRAL_STRUCTURE_SCORE = 50;

const NO_TRADE: AllocationResult = {
  allocationPercent: 0,
  amount: 0,
  reason: "Low edge",
};

export function computeBaseAllocation(
  probability: number,
  edgeScore: number,
): number {
  if (
    !Number.isFinite(probability) ||
    !Number.isFinite(edgeScore) ||
    probability <= 0 ||
    edgeScore <= 0
  ) {
    return 0;
  }

  return probability * edgeScore;
}

export function adjustForStructure(
  base: number,
  structureScore: number,
): number {
  const score =
    Number.isFinite(structureScore) && structureScore >= 0
      ? Math.min(100, structureScore)
      : NEUTRAL_STRUCTURE_SCORE;

  return base * (score / 100);
}

function hasValidInput(input: AllocationInput): boolean {
  return (
    Number.isFinite(input.probability) &&
    Number.isFinite(input.expectedReturn) &&
    Number.isFinite(input.expectedDrawdown) &&
    Number.isFinite(input.edgeScore) &&
    Number.isFinite(input.structureScore) &&
    Number.isFinite(input.portfolioValue) &&
    input.portfolioValue > 0 &&
    input.probability > 0 &&
    input.edgeScore > 0
  );
}

export function computeAllocation(input: AllocationInput): AllocationResult {
  if (!hasValidInput(input)) {
    return {
      allocationPercent: 0,
      amount: 0,
      reason: "Missing edge data",
    };
  }

  let base = computeBaseAllocation(input.probability, input.edgeScore);
  base = adjustForStructure(base, input.structureScore);

  let allocationPercent = Math.min(MAX_ALLOCATION_PCT, base);

  if (allocationPercent < MIN_ALLOCATION_PCT) {
    return NO_TRADE;
  }

  const amount = Math.round(input.portfolioValue * allocationPercent);

  if (amount <= 0) {
    return NO_TRADE;
  }

  return {
    allocationPercent,
    amount,
    reason: "Edge-based allocation",
  };
}

/** Never throws — missing data yields no trade. */
export function computeAllocationSafe(
  input: Partial<AllocationInput>,
): AllocationResult {
  try {
    if (
      input.portfolioValue === undefined ||
      !Number.isFinite(input.portfolioValue) ||
      input.portfolioValue <= 0
    ) {
      return {
        allocationPercent: 0,
        amount: 0,
        reason: "Missing portfolio value",
      };
    }

    if (
      input.probability === undefined ||
      input.edgeScore === undefined ||
      input.structureScore === undefined
    ) {
      return {
        allocationPercent: 0,
        amount: 0,
        reason: "Missing edge data",
      };
    }

    return computeAllocation({
      probability: input.probability,
      expectedReturn: input.expectedReturn ?? 0,
      expectedDrawdown: input.expectedDrawdown ?? 0,
      edgeScore: input.edgeScore,
      structureScore: input.structureScore,
      portfolioValue: input.portfolioValue,
    });
  } catch (error) {
    console.error("Capital allocation failed:", error);
    return {
      allocationPercent: 0,
      amount: 0,
      reason: "Allocation unavailable",
    };
  }
}
