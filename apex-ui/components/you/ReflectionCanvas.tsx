"use client";

import Link from "next/link";
import type { YouSnapshotViewModel } from "@/types/youSnapshot";

type Props = {
  snapshot: YouSnapshotViewModel;
};

export default function ReflectionCanvas({ snapshot }: Props) {
  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          I&apos;ve noticed
        </p>
        <p className="text-5xl font-semibold text-apex-text">{snapshot.trader_state}</p>
        <p className="text-lg text-apex-text/90">{snapshot.trader_narrative}</p>
      </section>

      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
        <p className="text-sm text-apex-text/85">{snapshot.coaching_insight}</p>
        <p className="text-sm text-apex-muted/80">{snapshot.forward_line}</p>
      </section>

      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Process
        </p>
        <p className="text-sm text-apex-text/90">
          Discipline {snapshot.process_score}/100 · Streak {snapshot.streak_count} days
        </p>
        <p className="text-xs text-apex-muted/75">{snapshot.this_week_summary}</p>
      </section>

      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Investor DNA
        </p>
        <p className="text-sm font-medium text-apex-text/90">
          {snapshot.investor_dna.behavior_tag}
        </p>
        <p className="text-sm text-apex-muted/85">{snapshot.investor_dna.summary}</p>
        <p className="text-xs text-apex-muted/70">{snapshot.investor_dna.insight}</p>
      </section>

      <div className="flex flex-wrap gap-4 text-sm">
        <Link
          href="/app/trust"
          className="text-apex-muted/80 transition-colors hover:text-apex-text"
        >
          How we&apos;re doing →
        </Link>
        <Link
          href="/app/review"
          className="text-apex-muted/80 transition-colors hover:text-apex-text"
        >
          Review & receipts →
        </Link>
        <Link
          href="/app/you/settings"
          className="text-apex-muted/80 transition-colors hover:text-apex-text"
        >
          Settings →
        </Link>
      </div>
    </div>
  );
}
