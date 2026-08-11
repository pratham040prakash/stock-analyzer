import { apiError, apiOk } from "@/lib/api/response";
import { syncPremiumSubscriptionFromRazorpay } from "@/services/subscription/billingSync";
import {
  isRazorpayBillingEnabled,
  readRazorpayConfig,
} from "@/services/subscription/razorpayConfig";
import {
  buildTierResponse,
  resolvePremiumTierWithDb,
} from "@/services/subscription/premiumAccess";
import {
  getPremiumSubscriptionByUserId,
  isActivePremiumSubscription,
} from "@/services/subscription/subscriptionRepository";
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

  const config = readRazorpayConfig();
  const row = await getPremiumSubscriptionByUserId(supabase, user.id);

  return apiOk({
    billingEnabled: Boolean(config),
    subscription: row
      ? {
          status: row.status,
          interval: row.billing_interval,
          currentPeriodEnd: row.current_period_end,
          active: isActivePremiumSubscription(row),
        }
      : null,
  });
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  if (!isRazorpayBillingEnabled()) {
    return apiError("Paid subscriptions are not available yet", 503);
  }

  let subscriptionId = "";

  try {
    const body = (await request.json()) as { subscriptionId?: string };
    subscriptionId = typeof body.subscriptionId === "string" ? body.subscriptionId.trim() : "";
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  if (!subscriptionId) {
    return apiError("subscriptionId is required", 400);
  }

  try {
    await syncPremiumSubscriptionFromRazorpay({
      subscriptionId,
      userId: user.id,
    });

    const snapshot = await resolvePremiumTierWithDb(supabase, user);

    return apiOk({
      ...buildTierResponse(snapshot),
      billingEnabled: true,
      message: "Subscription synced.",
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Could not sync subscription";
    return apiError(message, 502);
  }
}
