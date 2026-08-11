import { createAdminClient } from "@/lib/supabase/admin";
import {
  fetchRazorpaySubscription,
  inferBillingInterval,
  parseRazorpayPeriodEnd,
  type RazorpaySubscriptionPayload,
} from "@/services/subscription/razorpayClient";
import { readRazorpayConfig } from "@/services/subscription/razorpayConfig";
import {
  getPremiumSubscriptionByRazorpayId,
  upsertPremiumSubscription,
} from "@/services/subscription/subscriptionRepository";

function readUserIdFromSubscription(
  subscription: RazorpaySubscriptionPayload,
): string | null {
  const fromNotes = subscription.notes?.user_id?.trim();
  return fromNotes || null;
}

export async function syncPremiumSubscriptionFromRazorpay(input: {
  subscriptionId: string;
  userId?: string | null;
}): Promise<{ userId: string; status: string }> {
  const config = readRazorpayConfig();

  if (!config) {
    throw new Error("Razorpay billing is not configured");
  }

  const subscription = await fetchRazorpaySubscription(input.subscriptionId);
  const admin = createAdminClient();

  const existing = await getPremiumSubscriptionByRazorpayId(admin, subscription.id);
  const userId =
    input.userId?.trim() ||
    readUserIdFromSubscription(subscription) ||
    existing?.user_id ||
    null;

  if (!userId) {
    throw new Error("Could not resolve subscription owner");
  }

  const billingInterval = inferBillingInterval(subscription.plan_id, config);

  await upsertPremiumSubscription(admin, {
    userId,
    razorpaySubscriptionId: subscription.id,
    razorpayPlanId: subscription.plan_id,
    billingInterval,
    status: subscription.status,
    currentPeriodEnd: parseRazorpayPeriodEnd(subscription.current_end),
  });

  await syncUserPremiumMetadata(admin, userId, subscription.status);

  return { userId, status: subscription.status };
}

export async function applyRazorpayWebhookSubscription(
  subscription: RazorpaySubscriptionPayload,
): Promise<{ userId: string; status: string } | null> {
  const userId = readUserIdFromSubscription(subscription);

  if (!userId) {
    const admin = createAdminClient();
    const existing = await getPremiumSubscriptionByRazorpayId(admin, subscription.id);
    if (!existing?.user_id) {
      return null;
    }

    return syncPremiumSubscriptionFromRazorpay({
      subscriptionId: subscription.id,
      userId: existing.user_id,
    });
  }

  return syncPremiumSubscriptionFromRazorpay({
    subscriptionId: subscription.id,
    userId,
  });
}

async function syncUserPremiumMetadata(
  admin: ReturnType<typeof createAdminClient>,
  userId: string,
  status: string,
): Promise<void> {
  const {
    data: { user },
    error,
  } = await admin.auth.admin.getUserById(userId);

  if (error || !user) {
    return;
  }

  const existingMetadata = user.user_metadata ?? {};
  const isActive = status === "active" || status === "authenticated";

  await admin.auth.admin.updateUserById(userId, {
    user_metadata: {
      ...existingMetadata,
      apex_tier: isActive ? "premium" : "free",
      premium_billing_status: status,
      premium_billing_updated_at: new Date().toISOString(),
    },
  });
}

export function extractSubscriptionFromWebhook(payload: unknown): RazorpaySubscriptionPayload | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const body = payload as Record<string, unknown>;
  const entity =
    body.payload &&
    typeof body.payload === "object" &&
    (body.payload as Record<string, unknown>).subscription &&
    typeof (body.payload as Record<string, unknown>).subscription === "object"
      ? ((body.payload as Record<string, unknown>).subscription as Record<string, unknown>).entity
      : null;

  if (!entity || typeof entity !== "object") {
    return null;
  }

  const subscription = entity as Record<string, unknown>;

  if (typeof subscription.id !== "string" || typeof subscription.status !== "string") {
    return null;
  }

  return {
    id: subscription.id,
    plan_id: typeof subscription.plan_id === "string" ? subscription.plan_id : "",
    status: subscription.status,
    current_end:
      typeof subscription.current_end === "number" ? subscription.current_end : null,
    short_url:
      typeof subscription.short_url === "string" ? subscription.short_url : null,
    notes:
      subscription.notes && typeof subscription.notes === "object"
        ? (subscription.notes as Record<string, string | undefined>)
        : undefined,
  };
}

export function runBillingSyncSelfCheck(): void {
  const payload = extractSubscriptionFromWebhook({
    event: "subscription.activated",
    payload: {
      subscription: {
        entity: {
          id: "sub_test",
          plan_id: "plan_test",
          status: "active",
          current_end: 1_700_000_000,
          notes: { user_id: "00000000-0000-0000-0000-000000000000" },
        },
      },
    },
  });

  if (!payload || payload.id !== "sub_test") {
    throw new Error("Billing sync self-check failed: webhook parse");
  }
}
