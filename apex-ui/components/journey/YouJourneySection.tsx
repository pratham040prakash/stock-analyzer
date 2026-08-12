"use client";

import { useMemo } from "react";
import JourneyTargetTrack from "@/components/journey/JourneyTargetTrack";
import { buildJourneyProgress } from "@/lib/journey/buildJourneyProgress";
import { listActiveJourneys } from "@/lib/journey/journeyStore";

export default function YouJourneySection() {
  const activeJourneys = useMemo(() => listActiveJourneys(), []);

  const rows = useMemo(
    () =>
      activeJourneys.map((journey) => {
        const progress = buildJourneyProgress({ journey });
        const entry = progress.entryPriceInr ?? progress.targetPriceInr * 0.92;
        return { journey, progress, entry };
      }),
    [activeJourneys],
  );

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
            compact
          />
        ))}
      </div>
    </section>
  );
}
