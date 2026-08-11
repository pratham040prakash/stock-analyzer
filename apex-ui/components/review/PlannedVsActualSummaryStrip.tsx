"use client";

import type { PlannedVsActualSummary } from "@/types/plannedVsActual";

type Props = {
  summary: PlannedVsActualSummary | null;
  rowCount: number;
  className?: string;
};

export default function PlannedVsActualSummaryStrip({
  summary,
  rowCount,
  className = "",
}: Props) {
  if (!summary || rowCount === 0) {
    return (
      <section
        className={`rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 ${className}`.trim()}
        aria-label="Plan follow-through"
      >
        <p className="text-sm font-medium text-apex-text/90">Plan follow-through</p>
        <p className="mt-1 text-sm text-apex-muted/75">
          No planned vs actual rows yet — commit on Today and connect broker fills.
        </p>
      </section>
    );
  }

  const total =
    summary.aligned +
    summary.deviated +
    summary.planned_only +
    summary.actual_only;
  const followRate =
    total > 0 ? Math.round((summary.aligned / total) * 100) : 0;
  const tone =
    summary.deviated > summary.aligned
      ? "border-amber-500/20 bg-amber-500/5"
      : "border-emerald-500/20 bg-emerald-500/5";

  return (
    <section
      className={`rounded-xl border px-4 py-4 ${tone} ${className}`.trim()}
      aria-label="Plan follow-through"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-apex-text/90">Plan follow-through</p>
          <p className="mt-1 text-sm text-apex-muted/80">
            {followRate}% aligned over the last {rowCount} logged days.
          </p>
        </div>
        <p className="text-2xl font-semibold tabular-nums text-apex-text">
          {summary.aligned}/{total}
        </p>
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-apex-muted/80">
        <span className="text-emerald-200/90">Aligned {summary.aligned}</span>
        <span className="text-amber-200/90">Deviated {summary.deviated}</span>
        <span>Planned only {summary.planned_only}</span>
        <span>Actual only {summary.actual_only}</span>
      </div>
    </section>
  );
}
