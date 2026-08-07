import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";
import type { DailyDecisionOutput, DailyDecisionType } from "@/types/decision";

type Client = SupabaseClient<Database>;

export async function saveDailyDecision(
  supabase: Client,
  userId: string,
  output: DailyDecisionOutput,
): Promise<void> {
  const { error } = await supabase.from("decisions").insert({
    user_id: userId,
    decision: output.decision,
    confidence: output.confidence,
    reason: output.reason,
    actions: output.actions,
  });

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
    .select("decision, confidence, reason, actions, created_at")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return {
    decision: data.decision as DailyDecisionType,
    confidence: Number(data.confidence),
    reason: data.reason,
    actions: Array.isArray(data.actions)
      ? (data.actions as string[])
      : [],
  };
}

export async function getTodayDailyDecision(
  supabase: Client,
  userId: string,
): Promise<(DailyDecisionOutput & { created_at: string }) | null> {
  const startOfDay = new Date();
  startOfDay.setUTCHours(0, 0, 0, 0);

  const { data, error } = await supabase
    .from("decisions")
    .select("decision, confidence, reason, actions, created_at")
    .eq("user_id", userId)
    .gte("created_at", startOfDay.toISOString())
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return {
    decision: data.decision as DailyDecisionType,
    confidence: Number(data.confidence),
    reason: data.reason,
    actions: Array.isArray(data.actions)
      ? (data.actions as string[])
      : [],
    created_at: data.created_at,
  };
}
