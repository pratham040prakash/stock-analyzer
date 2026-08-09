import { apiError, apiOk } from "@/lib/api/response";
import {
  resolvePremiumTier,
  tierFeatures,
} from "@/services/subscription/tier";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const tier = resolvePremiumTier(user);

  return apiOk({
    tier,
    features: tierFeatures(tier),
  });
}
