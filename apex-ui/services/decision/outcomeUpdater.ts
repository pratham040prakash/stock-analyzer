import { monitorStopLosses } from "@/services/risk/stopLossMonitor";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export async function updateOpenDecisionOutcomes(supabase: Client) {
  return monitorStopLosses(supabase);
}
