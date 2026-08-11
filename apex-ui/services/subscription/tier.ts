import type { User } from "@supabase/supabase-js";

export type ApexTier = "free" | "premium";

export type TierFeatures = {
  marginMode: boolean;
  decisionDepth: boolean;
  decisionHistory: boolean;
  reviewDigest: boolean;
  thesisExport: boolean;
  trustCdqsHistory: boolean;
};

export function tierFeatures(tier: ApexTier): TierFeatures {
  if (tier === "premium") {
    return {
      marginMode: true,
      decisionDepth: true,
      decisionHistory: true,
      reviewDigest: true,
      thesisExport: true,
      trustCdqsHistory: true,
    };
  }

  return {
    marginMode: false,
    decisionDepth: false,
    decisionHistory: false,
    reviewDigest: false,
    thesisExport: false,
    trustCdqsHistory: false,
  };
}

function readAllowListedUserIds(): string[] {
  const raw = process.env.APEX_PREMIUM_USER_IDS?.trim();

  if (!raw) {
    return [];
  }

  return raw
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

function readTierFromMetadata(user: User): ApexTier | null {
  const userMeta = user.user_metadata ?? {};
  const appMeta = user.app_metadata ?? {};

  const candidates = [
    userMeta.subscription_tier,
    userMeta.apex_tier,
    appMeta.apex_tier,
    appMeta.subscription_tier,
  ];

  for (const value of candidates) {
    if (typeof value !== "string") {
      continue;
    }

    const normalized = value.trim().toLowerCase();

    if (normalized === "premium" || normalized === "pro") {
      return "premium";
    }
  }

  return null;
}

export function resolvePremiumTier(user: User | null): ApexTier {
  if (!user) {
    return "free";
  }

  if (process.env.APEX_PREMIUM_ALLOW_ALL === "true") {
    return "premium";
  }

  if (readAllowListedUserIds().includes(user.id)) {
    return "premium";
  }

  return readTierFromMetadata(user) ?? "free";
}
