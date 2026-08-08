import type { OutcomeEvaluationOutput } from "@/services/learning/outcomeEngine";
import { INITIAL_TRUST_SCORE } from "@/services/learning/trustEngine";

const TRUST_SCORE_KEY = "apex_trust_score";
const TRUST_DELTA_KEY = "apex_trust_delta";
const LAST_OUTCOME_KEY = "apex_last_outcome";

function readNumber(key: string, fallback: number): number {
  if (typeof window === "undefined") {
    return fallback;
  }

  const raw = window.localStorage.getItem(key);

  if (!raw) {
    return fallback;
  }

  const value = Number(raw);
  return Number.isFinite(value) ? value : fallback;
}

export function readTrustScore(): number {
  const score = readNumber(TRUST_SCORE_KEY, INITIAL_TRUST_SCORE);
  return Math.max(0, Math.min(100, Math.round(score)));
}

export function readTrustDelta(): number {
  return readNumber(TRUST_DELTA_KEY, 0);
}

export function readLastOutcome(): OutcomeEvaluationOutput | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(LAST_OUTCOME_KEY);

  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as OutcomeEvaluationOutput;
  } catch {
    return null;
  }
}

export function persistTrustUpdate(newScore: number, delta: number): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(TRUST_SCORE_KEY, String(newScore));
  window.localStorage.setItem(TRUST_DELTA_KEY, String(delta));
}

export function persistLastOutcome(outcome: OutcomeEvaluationOutput): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(LAST_OUTCOME_KEY, JSON.stringify(outcome));
}
