import { processPendingOutcomes } from "@/services/decision/trustOutcome";
import { monitorStopLosses } from "@/services/risk/stopLossMonitor";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export async function updateOpenDecisionOutcomes(supabase: Client) {
  const monitorResult = await monitorStopLosses(supabase);
  const trustResult = await processPendingOutcomes(supabase);

  return {
    ...monitorResult,
    trustEvaluated: trustResult.evaluated,
    trustUsersUpdated: trustResult.usersUpdated,
  };
}
