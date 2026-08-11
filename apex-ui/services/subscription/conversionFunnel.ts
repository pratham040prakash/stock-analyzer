import { createAdminClient } from "@/lib/supabase/admin";
import {
  PREMIUM_TRIAL_BODY,
  PREMIUM_TRIAL_HEADLINE,
  readPremiumTrialDays,
  isPremiumTrialEnabled,
} from "@/lib/subscription/premiumCopy";
import { resolvePremiumTier } from "@/services/subscription/tier";
import {
  claimPremiumTrialOffer,
  countWaitReceipts,
  dismissPremiumTrialOffer,
  getPremiumTrialOffer,
  insertPremiumTrialOffer,
  isPremiumTrialActive,
  type PremiumTrialOfferRow,
} from "@/services/subscription/trialOfferRepository";
import { hasActivePremiumSubscription } from "@/services/subscription/subscriptionRepository";
import type { User } from "@supabase/supabase-js";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type PremiumTrialStatus = "none" | "offer" | "active" | "expired";

export type PremiumTrialView = {
  status: PremiumTrialStatus;
  enabled: boolean;
  days: number;
  headline: string;
  body: string;
  expiresAt: string | null;
  daysRemaining: number | null;
};

function buildTrialView(
  row: PremiumTrialOfferRow | null,
  enabled: boolean,
): PremiumTrialView {
  const days = readPremiumTrialDays();
  const base = {
    enabled,
    days,
    headline: PREMIUM_TRIAL_HEADLINE,
    body: PREMIUM_TRIAL_BODY.replace("{days}", String(days)),
  };

  if (!row) {
    return { ...base, status: "none", expiresAt: null, daysRemaining: null };
  }

  if (isPremiumTrialActive(row) && row.expires_at) {
    const msLeft = new Date(row.expires_at).getTime() - Date.now();
    const daysRemaining = Math.max(1, Math.ceil(msLeft / 86_400_000));

    return {
      ...base,
      status: "active",
      expiresAt: row.expires_at,
      daysRemaining,
    };
  }

  if (row.claimed_at && row.expires_at) {
    return {
      ...base,
      status: "expired",
      expiresAt: row.expires_at,
      daysRemaining: 0,
    };
  }

  if (row.dismissed_at) {
    return { ...base, status: "none", expiresAt: null, daysRemaining: null };
  }

  return { ...base, status: "offer", expiresAt: null, daysRemaining: null };
}

async function isTrialEligibleUser(
  supabase: Client,
  user: User,
): Promise<boolean> {
  if (!isPremiumTrialEnabled()) {
    return false;
  }

  if (resolvePremiumTier(user) === "premium") {
    return false;
  }

  const [activated, subscribed, existingOffer] = await Promise.all([
    supabase
      .from("premium_activations")
      .select("user_id")
      .eq("user_id", user.id)
      .maybeSingle()
      .then(({ data }) => Boolean(data?.user_id)),
    hasActivePremiumSubscription(supabase, user.id),
    getPremiumTrialOffer(supabase, user.id),
  ]);

  if (activated || subscribed) {
    return false;
  }

  if (existingOffer?.claimed_at) {
    return false;
  }

  return true;
}

export async function resolvePremiumTrialView(
  supabase: Client,
  user: User | null,
): Promise<PremiumTrialView> {
  const enabled = isPremiumTrialEnabled();

  if (!user || !enabled) {
    return buildTrialView(null, enabled);
  }

  const row = await getPremiumTrialOffer(supabase, user.id);
  return buildTrialView(row, enabled);
}

export async function isUserOnActivePremiumTrial(
  supabase: Client,
  userId: string,
): Promise<boolean> {
  const row = await getPremiumTrialOffer(supabase, userId);
  return isPremiumTrialActive(row);
}

export async function maybeOfferPremiumTrialAfterWaitReceipt(
  supabase: Client,
  user: User,
  receiptId: string,
): Promise<PremiumTrialView> {
  if (!(await isTrialEligibleUser(supabase, user))) {
    return resolvePremiumTrialView(supabase, user);
  }

  const waitCount = await countWaitReceipts(supabase, user.id);

  if (waitCount !== 1) {
    return resolvePremiumTrialView(supabase, user);
  }

  const admin = createAdminClient();
  await insertPremiumTrialOffer(admin, {
    userId: user.id,
    triggerReceiptId: receiptId,
  });

  return resolvePremiumTrialView(supabase, user);
}

export async function claimPremiumTrial(
  supabase: Client,
  user: User,
): Promise<PremiumTrialView> {
  const row = await getPremiumTrialOffer(supabase, user.id);

  if (!row || row.claimed_at || row.dismissed_at) {
    throw new Error("No premium trial offer is available");
  }

  const days = readPremiumTrialDays();
  const expiresAt = new Date(Date.now() + days * 86_400_000).toISOString();
  const admin = createAdminClient();
  const claimed = await claimPremiumTrialOffer(admin, user.id, expiresAt);

  if (!claimed) {
    throw new Error("Could not start premium trial");
  }

  const existingMetadata = user.user_metadata ?? {};

  await admin.auth.admin.updateUserById(user.id, {
    user_metadata: {
      ...existingMetadata,
      apex_tier: "premium",
      premium_trial_started_at: new Date().toISOString(),
      premium_trial_expires_at: expiresAt,
    },
  });

  return resolvePremiumTrialView(supabase, user);
}

export async function dismissPremiumTrial(
  supabase: Client,
  userId: string,
): Promise<PremiumTrialView> {
  const admin = createAdminClient();
  await dismissPremiumTrialOffer(admin, userId);
  const row = await getPremiumTrialOffer(supabase, userId);
  return buildTrialView(row, isPremiumTrialEnabled());
}

export function runConversionFunnelSelfCheck(): void {
  const days = readPremiumTrialDays();

  if (days < 1 || days > 30) {
    throw new Error("Conversion funnel self-check failed: trial days bounds");
  }

  if (!PREMIUM_TRIAL_BODY.includes("{days}")) {
    throw new Error("Conversion funnel self-check failed: trial body template");
  }
}
