import { getContextualWeightsSafe } from "@/services/decision/contextualWeights";
import type { MarketTrend, Signals } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type ConfidenceResult = {
  /** Normalized success probability (0–1). */
  probability: number;
  /** Expected upside as a decimal fraction (e.g. 0.04 = 4%). */
  expectedReturn: number;
  /** Expected downside as a decimal fraction. */
  expectedDrawdown: number;
  /** Return / risk ratio (expectedReturn / expectedDrawdown). */
  edgeScore: number;
};

export type ComputeConfidenceInput = {
  signals: Signals;
  regime: MarketTrend;
  volatility?: number;
  structureScore?: number;
  supabase?: Client | null;
  userId?: string | null;
};

type BaseProbabilityContext = {
  signals: Signals;
  regime: MarketTrend;
  volatility: number;
  supabase?: Client | null;
  userId?: string | null;
};

function applyStructureAdjustment(prob: number, structureScore?: number): number {
  const score = structureScore ?? NEUTRAL_STRUCTURE_SCORE;
  const normalized =
    Number.isFinite(score) && score >= 0
      ? Math.min(100, score)
      : NEUTRAL_STRUCTURE_SCORE;

  return prob * (normalized / 100);
}

const NEUTRAL_STRUCTURE_SCORE = 50;
const MIN_HISTORY_SAMPLES = 5;
const MIN_PROBABILITY = 0.05;
const MAX_PROBABILITY = 0.95;
const UPSIDE_ASSUMPTION = 0.08;
const DRAWDOWN_SCALE = 0.05;

function resolveVolatility(volatility?: number): number {
  if (volatility !== undefined && Number.isFinite(volatility)) {
    return Math.min(1, Math.max(0, volatility));
  }

  return 0;
}

async function baseProbabilityWithContext(
  input: BaseProbabilityContext,
): Promise<number> {
  const weights = await getContextualWeightsSafe({
    regime: input.regime,
    volatility: input.volatility,
    supabase: input.supabase ?? null,
    userId: input.userId ?? null,
  });

  return (
    (input.signals.trend * weights.trend +
      input.signals.momentum * weights.momentum +
      input.signals.volume * weights.volume) /
    100
  );
}

/** @deprecated Use baseProbabilityWithContext via computeConfidence. */
export function baseProbability(signals: Signals): number {
  return (
    (signals.trend * 0.4 + signals.momentum * 0.3 + signals.volume * 0.3) / 100
  );
}

export function adjustForRegime(prob: number, regime: MarketTrend): number {
  if (regime === "bullish") {
    return prob * 1.1;
  }

  if (regime === "bearish") {
    return prob * 0.8;
  }

  return prob;
}

export async function adjustForHistory(
  supabase: Client | null | undefined,
  userId: string | null | undefined,
  prob: number,
): Promise<number> {
  if (!supabase) {
    return prob;
  }

  try {
    let query = supabase
      .from("decision_memory")
      .select("success")
      .not("success", "is", null);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error || !data || data.length < MIN_HISTORY_SAMPLES) {
      return prob;
    }

    const winRate =
      data.filter((row) => row.success === true).length / data.length;

    return prob * (0.5 + winRate);
  } catch (error) {
    console.error("Historical confidence adjustment failed:", error);
    return prob;
  }
}

export function estimateReturn(prob: number): number {
  return prob * UPSIDE_ASSUMPTION;
}

export function estimateDrawdown(prob: number): number {
  return (1 - prob) * DRAWDOWN_SCALE;
}

function clampProbability(prob: number): number {
  return Math.min(MAX_PROBABILITY, Math.max(MIN_PROBABILITY, prob));
}

function buildConfidenceResult(prob: number): ConfidenceResult {
  const expectedReturn = estimateReturn(prob);
  const expectedDrawdown = Math.max(estimateDrawdown(prob), 0.0001);

  return {
    probability: prob,
    expectedReturn,
    expectedDrawdown,
    edgeScore: expectedReturn / expectedDrawdown,
  };
}

export async function computeConfidenceFromSignals(
  signals: Signals,
  regime: MarketTrend,
  volatility = 0,
  structureScore = NEUTRAL_STRUCTURE_SCORE,
): Promise<ConfidenceResult> {
  let prob = await baseProbabilityWithContext({
    signals,
    regime,
    volatility,
  });
  prob = adjustForRegime(prob, regime);
  prob = applyStructureAdjustment(prob, structureScore);
  prob = clampProbability(prob);

  return buildConfidenceResult(prob);
}

export async function computeConfidence(
  input: ComputeConfidenceInput,
): Promise<ConfidenceResult> {
  const volatility = resolveVolatility(input.volatility);

  let prob = await baseProbabilityWithContext({
    signals: input.signals,
    regime: input.regime,
    volatility,
    supabase: input.supabase ?? null,
    userId: input.userId ?? null,
  });

  prob = adjustForRegime(prob, input.regime);
  prob = await adjustForHistory(input.supabase, input.userId, prob);
  prob = applyStructureAdjustment(prob, input.structureScore);
  prob = clampProbability(prob);

  return buildConfidenceResult(prob);
}

/** Deterministic fallback — never throws. */
export async function computeConfidenceSafe(
  input: ComputeConfidenceInput,
): Promise<ConfidenceResult> {
  try {
    return await computeConfidence(input);
  } catch (error) {
    console.error("Confidence computation failed:", error);

    try {
      return await computeConfidenceFromSignals(
        input.signals,
        input.regime,
        resolveVolatility(input.volatility),
        input.structureScore ?? NEUTRAL_STRUCTURE_SCORE,
      );
    } catch (fallbackError) {
      console.error("Confidence fallback failed:", fallbackError);

      let prob = adjustForRegime(baseProbability(input.signals), input.regime);
      prob = applyStructureAdjustment(
        prob,
        input.structureScore ?? NEUTRAL_STRUCTURE_SCORE,
      );
      prob = clampProbability(prob);

      return buildConfidenceResult(prob);
    }
  }
}
