"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import JourneyTargetTrack from "@/components/journey/JourneyTargetTrack";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { buildJourneyProgress } from "@/lib/journey/buildJourneyProgress";
import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";
import {
  buildJourneyPriceMap,
  lookupJourneyLiveQuote,
  type JourneyLiveQuote,
} from "@/lib/journey/journeyPriceMap";
import { hydrateJourneyPriceMap } from "@/lib/journey/journeyWatchLtp";
import {
  syncAllActiveJourneys,
  updateJourneyStatusOnServer,
} from "@/lib/journey/journeySync";
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

  const reload = useCallback(async () => {
    const [journeys, portfolioResponse] = await Promise.all([
      syncAllActiveJourneys(),
      apiFetch("/api/portfolio", { cache: "no-store" }),
    ]);

    const portfolioData = await parseApiJson<PortfolioApiResponse>(
      portfolioResponse,
      "You journey portfolio",
    );

    setActiveJourneys(journeys);
    setPriceMap(
      await hydrateJourneyPriceMap(journeys, portfolioData?.holdings ?? []),
    );
  }, []);

  useEffect(() => {
    let cancelled = false;

    void reload().finally(() => {
      if (!cancelled) {
        setLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [reload]);

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

  const handleStatusUpdate = useCallback(
    async (journeyId: string, status: "completed" | "paused") => {
      await updateJourneyStatusOnServer(journeyId, status);
      await reload();
    },
    [reload],
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
      <div className="mt-4 space-y-6">
        {rows.map(({ journey, progress, entry }) => (
          <div key={journey.id} className="space-y-3">
            <JourneyTargetTrack
              symbol={progress.symbol}
              entryPriceInr={entry}
              targetPriceInr={progress.targetPriceInr}
              currentPriceInr={progress.currentPriceInr}
              progressPct={progress.progressPct}
              waitingForEntry={
                progress.milestone === "waiting_entry" || progress.milestone === "planning"
              }
              targetReached={progress.targetReached}
              thesisBroken={progress.thesisBroken}
              timeTargetLabel={progress.timeTargetLabel}
              timeProgressPct={progress.timeProgressPct}
              timeRemainingLabel={progress.timeRemainingLabel}
              timeOverdue={progress.timeOverdue}
              patienceUntilLabel={progress.patienceUntilLabel}
              compact
            />

            {progress.targetReached ? (
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-3">
                <p className="text-sm font-medium text-emerald-100">
                  {JOURNEY_COPY.takeProfitTitle}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-emerald-50/85">
                  {JOURNEY_COPY.takeProfitBody}
                </p>
                <div className="mt-3 flex flex-wrap gap-3">
                  <Link
                    href="/app/portfolio"
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
                  >
                    {JOURNEY_COPY.takeProfitAction}
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      void handleStatusUpdate(journey.id, "completed");
                    }}
                    className="text-sm text-emerald-100/80 underline underline-offset-2 hover:text-white"
                  >
                    {JOURNEY_COPY.completeJourney}
                  </button>
                </div>
              </div>
            ) : (
              <>
                <p className="text-xs leading-snug text-apex-text/85">
                  {progress.guidance}
                </p>
                <button
                  type="button"
                  onClick={() => {
                    void handleStatusUpdate(journey.id, "paused");
                  }}
                  className="text-xs text-apex-muted/70 underline underline-offset-2 hover:text-apex-text"
                >
                  {progress.thesisBroken
                    ? JOURNEY_COPY.pauseJourney
                    : "Pause path"}
                </button>
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
