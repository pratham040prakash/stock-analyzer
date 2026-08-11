"use client";

import DisciplineProcessScore from "@/components/review/DisciplineProcessScore";
import { buildWeeklyReviewHeadline } from "@/lib/dailyLoop/weeklyReview";
import type { DisciplineProcessScore as ScoreModel } from "@/services/review/disciplineScore";
import type { DisciplineHistorySummary } from "@/types/decisionHistory";

type Props = {
  userName: string;
  summary: DisciplineHistorySummary;
  processScore: ScoreModel;
  reconcileMessage?: string | null;
};

export default function WeeklyReviewHero({
  userName,
  summary,
  processScore,
  reconcileMessage,
}: Props) {
  const headline = buildWeeklyReviewHeadline(summary);

  return (
    <header className="mb-6 space-y-4">
      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          I&apos;ve noticed
        </p>
        <h1 className="text-2xl font-semibold text-apex-text">Weekly review</h1>
        <p className="text-sm text-apex-muted">
          Discipline, receipts, and broker truth for {userName}.
        </p>
      </div>

      <section className="rounded-xl border border-blue-500/15 bg-blue-500/5 px-4 py-4 space-y-2">
        <p className="text-lg font-medium text-apex-text/95">{headline}</p>
        <p className="text-sm text-apex-muted/85">
          Wins {summary.wins} · Losses {summary.losses} · Followed{" "}
          {summary.followedDays} · Wait {summary.waitDays}
        </p>
        {reconcileMessage ? (
          <p className="text-xs text-emerald-200/80">{reconcileMessage}</p>
        ) : null}
      </section>

      <DisciplineProcessScore score={processScore} />
    </header>
  );
}
