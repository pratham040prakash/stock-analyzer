import {
  isPremiumSubscriptionStatus,
  type BillingInterval,
} from "@/services/subscription/razorpayConfig";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type PremiumSubscriptionRow =
  Database["public"]["Tables"]["premium_subscriptions"]["Row"];

export type PremiumSubscriptionUpsert = {
  userId: string;
  razorpaySubscriptionId: string;
  razorpayPlanId: string;
  billingInterval: BillingInterval;
  status: string;
  currentPeriodEnd: string | null;
};

export async function getPremiumSubscriptionByUserId(
  supabase: Client,
  userId: string,
): Promise<PremiumSubscriptionRow | null> {
  const { data, error } = await supabase
    .from("premium_subscriptions")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function getPremiumSubscriptionByRazorpayId(
  supabase: Client,
  razorpaySubscriptionId: string,
): Promise<PremiumSubscriptionRow | null> {
  const { data, error } = await supabase
    .from("premium_subscriptions")
    .select("*")
    .eq("razorpay_subscription_id", razorpaySubscriptionId)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function upsertPremiumSubscription(
  supabase: Client,
  input: PremiumSubscriptionUpsert,
): Promise<void> {
  const { error } = await supabase.from("premium_subscriptions").upsert(
    {
      user_id: input.userId,
      razorpay_subscription_id: input.razorpaySubscriptionId,
      razorpay_plan_id: input.razorpayPlanId,
      billing_interval: input.billingInterval,
      status: input.status,
      current_period_end: input.currentPeriodEnd,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" },
  );

  if (error) {
    throw new Error(error.message);
  }
}

export function isActivePremiumSubscription(
  row: PremiumSubscriptionRow | null,
): boolean {
  if (!row) {
    return false;
  }

  return isPremiumSubscriptionStatus(row.status, row.current_period_end);
}

export async function hasActivePremiumSubscription(
  supabase: Client,
  userId: string,
): Promise<boolean> {
  const row = await getPremiumSubscriptionByUserId(supabase, userId);
  return isActivePremiumSubscription(row);
}

export function runSubscriptionRepositorySelfCheck(): void {
  const sample = {
    user_id: "00000000-0000-0000-0000-000000000000",
    razorpay_subscription_id: "sub_test",
    razorpay_plan_id: "plan_test",
    billing_interval: "monthly" as const,
    status: "active",
    current_period_end: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  if (!isActivePremiumSubscription(sample)) {
    throw new Error("Subscription repository self-check failed: active row");
  }

  if (
    isActivePremiumSubscription({
      ...sample,
      status: "cancelled",
    })
  ) {
    throw new Error("Subscription repository self-check failed: cancelled row");
  }
}
