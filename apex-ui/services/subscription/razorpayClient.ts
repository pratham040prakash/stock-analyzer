import { createHmac, timingSafeEqual } from "node:crypto";
import {
  readRazorpayConfig,
  resolvePlanId,
  type BillingInterval,
  type RazorpayConfig,
} from "@/services/subscription/razorpayConfig";

export type RazorpaySubscriptionPayload = {
  id: string;
  plan_id: string;
  status: string;
  current_end: number | null;
  short_url?: string | null;
  notes?: Record<string, string | undefined>;
};

type RazorpayApiError = {
  error?: {
    description?: string;
    code?: string;
  };
};

function authHeader(config: RazorpayConfig): string {
  const token = Buffer.from(`${config.keyId}:${config.keySecret}`).toString("base64");
  return `Basic ${token}`;
}

async function razorpayRequest<T>(
  config: RazorpayConfig,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`https://api.razorpay.com/v1${path}`, {
    ...init,
    headers: {
      Authorization: authHeader(config),
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  const payload = (await response.json().catch(() => null)) as T | RazorpayApiError | null;

  if (!response.ok) {
    const message =
      payload &&
      typeof payload === "object" &&
      "error" in payload &&
      payload.error?.description
        ? payload.error.description
        : `Razorpay request failed (${response.status})`;
    throw new Error(message);
  }

  if (!payload || typeof payload !== "object") {
    throw new Error("Razorpay returned an empty response");
  }

  return payload as T;
}

export function verifyRazorpayWebhookSignature(
  rawBody: string,
  signature: string | null,
  webhookSecret: string,
): boolean {
  if (!signature?.trim()) {
    return false;
  }

  const expected = createHmac("sha256", webhookSecret).update(rawBody).digest("hex");
  const left = Buffer.from(expected);
  const right = Buffer.from(signature.trim());

  if (left.length !== right.length) {
    return false;
  }

  return timingSafeEqual(left, right);
}

export function parseRazorpayPeriodEnd(currentEnd: number | null): string | null {
  if (!currentEnd || currentEnd <= 0) {
    return null;
  }

  return new Date(currentEnd * 1000).toISOString();
}

export function inferBillingInterval(
  planId: string,
  config: RazorpayConfig,
): BillingInterval {
  if (config.planIdYearly && planId === config.planIdYearly) {
    return "yearly";
  }

  return "monthly";
}

export async function createRazorpaySubscription(input: {
  userId: string;
  interval: BillingInterval;
}): Promise<RazorpaySubscriptionPayload> {
  const config = readRazorpayConfig();

  if (!config) {
    throw new Error("Razorpay billing is not configured");
  }

  const planId = resolvePlanId(config, input.interval);

  if (!planId) {
    throw new Error("Selected billing interval is not available");
  }

  return razorpayRequest<RazorpaySubscriptionPayload>(config, "/subscriptions", {
    method: "POST",
    body: JSON.stringify({
      plan_id: planId,
      total_count: input.interval === "yearly" ? 10 : 120,
      customer_notify: 1,
      notes: {
        user_id: input.userId,
        billing_interval: input.interval,
      },
    }),
  });
}

export async function fetchRazorpaySubscription(
  subscriptionId: string,
): Promise<RazorpaySubscriptionPayload> {
  const config = readRazorpayConfig();

  if (!config) {
    throw new Error("Razorpay billing is not configured");
  }

  return razorpayRequest<RazorpaySubscriptionPayload>(
    config,
    `/subscriptions/${encodeURIComponent(subscriptionId)}`,
  );
}

export function runRazorpayClientSelfCheck(): void {
  const signature = createHmac("sha256", "secret")
    .update('{"event":"subscription.activated"}')
    .digest("hex");

  if (
    !verifyRazorpayWebhookSignature(
      '{"event":"subscription.activated"}',
      signature,
      "secret",
    )
  ) {
    throw new Error("Razorpay client self-check failed: signature verify");
  }

  if (
    verifyRazorpayWebhookSignature(
      '{"event":"subscription.activated"}',
      "invalid",
      "secret",
    )
  ) {
    throw new Error("Razorpay client self-check failed: invalid signature accepted");
  }

  const parsed = parseRazorpayPeriodEnd(1_700_000_000);

  if (!parsed || !parsed.endsWith("Z")) {
    throw new Error("Razorpay client self-check failed: period end parse");
  }
}
