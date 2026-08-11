"use client";

import Link from "next/link";
import type { NewCapitalViewModel } from "@/types/newCapital";

type Props = {
  workflow: NewCapitalViewModel | null;
  loading?: boolean;
};

export default function NewCapitalPanel({ workflow, loading }: Props) {
  if (loading) {
    return <p className="text-sm text-apex-muted/70">Loading new capital plan…</p>;
  }

  if (!workflow?.available) {
    return (
      <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          New capital
        </p>
        <p className="mt-2 text-sm text-apex-muted/85">{workflow?.message ?? "Sync broker to plan deployment."}</p>
      </section>
    );
  }

  const plan = workflow.available;

  return (
    <section className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 px-4 py-4 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-emerald-100/70">
        New capital workflow
      </p>
      <p className="text-lg font-medium text-apex-text/95">{plan.headline}</p>
      <p className="text-sm text-apex-muted/85">{plan.guidance}</p>
      {plan.sacred_core_note ? (
        <p className="text-sm text-amber-100/85">{plan.sacred_core_note}</p>
      ) : null}
      {plan.suggested_symbols.length > 0 ? (
        <div className="flex flex-wrap gap-2 pt-1">
          {plan.suggested_symbols.map((symbol) => (
            <Link
              key={symbol}
              href={`/app/research?symbol=${encodeURIComponent(symbol)}`}
              className="rounded-lg border border-blue-500/20 px-3 py-1 text-xs text-blue-100"
            >
              Research {symbol}
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}
