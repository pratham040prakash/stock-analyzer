"use client";

import DisciplineHistoryStrip from "@/components/dailyLoop/DisciplineHistoryStrip";
import { formatDisciplineSummary } from "@/lib/dailyLoop/disciplineHistoryMerge";
import { buildLastNIstDays } from "@/lib/dailyLoop/disciplineHistoryMerge";
import { buildWeeklyReviewHeadline } from "@/lib/dailyLoop/weeklyReview";
import type {
  DisciplineHistoryEntry,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";

const EMPTY_SUMMARY: DisciplineHistorySummary = {
  wins: 0,
  losses: 0,
  open: 0,
  waitDays: 0,
  executedDays: 0,
  followedDays: 0,
};

export type WeeklyReviewStripProps = {
  history: DisciplineHistoryEntry[];
  summary?: DisciplineHistorySummary;
  days?: string[];
};

export default function WeeklyReviewStrip({
  history,
  summary = EMPTY_SUMMARY,
  days = [],
}: WeeklyReviewStripProps) {
  const windowDays = days.length > 0 ? days : buildLastNIstDays(7);
  const summaryLine = formatDisciplineSummary(summary);
  const headline = buildWeeklyReviewHeadline(summary);

  return (
    <section
      className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-3"
      aria-label="Seven day review"
    >
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          This week
        </p>
        <p className="text-sm text-apex-text/85">{headline}</p>
        <p className="text-xs text-apex-muted/75">{summaryLine}</p>
      </div>

      <DisciplineHistoryStrip days={windowDays} history={history} />
    </section>
  );
}
