import {
  evaluateOutcomeSafe,
  type OutcomeEvaluationInput,
  type OutcomeEvaluationOutput,
} from "@/services/learning/outcomeEngine";
import {
  getTrustDisplay,
  INITIAL_TRUST_SCORE,
  updateTrustScoreSafe,
} from "@/services/learning/trustEngine";
import { TAKE_PROFIT_MULTIPLIER } from "@/services/risk/profitOptimization";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

type PendingDecisionRow =
  Database["public"]["Tables"]["decision_memory"]["Row"];

export type TrustOutcomeSnapshot = {
  trustScore: number;
  trustDelta: number;
  trustMessage: string;
  lastOutcome: OutcomeEvaluationOutput | null;
  lastClosedAt: string | null;
  stock: string | null;
};

export type ProcessPendingOutcomesResult = {
  evaluated: number;
  usersUpdated: number;
};

function parseFillPrice(signals: PendingDecisionRow["signals"]): number | null {
  if (!signals || typeof signals !== "object" || Array.isArray(signals)) {
    return null;
  }

  const fillPrice = (signals as Record<string, unknown>).fill_price;

  if (typeof fillPrice !== "number" || !Number.isFinite(fillPrice) || fillPrice <= 0) {
    return null;
  }

  return fillPrice;
}

function resolvePlannedExit(row: PendingDecisionRow, entryPrice: number): number {
  const stopLoss = Number(row.stop_loss ?? 0);

  if (Number(row.pnl ?? 0) <= 0 && stopLoss > 0) {
    return stopLoss;
  }

  return entryPrice * TAKE_PROFIT_MULTIPLIER;
}

function inferFollowedPlan(row: PendingDecisionRow, entryPrice: number): boolean {
  const exitPrice = Number(row.exit_price ?? 0);
  const stopLoss = Number(row.stop_loss ?? 0);
  const pnl = Number(row.pnl ?? 0);

  if (stopLoss > 0 && pnl <= 0) {
    return exitPrice <= stopLoss * 1.015;
  }

  if (pnl > 0) {
    return Boolean(row.take_profit_taken) || exitPrice >= entryPrice;
  }

  return pnl >= 0;
}

function buildOutcomeInput(row: PendingDecisionRow): OutcomeEvaluationInput | null {
  if (!row.stock || !row.entry_price || !row.exit_price) {
    return null;
  }

  const entryPrice = Number(row.entry_price);
  const exitPrice = Number(row.exit_price);
  const createdAt = new Date(row.created_at).getTime();
  const closedAt = new Date(row.updated_at).getTime();
  const fillPrice = parseFillPrice(row.signals);

  return {
    decisionId: row.id,
    stock: row.stock,
    plannedEntry: entryPrice,
    actualEntry: fillPrice ?? entryPrice,
    plannedExit: resolvePlannedExit(row, entryPrice),
    actualExit: exitPrice,
    followedPlan: inferFollowedPlan(row, entryPrice),
    profitLoss: Number(row.pnl ?? 0),
    holdingTime: Math.max(0, closedAt - createdAt),
  };
}

async function fetchPendingDecisions(
  supabase: Client,
  userId?: string,
): Promise<PendingDecisionRow[]> {
  let query = supabase
    .from("decision_memory")
    .select("*")
    .not("exit_price", "is", null)
    .is("trust_evaluated_at", null)
    .order("updated_at", { ascending: true })
    .limit(200);

  if (userId) {
    query = query.eq("user_id", userId);
  }

  const { data, error } = await query;

  if (error || !data) {
    return [];
  }

  return data;
}

async function readTrustScore(
  supabase: Client,
  userId: string,
): Promise<number> {
  const { data } = await supabase
    .from("user_trust_state")
    .select("trust_score")
    .eq("user_id", userId)
    .maybeSingle();

  if (data?.trust_score !== undefined && data.trust_score !== null) {
    return Math.max(0, Math.min(100, Math.round(Number(data.trust_score))));
  }

  return INITIAL_TRUST_SCORE;
}

