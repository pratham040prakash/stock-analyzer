"use client";

import { useMemo } from "react";
import InvestmentJourneyPanel from "@/components/journey/InvestmentJourneyPanel";
import { listActiveJourneys } from "@/lib/journey/journeyStore";

export default function YouJourneySection() {
  const activeJourneys = useMemo(() => listActiveJourneys(), []);

  if (activeJourneys.length === 0) {
    return (
      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4">
        <p className="text-sm font-medium text-apex-text/90">Target paths</p>
        <p className="mt-1 text-sm text-apex-muted/80">
          When APEX surfaces a stock on Today, we map a chart-backed path and stay
          with you until target or thesis break.
        </p>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      {activeJourneys.map((journey) => (
        <InvestmentJourneyPanel key={journey.id} symbol={journey.symbol} />
      ))}
    </div>
  );
}
