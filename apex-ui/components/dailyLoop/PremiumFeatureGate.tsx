"use client";

import {
  PREMIUM_FEATURE_COPY,
  type PremiumFeatureKey,
} from "@/lib/subscription/premiumCopy";
import PremiumActivationPanel from "@/components/dailyLoop/PremiumActivationPanel";

export type PremiumFeature = PremiumFeatureKey;

type Props = {
  feature: PremiumFeature;
  compact?: boolean;
  activationEnabled?: boolean;
  onActivated?: () => void;
};

export default function PremiumFeatureGate({
  feature,
  compact = false,
  activationEnabled = false,
  onActivated,
}: Props) {
  const copy = PREMIUM_FEATURE_COPY[feature];

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
      <p className="mt-2 text-xs font-medium text-blue-100/80">{copy.roi}</p>
      <p className="mt-2 text-xs text-apex-muted/60">
        Free tier keeps today&apos;s broker truth and one clear action.
      </p>

      {activationEnabled ? (
        <PremiumActivationPanel compact={compact} onActivated={onActivated} />
      ) : (
        <p className="mt-3 text-xs text-apex-muted/60">
          Premium invites roll out in batches — check back soon.
        </p>
      )}
    </div>
  );
}
