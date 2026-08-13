"use client";

import { useEffect, useMemo, useState } from "react";
import JourneyTargetTrack from "@/components/journey/JourneyTargetTrack";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { buildJourneyProgress } from "@/lib/journey/buildJourneyProgress";
import {
  buildJourneyPriceMap,
  lookupJourneyLiveQuote,
  type JourneyLiveQuote,
} from "@/lib/journey/journeyPriceMap";
import { syncAllActiveJourneys } from "@/lib/journey/journeySync";
import type { StoredInvestmentJourney } from "@/types/investmentJourney";
import type { PortfolioApiResponse } from "@/types/portfolioApi";

export default function YouJourneySection() {
  const [activeJourneys, setActiveJourneys] = useState<StoredInvestmentJourney[]>(
    [],
  );
  const [priceMap, setPriceMap] = useState<Map<string, JourneyLiveQuote>>(
    () => new Map(),
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const [journeys, portfolioResponse] = await Promise.all([
        syncAllActiveJourneys(),
        apiFetch("/api/portfolio", { cache: "no-store" }),
      ]);

      if (cancelled) {
        return;
      }

      const portfolioData = await parseApiJson<PortfolioApiResponse>(
        portfolioResponse,
        "You journey portfolio",
      );

      setActiveJourneys(journeys);
      setPriceMap(
        portfolioData?.holdings?.length
          ? buildJourneyPriceMap(portfolioData.holdings)
          : new Map(),
      );
      setLoading(false);
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  const rows = useMemo(
    () =>
      activeJourneys.map((journey) => {
        const quote = lookupJourneyLiveQuote(priceMap, journey.symbol);
        const progress = buildJourneyProgress({
          journey,
          currentPriceInr: quote?.currentPriceInr ?? null,
          quantity: quote?.quantity ?? 0,
          entryConfirmed: (quote?.quantity ?? 0) > 0,
        });
        const entry = progress.entryPriceInr ?? progress.targetPriceInr * 0.92;
        return { journey, progress, entry };
      }),
    [activeJourneys, priceMap],
  );

  if (loading) {
    return (
      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4">
        <p className="text-sm font-medium text-apex-text/90">Target paths</p>
        <p className="mt-2 text-sm text-apex-muted/70">Loading active paths…</p>
      </section>
    );
  }

  if (activeJourneys.length === 0) {
    return (
      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4">
        <p className="text-sm font-medium text-apex-text/90">Target paths</p>
        <p className="mt-1 text-sm text-apex-muted/80">
          When APEX surfaces a stock on Today, we map entry → target and track progress
          on a bar until you book profits or the thesis breaks.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-apex-border/20 bg-[#0a0d12]/80 px-4 py-4 shadow-inner">
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-apex-muted/70">
        Active paths
      </p>
      <div className="mt-4 space-y-5">
        {rows.map(({ journey, progress, entry }) => (
          <JourneyTargetTrack
            key={journey.id}
            symbol={progress.symbol}
            entryPriceInr={entry}
            targetPriceInr={progress.targetPriceInr}
            currentPriceInr={progress.currentPriceInr}
            progressPct={progress.progressPct}
            targetReached={progress.targetReached}
            thesisBroken={progress.thesisBroken}
            timeTargetLabel={progress.timeTargetLabel}
            timeProgressPct={progress.timeProgressPct}
            timeRemainingLabel={progress.timeRemainingLabel}
            timeOverdue={progress.timeOverdue}
            patienceUntilLabel={progress.patienceUntilLabel}
            compact
          />
        ))}
      </div>
    </section>
  );
}
