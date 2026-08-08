import type { MarketTrend, Signals } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type Weights = {
  trend: number;
  momentum: number;
  volume: number;
};

/** @deprecated Use Weights */
export type ContextualWeights = Weights;

export type MarketRegime = MarketTrend;

export type GetContextualWeightsInput = {
  regime: MarketRegime;
  volatility: number;
  supabase?: Client | null;
  userId?: string | null;
};

export const BASE_WEIGHTS: Weights = {
  trend: 0.4,
  momentum: 0.3,
  volume: 0.3,
};

/** @deprecated Use BASE_WEIGHTS */
export const BASE = BASE_WEIGHTS;

const MIN_HISTORY_SAMPLES = 10;

export function adjustForRegime(regime: MarketRegime, weights: Weights): Weights {
  const w = { ...weights };

  if (regime === "bullish") {
    w.trend += 0.1;
  } else if (regime === "bearish") {
    w.momentum += 0.1;
  } else {
    w.volume += 0.1;
  }

  return w;
}

export function adjustForVolatility(volatility: number, weights: Weights): Weights {
  const w = { ...weights };

  if (volatility > 0.7) {
    w.momentum += 0.1;
  }

  return w;
}

export async function adjustForHistory(
  supabase: Client,
  userId: string,
  weights: Weights,
): Promise<Weights> {
  try {
    const { data } = await supabase
      .from("decision_memory")
      .select("signals, success")
      .eq("user_id", userId)
      .not("success", "is", null);

    if (!data || data.length < MIN_HISTORY_SAMPLES) {
      return weights;
    }

    let trendWins = 0;
    let trendTotal = 0;
    let momentumWins = 0;
    let momentumTotal = 0;
    let volumeWins = 0;
    let volumeTotal = 0;

    for (const row of data) {
      const signals = row.signals as Signals | null;

      if (signals?.trend !== undefined && signals.trend > 60) {
        trendTotal += 1;
        if (row.success) {
          trendWins += 1;
        }
      }

      if (signals?.momentum !== undefined && signals.momentum > 60) {
        momentumTotal += 1;
        if (row.success) {
          momentumWins += 1;
        }
      }

      if (signals?.volume !== undefined && signals.volume > 60) {
        volumeTotal += 1;
        if (row.success) {
          volumeWins += 1;
        }
      }
    }

    const w = { ...weights };

    if (trendTotal > 0) {
      w.trend += (trendWins / trendTotal) * 0.1;
    }

    if (momentumTotal > 0) {
      w.momentum += (momentumWins / momentumTotal) * 0.1;
    }

    if (volumeTotal > 0) {
      w.volume += (volumeWins / volumeTotal) * 0.1;
    }

    return w;
  } catch (err) {
    console.error("adjustForHistory failed:", err);
    return weights;
  }
}

export function normalize(weights: Weights): Weights {
  const total = weights.trend + weights.momentum + weights.volume;

  if (total === 0) {
    return BASE_WEIGHTS;
  }

  return {
    trend: weights.trend / total,
    momentum: weights.momentum / total,
    volume: weights.volume / total,
  };
}

export async function getContextualWeights(
  input: GetContextualWeightsInput,
): Promise<Weights> {
  let weights: Weights = { ...BASE_WEIGHTS };

  weights = adjustForRegime(input.regime, weights);
  weights = adjustForVolatility(input.volatility, weights);

  if (input.supabase && input.userId) {
    weights = await adjustForHistory(input.supabase, input.userId, weights);
  }

  return normalize(weights);
}

export async function getContextualWeightsSafe(
  input: GetContextualWeightsInput,
): Promise<Weights> {
  try {
    return await getContextualWeights(input);
  } catch (err) {
    console.error("getContextualWeightsSafe:", err);
    return BASE_WEIGHTS;
  }
}

export function weightedSignalScore(signals: Signals, weights: Weights): number {
  return (
    signals.trend * weights.trend +
    signals.momentum * weights.momentum +
    signals.volume * weights.volume
  );
}

export function weightedProbability(signals: Signals, weights: Weights): number {
  return weightedSignalScore(signals, weights) / 100;
}
