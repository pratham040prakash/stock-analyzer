"use client";

import type { PortfolioHealthSummaryViewModel } from "@/services/portfolio/buildPortfolioHealthSummary";

type Props = {
  summary: PortfolioHealthSummaryViewModel;
};

export default function PortfolioHealthSummary({ summary }: Props) {
  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Portfolio health
      </p>
      <p className="text-sm font-medium text-apex-text/90">{summary.headline}</p>
      <p className="text-xs text-apex-muted/80">{summary.detail}</p>
      <p className="text-xs text-apex-muted/70">
        Strong {summary.strong} · Watch {summary.watch} · Risk {summary.risk}
      </p>
    </section>
  );
}
