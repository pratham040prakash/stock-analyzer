"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { usePremiumTier } from "@/lib/usePremiumTier";

type TierResponse = {
  status: string;
  tier: "free" | "premium";
};

export default function SettingsPageClient({ userName }: { userName: string }) {
  const { features, activationEnabled } = usePremiumTier(true);
  const [tier, setTier] = useState<"free" | "premium">("free");

  const loadTier = useCallback(async () => {
    const response = await apiFetch("/api/subscription/tier", { cache: "no-store" });
    const data = await parseApiJson<TierResponse>(response, "Tier");

    if (response.ok && data?.tier) {
      setTier(data.tier);
    }
  }, []);

  useEffect(() => {
    void loadTier();
  }, [loadTier]);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Settings</ApexTitle>
          <p className="text-sm text-apex-muted">
            Broker, tier, and export preferences for {userName}.
          </p>
        </div>
      </header>

      <div className="space-y-4">
        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Broker
          </p>
          <p className="text-sm text-apex-text/85">
            Reconnect Zerodha when sessions expire or portfolio looks stale.
          </p>
          <a
            href="/api/zerodha/login"
            className="inline-flex rounded-lg border border-blue-500/25 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100"
          >
            Connect / refresh Zerodha
          </a>
        </section>

        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Subscription
          </p>
          <p className="text-sm text-apex-text/85">
            Current tier · <span className="capitalize">{tier}</span>
          </p>
          <p className="text-xs text-apex-muted/75">
            Margin mode {features.marginMode ? "enabled" : "locked"} · Decision history{" "}
            {features.decisionHistory ? "enabled" : "preview"}
          </p>
          {activationEnabled ? (
            <Link href="/app/you" className="text-sm text-blue-200/90 hover:text-blue-100">
              Activate premium on You →
            </Link>
          ) : null}
        </section>

        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Exports
          </p>
          <p className="text-sm text-apex-text/85">
            Receipt and monthly doctor markdown exports are available from Review and Journal
            receipts.
          </p>
          <Link href="/app/review?tab=receipts" className="text-sm text-blue-200/90 hover:text-blue-100">
            Open receipts →
          </Link>
        </section>

        <Link href="/app/you" className="text-sm text-apex-muted/80 hover:text-apex-text">
          ← Back to You
        </Link>
      </div>
    </ApexShell>
  );
}
