export type BillingInterval = "monthly" | "yearly";

export type RazorpayConfig = {
  enabled: boolean;
  keyId: string;
  keySecret: string;
  webhookSecret: string;
  publicKeyId: string;
  planIdMonthly: string;
  planIdYearly: string | null;
};

const ACTIVE_SUBSCRIPTION_STATUSES = new Set(["active", "authenticated"]);

export function isRazorpayBillingEnabled(): boolean {
  return process.env.APEX_RAZORPAY_ENABLED === "true";
}

export function readRazorpayConfig(): RazorpayConfig | null {
  if (!isRazorpayBillingEnabled()) {
    return null;
  }

  const keyId = process.env.RAZORPAY_KEY_ID?.trim() ?? "";
  const keySecret = process.env.RAZORPAY_KEY_SECRET?.trim() ?? "";
  const webhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET?.trim() ?? "";
  const publicKeyId =
    process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID?.trim() || keyId;
  const planIdMonthly = process.env.RAZORPAY_PLAN_ID_MONTHLY?.trim() ?? "";
  const planIdYearly = process.env.RAZORPAY_PLAN_ID_YEARLY?.trim() ?? "";

  if (!keyId || !keySecret || !webhookSecret || !planIdMonthly || !publicKeyId) {
    return null;
  }

  return {
    enabled: true,
    keyId,
    keySecret,
    webhookSecret,
    publicKeyId,
    planIdMonthly,
    planIdYearly: planIdYearly || null,
  };
}

export function resolvePlanId(
  config: RazorpayConfig,
  interval: BillingInterval,
): string | null {
  if (interval === "monthly") {
    return config.planIdMonthly;
  }

  return config.planIdYearly;
}

export function isPremiumSubscriptionStatus(
  status: string,
  currentPeriodEnd: string | null,
): boolean {
  if (!ACTIVE_SUBSCRIPTION_STATUSES.has(status)) {
    return false;
  }

  if (currentPeriodEnd && new Date(currentPeriodEnd).getTime() < Date.now()) {
    return false;
  }

  return true;
}

export function runRazorpayConfigSelfCheck(): void {
  if (process.env.APEX_RAZORPAY_ENABLED !== "true") {
    return;
  }

  const config = readRazorpayConfig();

  if (!config) {
    throw new Error(
      "Razorpay config self-check failed: APEX_RAZORPAY_ENABLED=true but required env vars missing",
    );
  }

  if (!config.planIdMonthly.startsWith("plan_")) {
    throw new Error("Razorpay config self-check failed: monthly plan id format");
  }

  if (config.planIdYearly && !config.planIdYearly.startsWith("plan_")) {
    throw new Error("Razorpay config self-check failed: yearly plan id format");
  }

  if (!isPremiumSubscriptionStatus("active", null)) {
    throw new Error("Razorpay config self-check failed: active status");
  }

  if (isPremiumSubscriptionStatus("cancelled", null)) {
    throw new Error("Razorpay config self-check failed: cancelled status");
  }
}
