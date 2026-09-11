import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";
import type {
  DailyDecisionArtifact,
} from "@/types/decision";
import { validateDailyDecisionArtifact } from "@/types/decision";
import type { DecisionHistoryEntry } from "@/types/decisionHistory";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";

type Client = SupabaseClient<Database>;

export async function saveDailyDecision(
  supabase: Client,
  userId: string,
  artifact: DailyDecisionArtifact,
): Promise<void> {
  if (!validateDailyDecisionArtifact(artifact)) {
    throw new Error("Refusing to persist invalid daily decision artifact");
  }
  const decisionDate = tradingDateKey();
  if (artifact.decision_date !== decisionDate) {
    throw new Error("Refusing to persist artifact for a different trading day");
  }
  const output = artifact.projection;

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
      artifact: artifact as unknown as Database["public"]["Tables"]["decisions"]["Insert"]["artifact"],
      frozen_at: artifact.frozen_at,
      schema_version: artifact.schema_version,
      intent: artifact.intent,
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
): Promise<DailyDecisionArtifact | null> {
  const { data, error } = await supabase
    .from("decisions")
    .select(
      "artifact, created_at, decision_date",
    )
    .eq("user_id", userId)
    .order("decision_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return mapStoredArtifact(data);
}

function mapStoredArtifact(data: {
  artifact?: unknown;
}): DailyDecisionArtifact | null {
  return validateDailyDecisionArtifact(data.artifact) ? data.artifact : null;
}

export async function getTodayDailyDecision(
  supabase: Client,
  userId: string,
): Promise<DailyDecisionArtifact | null> {
  const today = tradingDateKey();

  const { data, error } = await supabase
    .from("decisions")
    .select(
      "artifact, created_at, decision_date",
    )
    .eq("user_id", userId)
    .eq("decision_date", today)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  // Legacy rows without a complete v1 artifact are intentionally non-executable.
  return mapStoredArtifact(data);
}

export async function getDecisionHistory(
  supabase: Client,
  userId: string,
  days = 3,
): Promise<DecisionHistoryEntry[]> {
  const result = await getDisciplineHistory(supabase, userId, days);
  return result.history;
}
