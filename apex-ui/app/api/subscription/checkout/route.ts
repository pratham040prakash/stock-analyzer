import { apiError, apiOk } from "@/lib/api/response";
import { createRazorpaySubscription } from "@/services/subscription/razorpayClient";
import {
  isRazorpayBillingEnabled,
  readRazorpayConfig,
  type BillingInterval,
} from "@/services/subscription/razorpayConfig";
import { resolvePremiumTierWithDb } from "@/services/subscription/premiumAccess";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

function parseInterval(value: unknown): BillingInterval {
  return value === "yearly" ? "yearly" : "monthly";
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

  const config = readRazorpayConfig();

  if (!config) {
    return apiError("Billing is not configured on the server", 503);
  }

  let interval: BillingInterval = "monthly";

  try {
    const body = (await request.json()) as { interval?: string };
    interval = parseInterval(body.interval);
  } catch {
    // default monthly
  }

  if (interval === "yearly" && !config.planIdYearly) {
    return apiError("Yearly billing is not available yet", 400);
  }

  const snapshot = await resolvePremiumTierWithDb(supabase, user);

  if (snapshot.tier === "premium") {
    return apiOk({
      alreadyPremium: true,
      message: "APEX Premium is already active on your account.",
      billingEnabled: true,
    });
  }

  try {
    const subscription = await createRazorpaySubscription({
      userId: user.id,
      interval,
    });

    return apiOk({
      billingEnabled: true,
      interval,
      subscriptionId: subscription.id,
      keyId: config.publicKeyId,
      shortUrl: subscription.short_url ?? null,
      message: "Open Razorpay checkout to authorize your subscription.",
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Could not start checkout";
    return apiError(message, 502);
  }
}
