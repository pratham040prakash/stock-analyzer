import { getDynamicWeights, type SignalWeights } from "@/services/market/regime";
import type { Signals } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

const MIN_COMPLETED_TRADES = 5;
const SIGNAL_THRESHOLD = 60;
const CACHE_MS = 5 * 60 * 1000;

type CompletedDecision = {
  signals: Signals | null;
  pnl: number;
  success: boolean | null;
};

export type LearningPerformance = {
  totalTrades: number;
  winRate: number;
  avgPnl: number;
};

export type SignalEffectiveness = {
  trend: number;
  momentum: number;
  volume: number;
};

export type LearningSnapshot = {
  performance: LearningPerformance;
  signalEffectiveness: SignalEffectiveness;
  weights: SignalWeights;
  source: "adaptive" | "default";
};

const weightCache = new Map<
  string,
  { weights: SignalWeights | null; at: number }
>();

export async function fetchCompletedDecisions(
  supabase: Client,
  userId: string,
): Promise<CompletedDecision[]> {
  const { data, error } = await supabase
    .from("decision_memory")
    .select("signals, pnl, success")
    .eq("user_id", userId)
    .not("exit_price", "is", null);

  if (error || !data) {
    return [];
  }

  return data.map((row) => ({
    signals: (row.signals as Signals | null) ?? null,
    pnl: Number(row.pnl ?? 0),
    success: row.success,
  }));
}

export function computePerformance(
  records: CompletedDecision[],
): LearningPerformance {
  if (records.length === 0) {
    return { totalTrades: 0, winRate: 0, avgPnl: 0 };
  }

  const wins = records.filter(
    (record) => record.success === true || record.pnl > 0,
  ).length;

  const avgPnl =
    records.reduce((sum, record) => sum + record.pnl, 0) / records.length;

  return {
    totalTrades: records.length,
    winRate: wins / records.length,
    avgPnl,
  };
}

type NumericSignalKey = "trend" | "momentum" | "volume";

function signalSuccessRate(
  records: CompletedDecision[],
  signalKey: NumericSignalKey,
): number {
  const strong = records.filter((record) => {
    const value = record.signals?.[signalKey];
    return typeof value === "number" && value > SIGNAL_THRESHOLD;
  });

  if (strong.length === 0) {
    return 0.5;
  }

  const wins = strong.filter(
    (record) => record.success === true || record.pnl > 0,
  ).length;

  return wins / strong.length;
}

export function analyzeSignalEffectiveness(
  records: CompletedDecision[],
): SignalEffectiveness {
  return {
    trend: signalSuccessRate(records, "trend"),
    momentum: signalSuccessRate(records, "momentum"),
    volume: signalSuccessRate(records, "volume"),
  };
}

export function generateAdaptiveWeights(
  effectiveness: SignalEffectiveness,
): SignalWeights {
  const total =
    effectiveness.trend + effectiveness.momentum + effectiveness.volume;

  if (total <= 0) {
    return getDynamicWeights("sideways");
  }

  return {
    trend: effectiveness.trend / total,
    momentum: effectiveness.momentum / total,
    volume: effectiveness.volume / total,
  };
}

export async function getAdaptiveWeights(
  supabase: Client,
  userId: string,
): Promise<SignalWeights | null> {
  const cached = weightCache.get(userId);
  if (cached && Date.now() - cached.at < CACHE_MS) {
    return cached.weights;
  }

  const records = await fetchCompletedDecisions(supabase, userId);

  if (records.length < MIN_COMPLETED_TRADES) {
    weightCache.set(userId, { weights: null, at: Date.now() });
    return null;
  }

  const effectiveness = analyzeSignalEffectiveness(records);
  const weights = generateAdaptiveWeights(effectiveness);

  weightCache.set(userId, { weights, at: Date.now() });
  return weights;
}

/** Non-blocking — returns null when learning data is insufficient or fetch fails. */
export async function getAdaptiveWeightsSafe(
  supabase: Client,
  userId: string,
): Promise<SignalWeights | null> {
  try {
    return await getAdaptiveWeights(supabase, userId);
  } catch (error) {
    console.error("Adaptive weight lookup failed:", error);
    return null;
  }
}

export async function getLearningSnapshot(
  supabase: Client,
  userId: string,
): Promise<LearningSnapshot> {
  const records = await fetchCompletedDecisions(supabase, userId);
  const performance = computePerformance(records);
  const signalEffectiveness = analyzeSignalEffectiveness(records);

  if (records.length < MIN_COMPLETED_TRADES) {
    return {
      performance,
      signalEffectiveness,
      weights: getDynamicWeights("sideways"),
      source: "default",
    };
  }

  return {
    performance,
    signalEffectiveness,
    weights: generateAdaptiveWeights(signalEffectiveness),
    source: "adaptive",
  };
}

export function resolveScoringWeights(
  regime: import("@/types/decision").MarketTrend,
  adaptiveWeights?: SignalWeights | null,
): SignalWeights {
  if (adaptiveWeights) {
    return adaptiveWeights;
  }
  return getDynamicWeights(regime);
}
