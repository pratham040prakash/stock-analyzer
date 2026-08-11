import { apiError, apiOk } from "@/lib/api/response";
import { resolvePremiumTrialView } from "@/services/subscription/conversionFunnel";
import {
  buildTierResponse,
  resolvePremiumTierWithDb,
} from "@/services/subscription/premiumAccess";
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

  try {
    const [snapshot, trial] = await Promise.all([
      resolvePremiumTierWithDb(supabase, user),
      resolvePremiumTrialView(supabase, user),
    ]);

    return apiOk({
      ...buildTierResponse(snapshot),
      trial,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load subscription tier";
    return apiError(message, 500);
  }
}