async function persistTrustState(
  supabase: Client,
  userId: string,
  input: {
    trustScore: number;
    trustDelta: number;
    lastOutcome: OutcomeEvaluationOutput | null;
    lastDecisionId: string | null;
    lastClosedAt: string | null;
    stock: string | null;
  },
): Promise<void> {
  const { error } = await supabase.from("user_trust_state").upsert(
    {
      user_id: userId,
      trust_score: input.trustScore,
      last_trust_delta: input.trustDelta,
      last_outcome: input.lastOutcome,
      last_decision_id: input.lastDecisionId,
      last_closed_at: input.lastClosedAt,
      last_stock: input.stock,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" },
  );

  if (error) {
    throw new Error(error.message);
  }
}

export async function processPendingOutcomes(
  supabase: Client,
  userId?: string,
): Promise<ProcessPendingOutcomesResult> {
  const pending = await fetchPendingDecisions(supabase, userId);
  const usersTouched = new Set<string>();
  let evaluated = 0;

  const byUser = new Map<string, PendingDecisionRow[]>();

  for (const row of pending) {
    const existing = byUser.get(row.user_id) ?? [];
    existing.push(row);
    byUser.set(row.user_id, existing);
  }

  for (const [pendingUserId, rows] of byUser) {
    let trustScore = await readTrustScore(supabase, pendingUserId);
    let lastDelta = 0;
    let lastOutcome: OutcomeEvaluationOutput | null = null;
    let lastDecisionId: string | null = null;
    let lastClosedAt: string | null = null;
    let lastStock: string | null = null;

    for (const row of rows) {
      const input = buildOutcomeInput(row);

      if (!input) {
        continue;
      }

      const evaluation = evaluateOutcomeSafe(input);
      const trustUpdate = updateTrustScoreSafe(trustScore, {
        disciplineScore: evaluation.disciplineScore,
        executionQuality: evaluation.executionQuality,
        outcome: evaluation.outcome,
      });

      trustScore = trustUpdate.newTrustScore;
      lastDelta = trustUpdate.delta;
      lastOutcome = evaluation;
      lastDecisionId = row.id;
      lastClosedAt = row.updated_at;
      lastStock = row.stock;

      const { error: markError } = await supabase
        .from("decision_memory")
        .update({
          trust_evaluated_at: new Date().toISOString(),
          updated_at: row.updated_at,
        })
        .eq("id", row.id);

      if (markError) {
        throw new Error(markError.message);
      }

      evaluated += 1;
    }

    if (rows.length > 0 && lastOutcome) {
      await persistTrustState(supabase, pendingUserId, {
        trustScore,
        trustDelta: lastDelta,
        lastOutcome,
        lastDecisionId,
        lastClosedAt,
        stock: lastStock,
      });
      usersTouched.add(pendingUserId);
    }
  }

  return {
    evaluated,
    usersUpdated: usersTouched.size,
  };
}

function parseStoredOutcome(value: unknown): OutcomeEvaluationOutput | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  const record = value as Record<string, unknown>;
  const outcome = record.outcome;

  if (
    outcome !== "win" &&
    outcome !== "loss" &&
    outcome !== "breakeven"
  ) {
    return null;
  }

  return {
    outcome,
    disciplineScore: Number(record.disciplineScore ?? 50),
    executionQuality: Number(record.executionQuality ?? 50),
    trustDelta: Number(record.trustDelta ?? 0),
    summary: typeof record.summary === "string" ? record.summary : "",
  };
}

export async function getUserTrustSnapshot(
  supabase: Client,
  userId: string,
): Promise<TrustOutcomeSnapshot> {
  await processPendingOutcomes(supabase, userId);

  const { data, error } = await supabase
    .from("user_trust_state")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  if (!data) {
    const display = getTrustDisplay(INITIAL_TRUST_SCORE);

    return {
      trustScore: INITIAL_TRUST_SCORE,
      trustDelta: 0,
      trustMessage: display.message,
      lastOutcome: null,
      lastClosedAt: null,
      stock: null,
    };
  }

  const trustScore = Math.max(
    0,
    Math.min(100, Math.round(Number(data.trust_score ?? INITIAL_TRUST_SCORE))),
  );
  const display = getTrustDisplay(trustScore);

  return {
    trustScore,
    trustDelta: Number(data.last_trust_delta ?? 0),
    trustMessage: display.message,
    lastOutcome: parseStoredOutcome(data.last_outcome),
    lastClosedAt: data.last_closed_at,
    stock: data.last_stock,
  };
}
