import type { DisciplineHistorySummary } from "@/types/decisionHistory";

/** One-line weekly accountability copy from the 7-day discipline summary. */
export function buildWeeklyReviewHeadline(
  summary: DisciplineHistorySummary,
): string {
  const activeDays =
    summary.executedDays + summary.followedDays + summary.waitDays;

  if (activeDays === 0) {
    return "Log discipline daily to build your weekly record.";
  }

  if (summary.losses > 0) {
    return "Review losses — tighten size and honor stops.";
  }

  if (summary.wins > 0 && summary.losses === 0) {
    return "Process is working — protect gains and stay disciplined.";
  }

  if (summary.followedDays >= 3) {
    return "Strong discipline week — keep following the plan.";
  }

  return "Stay consistent — small daily decisions compound.";
}

export function runWeeklyReviewSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Weekly review self-check failed: ${message}`);
    }
  };

  assert(
    buildWeeklyReviewHeadline({
      wins: 0,
      losses: 0,
      open: 0,
      waitDays: 0,
      executedDays: 0,
      followedDays: 0,
    }).includes("Log discipline"),
    "Empty week must prompt discipline logging",
  );

  assert(
    buildWeeklyReviewHeadline({
      wins: 2,
      losses: 0,
      open: 0,
      waitDays: 1,
      executedDays: 2,
      followedDays: 3,
    }).includes("Process is working"),
    "Winning week must reinforce process",
  );

  assert(
    buildWeeklyReviewHeadline({
      wins: 0,
      losses: 1,
      open: 0,
      waitDays: 0,
      executedDays: 1,
      followedDays: 1,
    }).includes("Review losses"),
    "Loss week must prompt review",
  );
}
