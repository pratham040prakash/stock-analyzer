"use client";

import type { DisciplineTrendPoint } from "@/services/review/buildDisciplineTrends";

type Props = {
  trends: DisciplineTrendPoint[];
};

export default function DisciplineTrendPanel({ trends }: Props) {
  if (trends.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Process score trend
      </p>
      <ul className="grid gap-2 sm:grid-cols-3">
        {trends.map((point) => (
          <li
            key={point.label}
            className="rounded-lg border border-apex-border/10 px-3 py-2"
          >
            <p className="text-xs text-apex-muted/75">{point.label}</p>
            <p className="text-lg font-semibold text-apex-text/95">{point.score}/100</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
