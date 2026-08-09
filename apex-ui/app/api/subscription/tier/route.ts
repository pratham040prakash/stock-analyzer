import { apiError, apiOk } from "@/lib/api/response";
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
    const snapshot = await resolvePremiumTierWithDb(supabase, user);
    return apiOk(buildTierResponse(snapshot));
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load subscription tier";
    return apiError(message, 500);
  }
}
