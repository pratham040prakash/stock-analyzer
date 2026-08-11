import { apiError } from "@/lib/api/response";
import {
  resolvePremiumTierWithDb,
  type PremiumTierSnapshot,
} from "@/services/subscription/premiumAccess";
import { tierFeatures, type ApexTier, type TierFeatures } from "@/services/subscription/tier";
import type { Database } from "@/types/database";
import type { SupabaseClient, User } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type PremiumAccessResult =
  | {
      ok: true;
      tier: ApexTier;
      features: TierFeatures;
      snapshot: PremiumTierSnapshot;
    }
  | {
      ok: false;
      status: 403;
      message: string;
    };

export async function requirePremiumFeature(
  supabase: Client,
  user: User,
  feature: keyof TierFeatures,
): Promise<PremiumAccessResult> {
  const snapshot = await resolvePremiumTierWithDb(supabase, user);
  const features = tierFeatures(snapshot.tier);

  if (features[feature]) {
    return { ok: true, tier: snapshot.tier, features, snapshot };
  }

  return {
    ok: false,
    status: 403,
    message: "This feature requires APEX Premium.",
  };
}

export function premiumDeniedResponse(result: Extract<PremiumAccessResult, { ok: false }>) {
  return apiError(result.message, result.status);
}
