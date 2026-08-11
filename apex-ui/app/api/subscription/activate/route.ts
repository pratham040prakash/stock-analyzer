import { apiError, apiOk } from "@/lib/api/response";
import {
  activatePremiumAccess,
  buildTierResponse,
} from "@/services/subscription/premiumAccess";
import { isPremiumActivationEnabled } from "@/services/subscription/activation";
import { readRazorpayConfig } from "@/services/subscription/razorpayConfig";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  const code =
    body && typeof body === "object" && typeof (body as Record<string, unknown>).code === "string"
      ? ((body as Record<string, unknown>).code as string).trim()
      : "";

  if (!code) {
    return apiError("Access code is required", 400);
  }

  try {
    const result = await activatePremiumAccess(supabase, user, code);

    if (!result.ok) {
      if (result.reason === "disabled") {
        return apiError("Premium activation is not available yet", 503);
      }

      return apiError("Invalid access code", 400);
    }

    return apiOk({
      ...buildTierResponse({
        tier: result.tier,
        activationEnabled: isPremiumActivationEnabled(),
        billingEnabled: Boolean(readRazorpayConfig()),
      }),
      alreadyPremium: result.alreadyPremium,
      message: result.alreadyPremium
        ? "APEX Premium is already active on your account."
        : "APEX Premium is now active.",
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Premium activation failed";
    return apiError(message, 500);
  }
}
