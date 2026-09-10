"use client";

import type { StarterBookHoldLines } from "@/lib/dailyLoop/firstBuyToday";

type Props = {
  lines: StarterBookHoldLines;
};

export default function TodayStarterHoldCard({ lines }: Props) {
  return (
    <section className="space-y-2 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 py-3">
      <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-apex-muted/70">
        This position
      </p>
      <p className="text-sm font-medium text-apex-text">{lines.position}</p>
      <p className="text-sm text-apex-text/85">{lines.marks}</p>
      {lines.plan ? (
        <p className="text-sm text-apex-text/85">{lines.plan}</p>
      ) : null}
      {lines.next ? (
        <p className="text-sm text-apex-muted/80">{lines.next}</p>
      ) : null}
    </section>
  );
}
