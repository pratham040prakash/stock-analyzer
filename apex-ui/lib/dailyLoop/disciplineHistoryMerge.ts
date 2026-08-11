import type {
  DisciplineHistoryEntry,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";
import type { DecisionActionType } from "@/types/decision";
import { istDateKey, shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";

export type DisciplineCommitRow = {
  commit_date: string;
  intent: string;
  action: string;
  stock: string | null;
  followed: boolean;
};

function guidanceAction(action: string | null): DecisionActionType {
  if (
    action === "buy" ||
    action === "sell" ||
    action === "wait" ||
    action === "hold" ||
    action === "reduce" ||
    action === "explore"
  ) {
    return action;
  }

  return "hold";
}

function outcomeLabel(
  outcome: DisciplineHistoryEntry["outcome"],
  source: DisciplineHistoryEntry["source"],
): string {
  if (outcome === "win") {
    return "Closed win";
  }

  if (outcome === "loss") {
    return "Closed loss";
  }

  if (outcome === "open") {
    return "Open position";
  }

  if (outcome === "followed") {
    return "Followed today";
  }

  if (outcome === "wait") {
    return source === "executed" ? "Wait" : "Wait — no trade";
  }

  if (outcome === "hold") {
    return "Held";
  }

  return "No execution logged";
}

export function buildLastNIstDays(days: number, today = new Date()): string[] {
  const windowDays = Math.min(7, Math.max(1, Math.round(days)));
  const todayKey = istDateKey(today);
  const keys: string[] = [];

  for (let index = windowDays - 1; index >= 0; index -= 1) {
    keys.push(shiftIstDateKey(todayKey, -index));
  }

  return keys;
}

export function resolveSinceIstDate(days: number, today = new Date()): string {
  const windowDays = Math.min(7, Math.max(1, Math.round(days)));
  const todayKey = istDateKey(today);
  return shiftIstDateKey(todayKey, -(windowDays - 1));
}

export function summarizeDisciplineHistory(
  history: DisciplineHistoryEntry[],
): DisciplineHistorySummary {
  return history.reduce<DisciplineHistorySummary>(
    (summary, entry) => {
      if (entry.source === "executed") {
        summary.executedDays += 1;
      }

      if (entry.source === "commit") {
        summary.followedDays += 1;
      }

      if (entry.outcome === "win") {
        summary.wins += 1;
      } else if (entry.outcome === "loss") {
        summary.losses += 1;
      } else if (entry.outcome === "open") {
        summary.open += 1;
      } else if (entry.outcome === "wait" || entry.outcome === "hold") {
        summary.waitDays += 1;
      }

      return summary;
    },
    {
      wins: 0,
      losses: 0,
      open: 0,
      waitDays: 0,
      executedDays: 0,
      followedDays: 0,
    },
  );
}

export function mergeDisciplineHistory(input: {
  dayKeys: string[];
  executedByDate: Map<string, DisciplineHistoryEntry[]>;
  commitsByDate: Map<string, DisciplineCommitRow>;
  guidanceByDate: Map<string, { action: string; stock?: string }>;
}): DisciplineHistoryEntry[] {
  const history: DisciplineHistoryEntry[] = [];

  for (const date of [...input.dayKeys].reverse()) {
    const executed = input.executedByDate.get(date);

    if (executed?.length) {
      const trades = executed.filter(
        (entry) => entry.action === "buy" || entry.action === "sell",
      );

      if (trades.length > 0) {
        history.push(...trades);
        continue;
      }

      // Hold-only memory rows are broker noise — prefer commit/guidance for the day.
    }

    const commit = input.commitsByDate.get(date);

    if (commit?.followed) {
      history.push({
        date,
        action: guidanceAction(commit.action),
        stock: commit.stock ?? undefined,
        outcome: "followed",
        outcomeLabel: outcomeLabel("followed", "commit"),
        pnl: null,
        source: "commit",
      });
      continue;
    }

    const guidance = input.guidanceByDate.get(date);

    if (!guidance) {
      continue;
    }

    const action = guidanceAction(guidance.action);
    const outcome =
      action === "wait" ? "wait" : action === "hold" ? "hold" : "none";

    history.push({
      date,
      action,
      stock: guidance.stock,
      outcome,
      outcomeLabel: outcomeLabel(outcome, "guidance"),
      pnl: null,
      source: "guidance",
    });
  }

  return history;
}

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`disciplineHistoryMerge self-check failed: ${message}`);
  }
}

export function runDisciplineHistoryMergeSelfCheck(): void {
  const dayKeys = buildLastNIstDays(7, new Date("2026-08-09T12:00:00+05:30"));
  const todayKey = istDateKey(new Date("2026-08-09T12:00:00+05:30"));

  assert(dayKeys.length === 7, "Seven IST day keys");
  assert(dayKeys.at(-1) === todayKey, "Last key is today in IST");

  const history = mergeDisciplineHistory({
    dayKeys,
    executedByDate: new Map(),
    commitsByDate: new Map([
      [
        todayKey,
        {
          commit_date: todayKey,
          intent: "grow",
          action: "wait",
          stock: "JIOFIN",
          followed: true,
        },
      ],
    ]),
    guidanceByDate: new Map(),
  });

  assert(history.length === 1, "Commit-only day appears in history");
  assert(history[0]?.outcome === "followed", "Commit maps to followed outcome");
  assert(history[0]?.source === "commit", "Commit source preserved");

  const summary = summarizeDisciplineHistory(history);
  assert(summary.followedDays === 1, "Summary counts followed days");

  const executedWins = mergeDisciplineHistory({
    dayKeys: [todayKey],
    executedByDate: new Map([
      [
        todayKey,
        [
          {
            date: todayKey,
            action: "sell",
            stock: "JIOFIN",
            outcome: "win",
            outcomeLabel: "Closed win",
            pnl: 120,
            source: "executed",
          },
        ],
      ],
    ]),
    commitsByDate: new Map([
      [
        todayKey,
        {
          commit_date: todayKey,
          intent: "grow",
          action: "wait",
          stock: "JIOFIN",
          followed: true,
        },
      ],
    ]),
    guidanceByDate: new Map(),
  });

  assert(
    executedWins.length === 1 && executedWins[0]?.source === "executed",
    "Executed trades outrank discipline commits on the same day",
  );

  const holdNoise = mergeDisciplineHistory({
    dayKeys: [todayKey],
    executedByDate: new Map([
      [
        todayKey,
        [
          {
            date: todayKey,
            action: "hold",
            stock: "RELIANCE",
            outcome: "hold",
            outcomeLabel: "Held",
            pnl: null,
            source: "executed",
          },
          {
            date: todayKey,
            action: "hold",
            stock: "TCS",
            outcome: "hold",
            outcomeLabel: "Held",
            pnl: null,
            source: "executed",
          },
        ],
      ],
    ]),
    commitsByDate: new Map([
      [
        todayKey,
        {
          commit_date: todayKey,
          intent: "grow",
          action: "wait",
          stock: null,
          followed: true,
        },
      ],
    ]),
    guidanceByDate: new Map(),
  });

  assert(
    holdNoise.length === 1 &&
      holdNoise[0]?.source === "commit" &&
      holdNoise[0]?.outcome === "followed",
    "Hold-only memory rows fall through to discipline commit",
  );
}
