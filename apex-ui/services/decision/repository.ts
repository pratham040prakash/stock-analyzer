import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";
import type {
  DailyDecisionOutput,
  DailyDecisionType,
  DecisionActionType,
} from "@/types/decision";
import { dailyDecisionTypeToAction } from "@/types/decision";
import type { DecisionHistoryEntry } from "@/types/decisionHistory";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";

type Client = SupabaseClient<Database>;

function utcDateString(date = new Date()): string {
  return date.toISOString().slice(0, 10);
}

export async function saveDailyDecision(
  supabase: Client,
  userId: string,
  output: DailyDecisionOutput,
): Promise<void> {
  const decisionDate = utcDateString();

  const { error } = await supabase.from("decisions").upsert(
    {
      user_id: userId,
      decision_date: decisionDate,
      decision: output.decision,
      action: output.action,
      stock: output.stock ?? null,
      confidence: output.confidence,
      reason: output.reason,
      actions: output.actions,
    },
    { onConflict: "user_id,decision_date" },
  );

  if (error) {
    throw new Error(error.message);
  }
}

export async function getLatestDailyDecision(
  supabase: Client,
  userId: string,
): Promise<DailyDecisionOutput | null> {
  const { data, error } = await supabase
    .from("decisions")
    .select(
      "decision, action, stock, confidence, reason, actions, created_at, decision_date",
    )
    .eq("user_id", userId)
    .order("decision_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return mapStoredDecision(data);
}

function mapStoredDecision(data: {
  decision: string;
  action?: string | null;
  stock?: string | null;
  confidence: number;
  reason: string;
  actions: unknown;
}): DailyDecisionOutput {
  const decision = data.decision as DailyDecisionType;
  const action =
    (data.action as DecisionActionType | null) ??
    dailyDecisionTypeToAction(decision);

  return {
    decision,
    action,
    stock: data.stock ?? undefined,
    confidence: Number(data.confidence),
    reason: data.reason,
    confidence_factors: [],
    actions: Array.isArray(data.actions) ? (data.actions as string[]) : [],
  };
}

export async function getTodayDailyDecision(
  supabase: Client,
  userId: string,
): Promise<(DailyDecisionOutput & { created_at: string }) | null> {
  const today = utcDateString();

  const { data, error } = await supabase
    .from("decisions")
    .select(
      "decision, action, stock, confidence, reason, actions, created_at, decision_date",
    )
    .eq("user_id", userId)
    .eq("decision_date", today)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return {
    ...mapStoredDecision(data),
    created_at: data.created_at,
  };
}

export async function getDecisionHistory(
  supabase: Client,
  userId: string,
  days = 3,
): Promise<DecisionHistoryEntry[]> {
  const result = await getDisciplineHistory(supabase, userId, days);
  return result.history;
}
