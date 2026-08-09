"use client";

import type { TierFeatures } from "@/services/subscription/tier";

export type PremiumFeature = keyof TierFeatures;

const COPY: Record<
  PremiumFeature,
  { title: string; body: string }
> = {
  marginMode: {
    title: "Margin mode",
    body: "Deploy with cash plus collateral under strict APEX limits. Available on APEX Premium.",
  },
  decisionDepth: {
    title: "Decision depth",
    body: "Full reasoning, watch items, and setup context. Available on APEX Premium.",
  },
  decisionHistory: {
    title: "Decision history",
    body: "Review your last seven days of decisions and discipline. Available on APEX Premium.",
  },
};

type Props = {
  feature: PremiumFeature;
  compact?: boolean;
};

export default function PremiumFeatureGate({
  feature,
  compact = false,
}: Props) {
  const copy = COPY[feature];

  return (
    <div
      className={
        compact
          ? "rounded-lg border border-apex-border/15 bg-white/[0.02] px-3 py-3"
          : "rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4"
      }
    >
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        APEX Premium
      </p>
      <p
        className={
          compact
            ? "mt-1 text-sm font-medium text-apex-text/90"
            : "mt-1 text-base font-medium text-apex-text/90"
        }
      >
        {copy.title}
      </p>
      <p className="mt-2 text-sm leading-snug text-apex-muted/80">{copy.body}</p>
      <p className="mt-2 text-xs text-apex-muted/60">
        Free tier keeps today&apos;s broker truth and one clear action.
      </p>
    </div>
  );
}
