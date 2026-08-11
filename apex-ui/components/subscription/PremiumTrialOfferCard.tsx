"use client";

import { useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { PremiumTrialView } from "@/services/subscription/conversionFunnel";

type Props = {
  trial: PremiumTrialView;
  compact?: boolean;
  onUpdated?: () => void;
};

type TrialActionResponse = {
  status: string;
  message?: string;
  trial?: PremiumTrialView;
};

export default function PremiumTrialOfferCard({
  trial,
  compact = false,
  onUpdated,
}: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!trial.enabled || trial.status === "none") {
    return null;
  }

  if (trial.status === "active") {
    return (
      <section
        className={
          compact
            ? "rounded-xl border border-emerald-500/20 bg-emerald-500/[0.06] px-4 py-4 space-y-2"
            : "rounded-xl border border-emerald-500/20 bg-emerald-500/[0.06] px-4 py-5 space-y-2"
        }
      >
        <p className="text-xs font-medium uppercase tracking-wide text-emerald-100/80">
          Premium trial active
        </p>
        <p className="text-sm text-apex-text/90">
          {trial.daysRemaining ?? trial.days} day
          {(trial.daysRemaining ?? trial.days) === 1 ? "" : "s"} left on your trial.
        </p>
      </section>
    );
  }

  if (trial.status !== "offer") {
    return null;
  }

  const runAction = async (action: "claim" | "dismiss") => {
    if (submitting) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await apiFetch("/api/subscription/trial", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const data = await parseApiJson<TrialActionResponse>(response, "Premium trial");

      if (!response.ok || data?.status !== "ok") {
        setError(
          typeof data?.message === "string"
            ? data.message
            : "Could not update trial offer.",
        );
        return;
      }

      onUpdated?.();
    } catch {
      setError("Could not update trial offer right now.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section
      className={
        compact
          ? "rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-4 space-y-3"
          : "rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-5 space-y-4"
      }
      aria-labelledby="premium-trial-heading"
    >
      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-blue-100/80">
          Premium trial
        </p>
        <h2 id="premium-trial-heading" className="text-lg font-semibold text-apex-text">
          {trial.headline}
        </h2>
        <p className="text-sm text-apex-muted/85">{trial.body}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={submitting}
          onClick={() => void runAction("claim")}
          className="rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100 disabled:opacity-50"
        >
          {submitting ? "Starting…" : `Start ${trial.days}-day trial`}
        </button>
        <button
          type="button"
          disabled={submitting}
          onClick={() => void runAction("dismiss")}
          className="rounded-lg border border-apex-border/25 px-4 py-2 text-sm text-apex-muted"
        >
          Not now
        </button>
      </div>

      {error ? <p className="text-xs text-amber-200/90">{error}</p> : null}
    </section>
  );
}
