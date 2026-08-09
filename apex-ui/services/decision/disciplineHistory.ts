import type { DecisionActionType } from "@/types/decision";
import type { DisciplineHistoryEntry } from "@/types/decisionHistory";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type DisciplineHistorySummary = {
  wins: number;
  losses: number;
  open: number;
  waitDays: number;
  executedDays: number;
};

function utcDateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function resolveSinceDate(days: number): string {
  const since = new Date();
  since.setUTCDate(since.getUTCDate() - (Math.max(1, days) - 1));
  return utcDateKey(since);
}

function buildLastNDays(days: number): string[] {
  const keys: string[] = [];
  const cursor = new Date();

  for (let index = 0; index < days; index += 1) {
    keys.unshift(utcDateKey(cursor));
    cursor.setUTCDate(cursor.getUTCDate() - 1);
  }

  return keys;
}

function resolveMemoryOutcome(row: {
  action: string;
  exit_price: number | null;
  pnl: number | null;
  success: boolean | null;
}): DisciplineHistoryEntry["outcome"] {
  if (row.action === "buy" && row.exit_price === null) {
    return "open";
  }

  if (row.pnl !== null && Number.isFinite(Number(row.pnl))) {
    return Number(row.pnl) > 0 ? "win" : "loss";
  }

  if (row.success === true) {
    return "win";
  }

  if (row.success === false) {
    return "loss";
  }

  return "none";
}

function memoryActionLabel(action: string): DecisionActionType {
  if (action === "buy" || action === "sell") {
    return action;
  }

  return "hold";
}

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

  if (outcome === "wait") {
    return source === "executed" ? "Wait" : "Wait — no trade";
  }

  if (outcome === "hold") {
    return "Held";
  }

  return "No execution logged";
}

function summarizeHistory(
  history: DisciplineHistoryEntry[],
): DisciplineHistorySummary {
  return history.reduce<DisciplineHistorySummary>(
    (summary, entry) => {
      if (entry.source === "executed") {
        summary.executedDays += 1;
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
    },
  );
}

export async function getDisciplineHistory(
  supabase: Client,
  userId: string,
  days = 7,
): Promise<{
  history: DisciplineHistoryEntry[];
  summary: DisciplineHistorySummary;
  days: string[];
}> {
  const windowDays = Math.min(7, Math.max(1, Math.round(days)));
  const sinceDate = resolveSinceDate(windowDays);
  const dayKeys = buildLastNDays(windowDays);

  const [decisionsResult, memoryResult] = await Promise.all([
    supabase
      .from("decisions")
      .select("decision_date, action, stock")
      .eq("user_id", userId)
      .gte("decision_date", sinceDate)
      .order("decision_date", { ascending: false }),
    supabase
      .from("decision_memory")
      .select(
        "decision_date, stock, action, exit_price, pnl, success, entry_price, quantity",
      )
      .eq("user_id", userId)
      .gte("decision_date", sinceDate)
      .order("decision_date", { ascending: false }),
  ]);

  const guidanceByDate = new Map<string, { action: string; stock?: string }>();

  for (const row of decisionsResult.data ?? []) {
    if (!row.decision_date || guidanceByDate.has(row.decision_date)) {
      continue;
    }

    guidanceByDate.set(row.decision_date, {
      action: row.action ?? "hold",
      stock: row.stock ?? undefined,
    });
  }

  const executedByDate = new Map<string, DisciplineHistoryEntry[]>();

  for (const row of memoryResult.data ?? []) {
    if (!row.decision_date || !row.stock) {
      continue;
    }

    const outcome = resolveMemoryOutcome(row);
    const action = memoryActionLabel(row.action ?? "buy");
    const pnl =
      row.pnl !== null && Number.isFinite(Number(row.pnl))
        ? Math.round(Number(row.pnl))
        : null;

    const entry: DisciplineHistoryEntry = {
      date: row.decision_date,
      action,
      stock: row.stock,
      outcome,
      outcomeLabel: outcomeLabel(outcome, "executed"),
      pnl,
      source: "executed",
    };

    const bucket = executedByDate.get(row.decision_date) ?? [];
    bucket.push(entry);
    executedByDate.set(row.decision_date, bucket);
  }

  const history: DisciplineHistoryEntry[] = [];

  for (const date of [...dayKeys].reverse()) {
    const executed = executedByDate.get(date);

    if (executed?.length) {
      history.push(...executed);
      continue;
    }

    const guidance = guidanceByDate.get(date);

    if (!guidance) {
      continue;
    }

    const action = guidanceAction(guidance.action);
    const outcome =
      action === "wait"
        ? "wait"
        : action === "hold"
          ? "hold"
          : "none";

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

  return {
    history,
    summary: summarizeHistory(history),
    days: dayKeys,
  };
}
