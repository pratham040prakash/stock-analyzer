"use client";

import Link from "next/link";
import PremiumCheckoutPanel from "@/components/subscription/PremiumCheckoutPanel";
import {
  PREMIUM_FEATURE_COPY,
  PREMIUM_VALUE_DETAIL,
  PREMIUM_VALUE_HEADLINE,
  type PremiumFeatureKey,
} from "@/lib/subscription/premiumCopy";
import type { ApexTier } from "@/services/subscription/tier";

const FEATURE_ORDER: PremiumFeatureKey[] = [
  "decisionDepth",
  "decisionHistory",
  "reviewDigest",
  "thesisExport",
  "marginMode",
  "trustCdqsHistory",
];

type Props = {
  tier: ApexTier;
  activationEnabled?: boolean;
  billingEnabled?: boolean;
  onSubscribed?: () => void;
  compact?: boolean;
};

export default function PremiumValueCard({
  tier,
  activationEnabled = false,
  billingEnabled = false,
  onSubscribed,
  compact = false,
}: Props) {
  if (tier === "premium") {
    return null;
  }

  return (
    <section
      className={
        compact
          ? "rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-4 space-y-3"
          : "rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-5 space-y-4"
      }
      aria-labelledby="premium-value-heading"
    >
      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-blue-100/80">
          APEX Premium
        </p>
        <h2 id="premium-value-heading" className="text-lg font-semibold text-apex-text">
          {PREMIUM_VALUE_HEADLINE}
        </h2>
        <p className="text-sm text-apex-muted/85">{PREMIUM_VALUE_DETAIL}</p>
      </div>

      <ul className="space-y-3">
        {FEATURE_ORDER.map((key) => {
          const copy = PREMIUM_FEATURE_COPY[key];

          return (
            <li key={key} className="rounded-lg border border-apex-border/15 bg-white/[0.02] px-3 py-3">
              <p className="text-sm font-medium text-apex-text/90">{copy.title}</p>
              <p className="mt-1 text-xs text-apex-muted/80">{copy.roi}</p>
            </li>
          );
        })}
      </ul>

      {billingEnabled ? (
        <PremiumCheckoutPanel compact={compact} onSubscribed={onSubscribed} />
      ) : activationEnabled ? (
        <Link
          href="/app/you/settings"
          className="inline-flex rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100"
        >
          Unlock with invite code →
        </Link>
      ) : (
        <p className="text-xs text-apex-muted/70">
          Premium invites roll out in batches — check back soon.
        </p>
      )}
    </section>
  );
}
