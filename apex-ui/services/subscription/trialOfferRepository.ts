import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type PremiumTrialOfferRow =
  Database["public"]["Tables"]["premium_trial_offers"]["Row"];

export async function getPremiumTrialOffer(
  supabase: Client,
  userId: string,
): Promise<PremiumTrialOfferRow | null> {
  const { data, error } = await supabase
    .from("premium_trial_offers")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function countWaitReceipts(
  supabase: Client,
  userId: string,
): Promise<number> {
  const { count, error } = await supabase
    .from("decision_receipts")
    .select("id", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("execution_kind", "WAIT");

  if (error) {
    throw new Error(error.message);
  }

  return count ?? 0;
}

export async function insertPremiumTrialOffer(
  supabase: Client,
  input: { userId: string; triggerReceiptId: string },
): Promise<PremiumTrialOfferRow | null> {
  const { data, error } = await supabase
    .from("premium_trial_offers")
    .insert({
      user_id: input.userId,
      trigger_receipt_id: input.triggerReceiptId,
    })
    .select("*")
    .maybeSingle();

  if (error) {
    if (error.code === "23505") {
      return getPremiumTrialOffer(supabase, input.userId);
    }

    throw new Error(error.message);
  }

  return data;
}

export async function claimPremiumTrialOffer(
  supabase: Client,
  userId: string,
  expiresAt: string,
): Promise<PremiumTrialOfferRow | null> {
  const { data, error } = await supabase
    .from("premium_trial_offers")
    .update({
      claimed_at: new Date().toISOString(),
      expires_at: expiresAt,
      dismissed_at: null,
    })
    .eq("user_id", userId)
    .is("claimed_at", null)
    .select("*")
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function dismissPremiumTrialOffer(
  supabase: Client,
  userId: string,
): Promise<boolean> {
  const { error } = await supabase
    .from("premium_trial_offers")
    .update({ dismissed_at: new Date().toISOString() })
    .eq("user_id", userId)
    .is("claimed_at", null);

  return !error;
}

export function isPremiumTrialActive(row: PremiumTrialOfferRow | null): boolean {
  if (!row?.claimed_at || !row.expires_at) {
    return false;
  }

  if (row.dismissed_at && !row.claimed_at) {
    return false;
  }

  return new Date(row.expires_at).getTime() > Date.now();
}

export function runTrialOfferRepositorySelfCheck(): void {
  const active = isPremiumTrialActive({
    user_id: "00000000-0000-0000-0000-000000000000",
    trigger_receipt_id: "00000000-0000-0000-0000-000000000001",
    offered_at: new Date().toISOString(),
    claimed_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 86_400_000).toISOString(),
    dismissed_at: null,
  });

  if (!active) {
    throw new Error("Trial offer repository self-check failed: active trial");
  }

  const expired = isPremiumTrialActive({
    user_id: "00000000-0000-0000-0000-000000000000",
    trigger_receipt_id: "00000000-0000-0000-0000-000000000001",
    offered_at: new Date().toISOString(),
    claimed_at: new Date().toISOString(),
    expires_at: new Date(Date.now() - 86_400_000).toISOString(),
    dismissed_at: null,
  });

  if (expired) {
    throw new Error("Trial offer repository self-check failed: expired trial");
  }
}
