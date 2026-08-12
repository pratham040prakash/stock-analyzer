"use client";

import { useCallback, useEffect, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import PremiumValueCard from "@/components/subscription/PremiumValueCard";
import PremiumTrialOfferCard from "@/components/subscription/PremiumTrialOfferCard";
import ReflectionCanvas from "@/components/you/ReflectionCanvas";
import YouJourneySection from "@/components/journey/YouJourneySection";
import YouAccountStrip from "@/components/you/YouAccountStrip";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { usePremiumTier } from "@/lib/usePremiumTier";
import type { YouSnapshotViewModel } from "@/types/youSnapshot";

type SnapshotResponse = {
  status: string;
  snapshot: YouSnapshotViewModel;
};

export default function YouPageClient({ userName }: { userName: string }) {
  const {
    tier,
    activationEnabled,
    billingEnabled,
    trial,
    refresh: refreshTier,
  } = usePremiumTier(true);
  const [snapshot, setSnapshot] = useState<YouSnapshotViewModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/api/you/snapshot", { cache: "no-store" });
      const data = await parseApiJson<SnapshotResponse>(response, "You snapshot");

      if (response.ok && data?.snapshot) {
        setSnapshot(data.snapshot);
      } else {
        setError("Could not load your trader snapshot.");
      }
    } catch (loadError) {
      setError(
        loadError instanceof Error ? loadError.message : "Could not load snapshot.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>You</ApexTitle>
          <p className="text-sm text-apex-muted">
            How {userName} is becoming a better investor — not a brokerage dashboard.
          </p>
        </div>
      </header>

      <YouAccountStrip />

      <div className="mb-6">
        <YouJourneySection />
      </div>

      <div className="mb-6">
        <PremiumTrialOfferCard trial={trial} onUpdated={() => void refreshTier()} compact />
      </div>

      {tier === "free" ? (
        <div className="mb-6">
          <PremiumValueCard
            tier={tier}
            activationEnabled={activationEnabled}
            billingEnabled={billingEnabled}
            onSubscribed={() => void refreshTier()}
            compact
          />
        </div>
      ) : null}

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading reflection…</p>
      ) : error ? (
        <p className="text-sm text-amber-200/85">{error}</p>
      ) : snapshot ? (
        <ReflectionCanvas snapshot={snapshot} />
      ) : null}
    </ApexShell>
  );
}
