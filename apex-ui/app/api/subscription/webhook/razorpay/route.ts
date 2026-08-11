import { apiError, apiOk } from "@/lib/api/response";
import {
  applyRazorpayWebhookSubscription,
  extractSubscriptionFromWebhook,
} from "@/services/subscription/billingSync";
import { verifyRazorpayWebhookSignature } from "@/services/subscription/razorpayClient";
import { readRazorpayConfig } from "@/services/subscription/razorpayConfig";

export const dynamic = "force-dynamic";

const HANDLED_EVENTS = new Set([
  "subscription.authenticated",
  "subscription.activated",
  "subscription.charged",
  "subscription.pending",
  "subscription.halted",
  "subscription.cancelled",
  "subscription.completed",
  "subscription.expired",
]);

export async function POST(request: Request) {
  const config = readRazorpayConfig();

  if (!config) {
    return apiError("Billing webhook is not configured", 503);
  }

  const rawBody = await request.text();
  const signature = request.headers.get("x-razorpay-signature");

  if (!verifyRazorpayWebhookSignature(rawBody, signature, config.webhookSecret)) {
    return apiError("Invalid webhook signature", 401);
  }

  let payload: unknown;

  try {
    payload = JSON.parse(rawBody) as unknown;
  } catch {
    return apiError("Invalid webhook payload", 400);
  }

  const event =
    payload && typeof payload === "object" && typeof (payload as Record<string, unknown>).event === "string"
      ? ((payload as Record<string, unknown>).event as string)
      : "";

  if (!HANDLED_EVENTS.has(event)) {
    return apiOk({ ignored: true, event });
  }

  const subscription = extractSubscriptionFromWebhook(payload);

  if (!subscription) {
    return apiError("Subscription entity missing from webhook", 400);
  }

  try {
    const result = await applyRazorpayWebhookSubscription(subscription);

    return apiOk({
      event,
      processed: Boolean(result),
      status: result?.status ?? subscription.status,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Webhook processing failed";
    return apiError(message, 500);
  }
}
