import { buildDisciplineProcessScore } from "@/services/review/disciplineScore";
import type { DisciplineHistoryEntry, DisciplineHistorySummary } from "@/types/decisionHistory";

export type DisciplineTrendPoint = {
  label: string;
  score: number;
  window_days: number;
};

function summarizeWindow(entries: DisciplineHistoryEntry[]): DisciplineHistorySummary {
  const summary: DisciplineHistorySummary = {
    wins: 0,
    losses: 0,
    open: 0,
    waitDays: 0,
    executedDays: 0,
    followedDays: 0,
  };

  for (const entry of entries) {
    if (entry.outcome === "win") {
      summary.wins += 1;
    } else if (entry.outcome === "loss") {
      summary.losses += 1;
    } else if (entry.outcome === "open") {
      summary.open += 1;
    }

    if (entry.outcome === "wait") {
      summary.waitDays += 1;
    }

    if (entry.source === "executed") {
      summary.executedDays += 1;
    }

    if (entry.outcome === "followed") {
      summary.followedDays += 1;
    }
  }

  return summary;
}

export function buildDisciplineTrends(
  history: DisciplineHistoryEntry[],
  streakCount = 0,
): DisciplineTrendPoint[] {
  const windows = [
    { label: "Last 14 days", days: 14 },
    { label: "Last 30 days", days: 30 },
    { label: "Last 90 days", days: 90 },
  ];

  return windows.map((window) => {
    const slice = history.slice(0, window.days);
    const summary = summarizeWindow(slice);
    const score = buildDisciplineProcessScore(summary, streakCount);

    return {
      label: window.label,
      score: score.score,
      window_days: window.days,
    };
  });
}

export function runDisciplineTrendsSelfCheck(): void {
  const trends = buildDisciplineTrends(
    [
      {
        date: "2026-08-01",
        action: "wait",
        outcome: "wait",
        outcomeLabel: "Wait",
        source: "guidance",
      },
      {
        date: "2026-08-02",
        action: "hold",
        outcome: "followed",
        outcomeLabel: "Followed",
        source: "commit",
      },
    ],
    2,
  );

  if (trends.length !== 3 || trends[0].score < 0) {
    throw new Error("Discipline trends self-check failed");
  }
}
