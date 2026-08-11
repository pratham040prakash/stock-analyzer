"use client";

import { useCallback, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => {
      open: () => void;
      on: (event: string, handler: (response: unknown) => void) => void;
    };
  }
}

type CheckoutResponse = {
  status: string;
  message?: string;
  alreadyPremium?: boolean;
  subscriptionId?: string;
  keyId?: string;
  shortUrl?: string | null;
  interval?: "monthly" | "yearly";
};

type Props = {
  compact?: boolean;
  yearlyAvailable?: boolean;
  onSubscribed?: () => void;
};

function loadRazorpayScript(): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Checkout unavailable"));
  }

  if (window.Razorpay) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-razorpay-checkout="true"]');

    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Could not load checkout")), {
        once: true,
      });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.dataset.razorpayCheckout = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Could not load checkout"));
    document.body.appendChild(script);
  });
}

export default function PremiumCheckoutPanel({
  compact = false,
  yearlyAvailable = false,
  onSubscribed,
}: Props) {
  const [billingInterval, setBillingInterval] = useState<"monthly" | "yearly">("monthly");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const syncSubscription = useCallback(
    async (subscriptionId: string) => {
      const response = await apiFetch("/api/subscription/billing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subscriptionId }),
      });
      const data = await parseApiJson<{ status: string; message?: string; tier?: string }>(
        response,
        "Subscription sync",
      );

      if (!response.ok || data?.status !== "ok") {
        throw new Error(
          typeof data?.message === "string" ? data.message : "Could not confirm subscription",
        );
      }

      setSuccess(
        data.tier === "premium"
          ? "APEX Premium is active. Your discipline tools are unlocked."
          : "Payment received — finishing setup…",
      );
      onSubscribed?.();
    },
    [onSubscribed],
  );

  const startCheckout = async () => {
    if (submitting) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiFetch("/api/subscription/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval: billingInterval }),
      });
      const data = await parseApiJson<CheckoutResponse>(response, "Subscription checkout");

      if (!response.ok || data?.status !== "ok") {
        setError(
          typeof data?.message === "string"
            ? data.message
            : "Could not start checkout right now.",
        );
        return;
      }

      if (data.alreadyPremium) {
        setSuccess(data.message ?? "APEX Premium is already active.");
        onSubscribed?.();
        return;
      }

      if (!data.subscriptionId || !data.keyId) {
        setError("Checkout session was incomplete. Try again.");
        return;
      }

      if (data.shortUrl) {
        window.open(data.shortUrl, "_blank", "noopener,noreferrer");
        setSuccess("Complete payment in the Razorpay window, then return here.");
        return;
      }

      await loadRazorpayScript();

      if (!window.Razorpay) {
        setError("Checkout could not load. Try again.");
        return;
      }

      const checkout = new window.Razorpay({
        key: data.keyId,
        subscription_id: data.subscriptionId,
        name: "APEX Premium",
        description: "Discipline infrastructure — not tips.",
        theme: { color: "#2563eb" },
        handler: () => {
          void syncSubscription(data.subscriptionId!).catch((syncError) => {
            setError(
              syncError instanceof Error
                ? syncError.message
                : "Payment succeeded but sync failed. Contact support.",
            );
          });
        },
      });

      checkout.open();
    } catch {
      setError("Could not start checkout right now.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className={
        compact
          ? "mt-3 space-y-3 border-t border-apex-border/10 pt-3"
          : "mt-4 space-y-4 border-t border-apex-border/10 pt-4"
      }
    >
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Subscribe with Razorpay
        </p>
        <p className="mt-1 text-xs leading-snug text-apex-muted/70">
          Pay for discipline infrastructure — exports, digests, depth, and trust history.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setBillingInterval("monthly")}
          className={
            billingInterval === "monthly"
              ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-100"
              : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
          }
        >
          Monthly
        </button>
        {yearlyAvailable ? (
          <button
            type="button"
            onClick={() => setBillingInterval("yearly")}
            className={
              billingInterval === "yearly"
                ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-100"
                : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
            }
          >
            Yearly
          </button>
        ) : null}
      </div>

      <button
        type="button"
        disabled={submitting}
        onClick={() => void startCheckout()}
        className="rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100 disabled:opacity-50"
      >
        {submitting ? "Starting checkout…" : "Subscribe to Premium"}
      </button>

      {error ? <p className="text-xs text-amber-200/90">{error}</p> : null}
      {success ? <p className="text-xs text-emerald-300/90">{success}</p> : null}
    </div>
  );
}
