import type { DisciplineHistorySummary } from "@/types/decisionHistory";

export type DisciplineProcessScore = {
  score: number;
  streakCount: number;
  message: string;
};

export function buildDisciplineProcessScore(
  summary: DisciplineHistorySummary,
  streakCount = 0,
): DisciplineProcessScore {
  const windowDays = Math.max(
    1,
    summary.followedDays +
      summary.waitDays +
      summary.executedDays +
      summary.open,
  );

  const followedRate = summary.followedDays / windowDays;
  const waitDiscipline = summary.waitDays / windowDays;
  const raw =
    followedRate * 55 + waitDiscipline * 25 + Math.min(streakCount, 7) * 3;
  const score = Math.max(0, Math.min(100, Math.round(raw)));

  let message = "Process discipline is steady.";
  if (score >= 75) {
    message = "Strong process discipline this week.";
  } else if (score < 45) {
    message = "Focus on following today's plan before chasing outcomes.";
  }

  return {
    score,
    streakCount,
    message,
  };
}

export function runDisciplineScoreSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Discipline score self-check failed: ${message}`);
    }
  };

  const score = buildDisciplineProcessScore(
    {
      wins: 1,
      losses: 0,
      open: 0,
      waitDays: 3,
      executedDays: 2,
      followedDays: 4,
    },
    3,
  );

  assert(score.score >= 35, "Followed days must lift process score");
  assert(score.message.length > 0, "Message required");
}
