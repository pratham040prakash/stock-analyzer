"use client";

import Link from "next/link";
import type { MorningBriefViewModel } from "@/types/morningBrief";

type Props = {
  discipline: MorningBriefViewModel["discipline"];
};

export default function TodayDisciplineChip({ discipline }: Props) {
  return (
    <section
      aria-label="Process discipline"
      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3"
    >
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Process discipline
        </p>
        <p className="text-sm text-apex-text/90">
          {discipline.process_score}/100 · {discipline.streak_message}
        </p>
      </div>
      <Link
        href="/app/review"
        className="text-xs text-blue-200/90 transition-colors hover:text-blue-100"
      >
        Weekly review →
      </Link>
    </section>
  );
}
