"use client";

import Link from "next/link";
import { usePremiumTier } from "@/lib/usePremiumTier";

export default function YouAccountStrip() {
  const { tier, billingEnabled, activationEnabled } = usePremiumTier(true);

  return (
    <section
      className="mb-6 rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4"
      aria-labelledby="you-account-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <p
            id="you-account-heading"
            className="text-xs font-medium uppercase tracking-wide text-apex-muted"
          >
            Account & settings
          </p>
          <p className="text-sm text-apex-text/85">
            Broker connection, subscription, exports, and notifications.
          </p>
          <p className="text-xs text-apex-muted/75">
            Tier · <span className="capitalize">{tier}</span>
            {billingEnabled ? " · Razorpay checkout available" : null}
            {!billingEnabled && activationEnabled ? " · Invite codes open" : null}
          </p>
        </div>
        <Link
          href="/app/you/settings"
          className="inline-flex min-h-[44px] items-center rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100"
        >
          Open settings
        </Link>
      </div>
    </section>
  );
}
