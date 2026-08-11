import { syncBrokerActivityFromKite } from "@/services/trade/syncBrokerActivity";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type BrokerReconcileResult = {
  synced: boolean;
  message: string;
};

export async function reconcileBrokerForReview(
  supabase: Client,
  userId: string,
): Promise<BrokerReconcileResult> {
  try {
    await syncBrokerActivityFromKite(supabase, userId);
    return {
      synced: true,
      message: "Broker activity reconciled with today's plan.",
    };
  } catch (error) {
    return {
      synced: false,
      message:
        error instanceof Error
          ? error.message
          : "Could not reconcile broker activity.",
    };
  }
}
