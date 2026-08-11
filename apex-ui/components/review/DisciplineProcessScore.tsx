"use client";

import type { DisciplineProcessScore as ScoreModel } from "@/services/review/disciplineScore";

type Props = {
  score: ScoreModel;
  compact?: boolean;
};

export default function DisciplineProcessScore({ score, compact }: Props) {
  if (compact) {
    return (
      <p className="text-xs text-apex-muted/75">
        Process discipline · {score.score}/100 · {score.message}
      </p>
    );
  }

  return (
    <section
      aria-label="Process discipline score"
      className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2"
    >
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Process discipline
      </p>
      <p className="text-3xl font-semibold tabular-nums text-apex-text">
        {score.score}
        <span className="text-base font-normal text-apex-muted/70">/100</span>
      </p>
      <p className="text-sm text-apex-text/85">{score.message}</p>
      {score.streakCount > 0 ? (
        <p className="text-xs text-apex-muted/70">
          {score.streakCount}-day follow-through streak
        </p>
      ) : null}
    </section>
  );
}
