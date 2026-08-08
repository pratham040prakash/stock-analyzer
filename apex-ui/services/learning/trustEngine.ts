import type { OutcomeResult } from "@/services/learning/outcomeEngine";

/** Default trust score for new users. */
export const INITIAL_TRUST_SCORE = 50;

export type TrustOutcomeInput = {
  disciplineScore: number;
  executionQuality: number;
  outcome: OutcomeResult;
};

export type TrustLevel = "low" | "building" | "high";

export type TrustUpdateOutput = {
  newTrustScore: number;
  delta: number;
  level: TrustLevel;
  message: string;
};

const HIGH_SCORE_THRESHOLD = 80;
const LOW_SCORE_THRESHOLD = 50;
const DISCIPLINE_TRUST_BONUS = 5;
const DISCIPLINE_TRUST_PENALTY = -5;
const EXECUTION_TRUST_BONUS = 5;
const EXECUTION_TRUST_PENALTY = -5;
const DISCIPLINED_LOSS_BONUS = 2;
const LUCKY_WIN_PENALTY = -2;
const LOW_LEVEL_MAX = 40;
const HIGH_LEVEL_MIN = 70;

function clampTrustScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function resolveLevel(score: number): TrustLevel {
  if (score >= HIGH_LEVEL_MIN) {
    return "high";
  }

  if (score >= LOW_LEVEL_MAX) {
    return "building";
  }

  return "low";
}

function buildMessage(level: TrustLevel): string {
  if (level === "high") {
    return "You are trusting the system and it is working.";
  }

  if (level === "building") {
    return "Consistency will improve your results.";
  }

  return "You are not following the system consistently.";
}

function computeDelta(input: TrustOutcomeInput): number {
  let delta = 0;

  if (input.disciplineScore > HIGH_SCORE_THRESHOLD) {
    delta += DISCIPLINE_TRUST_BONUS;
  } else if (input.disciplineScore < LOW_SCORE_THRESHOLD) {
    delta += DISCIPLINE_TRUST_PENALTY;
  }

  if (input.executionQuality > HIGH_SCORE_THRESHOLD) {
    delta += EXECUTION_TRUST_BONUS;
  } else if (input.executionQuality < LOW_SCORE_THRESHOLD) {
    delta += EXECUTION_TRUST_PENALTY;
  }

  if (input.outcome === "loss" && input.disciplineScore > HIGH_SCORE_THRESHOLD) {
    delta += DISCIPLINED_LOSS_BONUS;
  }

  if (input.outcome === "win" && input.disciplineScore < LOW_SCORE_THRESHOLD) {
    delta += LUCKY_WIN_PENALTY;
  }

  return delta;
}

function assertValidInput(
  currentScore: number,
  outcome: TrustOutcomeInput,
): void {
  if (
    !Number.isFinite(currentScore) ||
    currentScore < 0 ||
    currentScore > 100 ||
    !Number.isFinite(outcome.disciplineScore) ||
    !Number.isFinite(outcome.executionQuality) ||
    outcome.disciplineScore < 0 ||
    outcome.disciplineScore > 100 ||
    outcome.executionQuality < 0 ||
    outcome.executionQuality > 100 ||
    (outcome.outcome !== "win" &&
      outcome.outcome !== "loss" &&
      outcome.outcome !== "breakeven")
  ) {
    throw new Error("Invalid trust update input");
  }
}

/**
 * Updates trust based on discipline and execution — not raw win/loss alone.
 */
export function updateTrustScore(
  currentScore: number,
  outcome: TrustOutcomeInput,
): TrustUpdateOutput {
  assertValidInput(currentScore, outcome);

  const delta = computeDelta(outcome);
  const newTrustScore = clampTrustScore(currentScore + delta);
  const level = resolveLevel(newTrustScore);

  return {
    newTrustScore,
    delta,
    level,
    message: buildMessage(level),
  };
}

export function updateTrustScoreSafe(
  currentScore: number,
  outcome: TrustOutcomeInput,
): TrustUpdateOutput {
  try {
    return updateTrustScore(currentScore, outcome);
  } catch {
    const safeScore = Number.isFinite(currentScore)
      ? clampTrustScore(currentScore)
      : INITIAL_TRUST_SCORE;

    return {
      newTrustScore: safeScore,
      delta: 0,
      level: "building",
      message: "Trust unchanged",
    };
  }
}
