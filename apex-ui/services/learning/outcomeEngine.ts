export type OutcomeEvaluationInput = {
  decisionId: string;
  stock: string;
  plannedEntry: number;
  actualEntry: number | null;
  plannedExit: number;
  actualExit: number | null;
  followedPlan: boolean;
  profitLoss: number;
  holdingTime: number;
};

export type OutcomeResult = "win" | "loss" | "breakeven";

export type OutcomeEvaluationOutput = {
  outcome: OutcomeResult;
  disciplineScore: number;
  executionQuality: number;
  trustDelta: number;
  summary: string;
};

const DISCIPLINE_BASE = 50;
const EXECUTION_BASE = 50;
const FOLLOWED_PLAN_BONUS = 30;
const EXACT_LEVEL_BONUS = 10;
const ENTRY_DEVIATION_BONUS = 20;
const EXIT_RESPECTED_BONUS = 20;
const ENTRY_DEVIATION_THRESHOLD_PCT = 1;
const HIGH_SCORE_THRESHOLD = 80;
const LOW_SCORE_THRESHOLD = 50;
const TRUST_BONUS = 5;
const TRUST_PENALTY = -5;

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function clampTrustDelta(value: number): number {
  return Math.max(-10, Math.min(10, Math.round(value)));
}

function roundPrice(value: number): number {
  if (!Number.isFinite(value)) {
    return value;
  }

  return value >= 1000 ? Math.round(value) : Math.round(value * 100) / 100;
}

function pricesMatch(
  planned: number,
  actual: number | null,
): actual is number {
  if (actual === null || !Number.isFinite(planned) || !Number.isFinite(actual)) {
    return false;
  }

  return roundPrice(planned) === roundPrice(actual);
}

function resolveOutcome(profitLoss: number): OutcomeResult {
  if (profitLoss > 0) {
    return "win";
  }

  if (profitLoss < 0) {
    return "loss";
  }

  return "breakeven";
}

function entryDeviationPct(
  plannedEntry: number,
  actualEntry: number | null,
): number | null {
  if (
    actualEntry === null ||
    !Number.isFinite(plannedEntry) ||
    !Number.isFinite(actualEntry) ||
    plannedEntry <= 0
  ) {
    return null;
  }

  return (Math.abs(actualEntry - plannedEntry) / plannedEntry) * 100;
}

function computeDisciplineScore(input: OutcomeEvaluationInput): number {
  let score = DISCIPLINE_BASE;

  if (input.followedPlan) {
    score += FOLLOWED_PLAN_BONUS;
  }

  if (pricesMatch(input.plannedEntry, input.actualEntry)) {
    score += EXACT_LEVEL_BONUS;
  }

  if (pricesMatch(input.plannedExit, input.actualExit)) {
    score += EXACT_LEVEL_BONUS;
  }

  return clampScore(score);
}

function computeExecutionQuality(input: OutcomeEvaluationInput): number {
  let score = EXECUTION_BASE;

  const deviation = entryDeviationPct(input.plannedEntry, input.actualEntry);

  if (deviation !== null && deviation < ENTRY_DEVIATION_THRESHOLD_PCT) {
    score += ENTRY_DEVIATION_BONUS;
  }

  if (pricesMatch(input.plannedExit, input.actualExit)) {
    score += EXIT_RESPECTED_BONUS;
  }

  return clampScore(score);
}

function computeTrustDelta(
  disciplineScore: number,
  executionQuality: number,
): number {
  let delta = 0;

  if (disciplineScore > HIGH_SCORE_THRESHOLD) {
    delta += TRUST_BONUS;
  } else if (disciplineScore < LOW_SCORE_THRESHOLD) {
    delta += TRUST_PENALTY;
  }

  if (executionQuality > HIGH_SCORE_THRESHOLD) {
    delta += TRUST_BONUS;
  } else if (executionQuality < LOW_SCORE_THRESHOLD) {
    delta += TRUST_PENALTY;
  }

  return clampTrustDelta(delta);
}

function buildSummary(
  input: OutcomeEvaluationInput,
  disciplineScore: number,
  executionQuality: number,
): string {
  if (!input.followedPlan) {
    return "You deviated from the plan. This reduces consistency.";
  }

  if (
    disciplineScore > HIGH_SCORE_THRESHOLD &&
    executionQuality > HIGH_SCORE_THRESHOLD
  ) {
    return "Strong execution. Keep repeating this behavior.";
  }

  if (
    disciplineScore >= 70 &&
    executionQuality >= 70 &&
    input.followedPlan
  ) {
    return "Good discipline. Execution matched the plan.";
  }

  if (disciplineScore < LOW_SCORE_THRESHOLD) {
    return "Follow the plan more closely next time — consistency builds trust.";
  }

  if (executionQuality < LOW_SCORE_THRESHOLD) {
    return "Your timing drifted from the plan. Tighter execution will help.";
  }

  return "Solid effort. Small improvements will compound over time.";
}

function assertValidInput(input: OutcomeEvaluationInput): void {
  if (
    !input.decisionId ||
    !input.stock ||
    !Number.isFinite(input.plannedEntry) ||
    input.plannedEntry <= 0 ||
    !Number.isFinite(input.plannedExit) ||
    input.plannedExit <= 0 ||
    !Number.isFinite(input.profitLoss) ||
    !Number.isFinite(input.holdingTime) ||
    input.holdingTime < 0
  ) {
    throw new Error("Invalid outcome evaluation input");
  }

  if (
    input.actualEntry !== null &&
    (!Number.isFinite(input.actualEntry) || input.actualEntry <= 0)
  ) {
    throw new Error("Invalid actual entry");
  }

  if (
    input.actualExit !== null &&
    (!Number.isFinite(input.actualExit) || input.actualExit <= 0)
  ) {
    throw new Error("Invalid actual exit");
  }
}

/**
 * Evaluates whether a decision was followed and how it affects trust.
 */
export function evaluateOutcome(
  input: OutcomeEvaluationInput,
): OutcomeEvaluationOutput {
  assertValidInput(input);

  const outcome = resolveOutcome(input.profitLoss);
  const disciplineScore = computeDisciplineScore(input);
  const executionQuality = computeExecutionQuality(input);
  const trustDelta = computeTrustDelta(disciplineScore, executionQuality);
  const summary = buildSummary(input, disciplineScore, executionQuality);

  return {
    outcome,
    disciplineScore,
    executionQuality,
    trustDelta,
    summary,
  };
}

export function evaluateOutcomeSafe(
  input: OutcomeEvaluationInput,
): OutcomeEvaluationOutput {
  try {
    return evaluateOutcome(input);
  } catch {
    return {
      outcome: "breakeven",
      disciplineScore: 50,
      executionQuality: 50,
      trustDelta: 0,
      summary: "Unable to evaluate outcome",
    };
  }
}
