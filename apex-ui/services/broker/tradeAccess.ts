import type { SupabaseClient } from "@supabase/supabase-js";
import { listZerodhaAccessTokenCandidates } from "@/services/broker/accessToken";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type TradeTokenCandidate = {
  accessToken: string;
  source: "db" | "cookie";
};

export async function listTradeAccessTokens(
  supabase: Client,
  userId: string,
): Promise<TradeTokenCandidate[]> {
  return listZerodhaAccessTokenCandidates(supabase, userId);
}
