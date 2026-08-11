import { apiError, apiOk } from "@/lib/api/response";
import {
  claimPremiumTrial,
  dismissPremiumTrial,
  resolvePremiumTrialView,
} from "@/services/subscription/conversionFunnel";
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
    const trial = await resolvePremiumTrialView(supabase, user);
    return apiOk({ trial });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load premium trial";
    return apiError(message, 500);
  }
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let action: "claim" | "dismiss" = "claim";

  try {
    const body = (await request.json()) as { action?: string };
    if (body.action === "dismiss") {
      action = "dismiss";
    }
  } catch {
    // default claim
  }

  try {
    const trial =
      action === "dismiss"
        ? await dismissPremiumTrial(supabase, user.id)
        : await claimPremiumTrial(supabase, user);

    const snapshot = await resolvePremiumTierWithDb(supabase, user);

    return apiOk({
      ...buildTierResponse(snapshot),
      trial,
      message:
        action === "dismiss"
          ? "Trial offer dismissed."
          : "Premium trial is active.",
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Premium trial request failed";
    return apiError(message, 400);
  }
}
