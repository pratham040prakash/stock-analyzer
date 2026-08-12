"use client";

import Link from "next/link";
import type { ExploreLiveTrigger } from "@/services/explore/liveTriggers";

type Props = {
  triggers: ExploreLiveTrigger[];
  loading?: boolean;
};

export default function ExploreResearchHandoff({ triggers, loading }: Props) {
  if (loading && triggers.length === 0) {
    return <p className="text-sm text-apex-muted/70">Loading explore triggers…</p>;
  }

  if (triggers.length === 0) {
    return (
      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Explore handoff
        </p>
        <p className="mt-2 text-sm text-apex-muted/75">
          Switch to Explore intent on Today to surface live triggers here.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-3">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Explore → Research
      </p>
      <ul className="space-y-2">
        {triggers.map((trigger) => (
          <li
            key={trigger.symbol}
            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-apex-border/10 px-3 py-2"
          >
            <div>
              <p className="text-sm font-medium text-apex-text/90">{trigger.symbol}</p>
              <p className="text-xs text-apex-muted/75">{trigger.label}</p>
            </div>
            <Link
              href={`/app/research?symbol=${encodeURIComponent(trigger.symbol)}`}
              className="text-xs text-blue-200/90 hover:text-blue-100"
            >
              Research →
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
