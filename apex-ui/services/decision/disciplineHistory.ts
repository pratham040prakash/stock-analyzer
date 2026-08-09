import type { DecisionActionType } from "@/types/decision";
import type { DisciplineHistoryEntry } from "@/types/decisionHistory";
import {
  buildLastNIstDays,
  mergeDisciplineHistory,
  resolveSinceIstDate,
  summarizeDisciplineHistory,
  type DisciplineCommitRow,
} from "@/lib/dailyLoop/disciplineHistoryMerge";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type DisciplineHistorySummary = ReturnType<
  typeof summarizeDisciplineHistory
>;

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
  const sinceDate = resolveSinceIstDate(windowDays);
  const dayKeys = buildLastNIstDays(windowDays);

  const [decisionsResult, memoryResult, commitsResult] = await Promise.all([
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
    supabase
      .from("discipline_commits")
      .select("commit_date, intent, action, stock, followed")
      .eq("user_id", userId)
      .gte("commit_date", sinceDate)
      .order("commit_date", { ascending: false }),
  ]);

  if (decisionsResult.error) {
    throw new Error(decisionsResult.error.message);
  }

  if (memoryResult.error) {
    throw new Error(memoryResult.error.message);
  }

  if (commitsResult.error) {
    throw new Error(commitsResult.error.message);
  }

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

  const commitsByDate = new Map<string, DisciplineCommitRow>();

  for (const row of commitsResult.data ?? []) {
    if (!row.commit_date || commitsByDate.has(row.commit_date)) {
      continue;
    }

    commitsByDate.set(row.commit_date, {
      commit_date: row.commit_date,
      intent: row.intent,
      action: row.action,
      stock: row.stock,
      followed: row.followed,
    });
  }

  const history = mergeDisciplineHistory({
    dayKeys,
    executedByDate,
    commitsByDate,
    guidanceByDate,
  });

  return {
    history,
    summary: summarizeDisciplineHistory(history),
    days: dayKeys,
  };
}
