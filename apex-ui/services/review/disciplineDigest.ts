import type { WeeklyReviewSlice } from "@/types/reviewCadence";

export type DisciplineDigestView = {
  headline: string;
  detail: string;
  followed_days: number;
  trackable_days: number;
  wait_days: number;
  process_score: number;
  streak_count: number;
};

export function buildDisciplineDigestView(
  weekly: WeeklyReviewSlice,
): DisciplineDigestView {
  const trackableDays =
    weekly.planned_summary.aligned +
    weekly.planned_summary.deviated +
    weekly.planned_summary.planned_only;
  const followedDays = weekly.planned_summary.aligned;
  const waitDays = weekly.summary.waitDays;
  const processScore = weekly.process_score.score;
  const streakCount = weekly.process_score.streakCount;

  if (trackableDays === 0) {
    return {
      headline: "Discipline memory building",
      detail: `${streakCount}-day streak · process ${processScore}/100 · commit on Today to start the loop.`,
      followed_days: 0,
      trackable_days: 0,
      wait_days: waitDays,
      process_score: processScore,
      streak_count: streakCount,
    };
  }

  const headline = `${followedDays}/${trackableDays} days followed plan`;

  const detail = [
    waitDays > 0 ? `${waitDays} Wait day${waitDays === 1 ? "" : "s"} honored` : null,
    `${processScore}/100 process score`,
    streakCount > 0 ? `${streakCount}-day streak` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return {
    headline,
    detail,
    followed_days: followedDays,
    trackable_days: trackableDays,
    wait_days: waitDays,
    process_score: processScore,
    streak_count: streakCount,
  };
}

export function buildDisciplineDigestLine(weekly: WeeklyReviewSlice): string {
  const view = buildDisciplineDigestView(weekly);
  return `${view.headline}${view.detail ? ` · ${view.detail}` : ""}`;
}

export function runDisciplineDigestSelfCheck(): void {
  const view = buildDisciplineDigestView({
    headline: "Test",
    summary: {
      wins: 1,
      losses: 0,
      open: 0,
      waitDays: 2,
      executedDays: 1,
      followedDays: 3,
    },
    process_score: {
      score: 72,
      streakCount: 4,
      message: "Test",
    },
    planned_summary: {
      aligned: 4,
      deviated: 1,
      planned_only: 0,
      actual_only: 0,
    },
  });

  if (view.headline !== "4/5 days followed plan") {
    throw new Error("Discipline digest self-check failed: headline");
  }

  const line = buildDisciplineDigestLine({
    headline: "Test",
    summary: {
      wins: 0,
      losses: 0,
      open: 0,
      waitDays: 0,
      executedDays: 0,
      followedDays: 0,
    },
    process_score: { score: 50, streakCount: 0, message: "Test" },
    planned_summary: {
      aligned: 0,
      deviated: 0,
      planned_only: 0,
      actual_only: 0,
    },
  });

  if (!line.includes("Discipline memory building")) {
    throw new Error("Discipline digest self-check failed: empty trackable");
  }
}
