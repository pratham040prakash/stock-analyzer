"use client";

import type { TodayWaitInsight } from "@/lib/dailyLoop/todayWaitInsight";

type Props = {
  insight: TodayWaitInsight;
};

export default function TodayWaitInsightCard({ insight }: Props) {
  return (
    <section className="rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-4">
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-blue-200/80">
        {insight.title}
      </p>
      {insight.symbol ? (
        <p className="mt-1 text-lg font-semibold tracking-tight text-apex-text">
          {insight.symbol}
        </p>
      ) : null}
      <div className="mt-3 space-y-2 text-sm leading-snug">
        <p>
          <span className="font-medium text-apex-text/90">Blocking: </span>
          <span className="text-apex-text/80">{insight.blocker}</span>
        </p>
        <p>
          <span className="font-medium text-emerald-200/90">Unlocks trade: </span>
          <span className="text-apex-text/80">{insight.unlock}</span>
        </p>
        {insight.footnote ? (
          <p className="text-xs text-apex-muted/75">{insight.footnote}</p>
        ) : null}
      </div>
    </section>
  );
}
