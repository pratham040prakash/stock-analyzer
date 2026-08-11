"use client";

import type { QuarterlyReviewViewModel } from "@/types/quarterlyReview";
import Link from "next/link";

type Props = {
  quarterly: QuarterlyReviewViewModel;
  loading?: boolean;
};

export default function QuarterlyReviewPanel({ quarterly, loading }: Props) {
  if (loading) {
    return <p className="text-sm text-apex-muted/70">Loading quarterly review…</p>;
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-purple-500/15 bg-purple-500/5 px-4 py-4 space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Quarterly review · {quarterly.quarter_label}
        </p>
        <p className="text-lg font-medium text-apex-text/95">{quarterly.headline}</p>
        <p className="text-sm text-apex-muted/85">{quarterly.summary}</p>
        <p className="text-xs text-apex-muted/70">
          Discipline {quarterly.discipline_score}/100 · {quarterly.aligned_days} aligned ·{" "}
          {quarterly.deviated_days} deviations
        </p>
        {quarterly.concentration_warning ? (
          <p className="text-sm text-amber-100/85">{quarterly.concentration_warning}</p>
        ) : null}
        <p className="text-sm text-apex-muted/80">{quarterly.goal_framing}</p>
      </section>

      {quarterly.thesis_progress.length > 0 ? (
        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Thesis progress
          </p>
          <ul className="space-y-1 text-sm text-apex-text/85">
            {quarterly.thesis_progress.map((row) => (
              <li key={row.symbol}>
                {row.symbol} · {row.note}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {quarterly.action_items.length > 0 ? (
        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Quarter priorities
          </p>
          <ul className="space-y-1 text-sm text-apex-text/85">
            {quarterly.action_items.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <Link
        href="/app/review?tab=monthly"
        className="inline-flex text-sm text-blue-200/90 hover:text-blue-100"
      >
        Open monthly doctor →
      </Link>
    </div>
  );
}
