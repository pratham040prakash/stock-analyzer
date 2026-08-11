import { createAdminClient } from "@/lib/supabase/admin";
import {
  isPremiumActivationEnabled,
  validatePremiumAccessCode,
} from "@/services/subscription/activation";
import {
  readRazorpayConfig,
} from "@/services/subscription/razorpayConfig";
import {
  hasActivePremiumSubscription,
} from "@/services/subscription/subscriptionRepository";
import {
  resolvePremiumTier,
  tierFeatures,
  type ApexTier,
} from "@/services/subscription/tier";
import type { Database } from "@/types/database";
import type { User } from "@supabase/supabase-js";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type PremiumTierSnapshot = {
  tier: ApexTier;
  activationEnabled: boolean;
  billingEnabled: boolean;
};

async function resolvePaidPremium(
  supabase: Client,
  userId: string,
): Promise<boolean> {
  return hasActivePremiumSubscription(supabase, userId);
}

export async function hasPremiumActivation(
  supabase: Client,
  userId: string,
): Promise<boolean> {
  const { data, error } = await supabase
    .from("premium_activations")
    .select("user_id")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  return Boolean(data?.user_id);
}

export async function resolvePremiumTierWithDb(
  supabase: Client,
  user: User | null,
): Promise<PremiumTierSnapshot> {
  const activationEnabled = isPremiumActivationEnabled();
  const billingEnabled = Boolean(readRazorpayConfig());

  if (!user) {
    return { tier: "free", activationEnabled, billingEnabled };
  }

  const baseTier = resolvePremiumTier(user);

  if (baseTier === "premium") {
    return { tier: "premium", activationEnabled, billingEnabled };
  }

  const [activated, subscribed] = await Promise.all([
    hasPremiumActivation(supabase, user.id),
    resolvePaidPremium(supabase, user.id),
  ]);

  return {
    tier: activated || subscribed ? "premium" : "free",
    activationEnabled,
    billingEnabled,
  };
}

export async function resolvePremiumTierForUserId(
  admin: Client,
  userId: string,
): Promise<ApexTier> {
  if (process.env.APEX_PREMIUM_ALLOW_ALL === "true") {
    return "premium";
  }

  const activated = await hasPremiumActivation(admin, userId);

  if (activated) {
    return "premium";
  }

  const subscribed = await resolvePaidPremium(admin, userId);

  if (subscribed) {
    return "premium";
  }

  const {
    data: { user },
    error,
  } = await admin.auth.admin.getUserById(userId);

  if (error || !user) {
    return "free";
  }

  return resolvePremiumTier(user);
}

export async function activatePremiumAccess(
  supabase: Client,
  user: User,
  code: string,
): Promise<
  | { ok: true; tier: ApexTier; alreadyPremium: boolean }
  | { ok: false; reason: "disabled" | "invalid_code" }
> {
  const validation = validatePremiumAccessCode(code);

  if (validation.status === "disabled") {
    return { ok: false, reason: "disabled" };
  }

  if (validation.status !== "activated") {
    return { ok: false, reason: "invalid_code" };
  }

  const current = await resolvePremiumTierWithDb(supabase, user);

  if (current.tier === "premium") {
    return { ok: true, tier: "premium", alreadyPremium: true };
  }

  const admin = createAdminClient();
  const { error: insertError } = await admin.from("premium_activations").upsert(
    {
      user_id: user.id,
      code_label: validation.codeLabel,
      activated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" },
  );

  if (insertError) {
    throw new Error(insertError.message);
  }

  const existingMetadata = user.user_metadata ?? {};

  await admin.auth.admin.updateUserById(user.id, {
    user_metadata: {
      ...existingMetadata,
      apex_tier: "premium",
      premium_activated_at: new Date().toISOString(),
      premium_code_label: validation.codeLabel,
    },
  });

  return { ok: true, tier: "premium", alreadyPremium: false };
}

export function buildTierResponse(snapshot: PremiumTierSnapshot) {
  return {
    tier: snapshot.tier,
    features: tierFeatures(snapshot.tier),
    activationEnabled: snapshot.activationEnabled,
    billingEnabled: snapshot.billingEnabled,
  };
}
