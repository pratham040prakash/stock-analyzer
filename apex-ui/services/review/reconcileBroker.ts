import { syncBrokerActivityFromKite } from "@/services/trade/syncBrokerActivity";
import type { BrokerActivitySyncResult } from "@/services/trade/syncBrokerActivity";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type BrokerReconcileResult = {
  synced: boolean;
  message: string;
  sync?: BrokerActivitySyncResult;
};

export async function reconcileBrokerForReview(
  supabase: Client,
  userId: string,
): Promise<BrokerReconcileResult> {
  try {
    const sync = await syncBrokerActivityFromKite(supabase, userId);

    if (sync.status === "OK") {
      return {
        synced: true,
        message: `Reconciled ${sync.imported} fill(s) from broker.`,
        sync,
      };
    }

    if (sync.status === "NOT_CONNECTED") {
      return {
        synced: false,
        message: "Connect Zerodha to reconcile broker fills.",
        sync,
      };
    }

    if (sync.status === "TOKEN_EXPIRED") {
      return {
        synced: false,
        message: "Zerodha session expired — reconnect to reconcile.",
        sync,
      };
    }

    return {
      synced: false,
      message: sync.message,
      sync,
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
