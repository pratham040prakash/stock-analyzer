import { istDateKey, shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";
import type { Database } from "@/types/database";
import type {
  PlannedVsActualRow,
  PlannedVsActualStatus,
  PlannedVsActualSummary,
} from "@/types/plannedVsActual";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

function buildWindowDays(days: number, today = new Date()): string[] {
  const windowDays = Math.min(14, Math.max(1, Math.round(days)));
  const todayKey = istDateKey(today);
  const keys: string[] = [];

  for (let index = windowDays - 1; index >= 0; index -= 1) {
    keys.push(shiftIstDateKey(todayKey, -index));
  }

  return keys;
}

function normalizeAction(action: string | null | undefined): string {
  return (action ?? "hold").trim().toLowerCase();
}

function statusLabel(status: PlannedVsActualStatus): string {
  switch (status) {
    case "aligned":
      return "Aligned";
    case "deviated":
      return "Deviated";
    case "planned_only":
      return "No broker fill";
    case "actual_only":
      return "Unplanned fill";
    case "wait_ok":
      return "Wait honored";
    default:
      return "Unknown";
  }
}

function resolveStatus(
  planned: string,
  actual: string | null,
): PlannedVsActualStatus {
  if (!actual) {
    if (planned === "wait" || planned === "hold") {
      return "wait_ok";
    }

    return "planned_only";
  }

  if (!planned || planned === "none") {
    return "actual_only";
  }

  if (planned === "wait" || planned === "hold") {
    return actual === "wait" || actual === "hold" ? "wait_ok" : "deviated";
  }

  if (planned === actual) {
    return "aligned";
  }

  if (
    (planned === "buy" && actual === "buy") ||
    (planned === "sell" && actual === "sell")
  ) {
    return "aligned";
  }

  return "deviated";
}

export async function buildPlannedVsActualRows(
  supabase: Client,
  userId: string,
  days = 14,
): Promise<{ rows: PlannedVsActualRow[]; summary: PlannedVsActualSummary }> {
  const dayKeys = buildWindowDays(days);
  const sinceDate = dayKeys[0] ?? istDateKey();

  const [decisionsResult, memoryResult] = await Promise.all([
    supabase
      .from("decisions")
      .select("decision_date, action, stock")
      .eq("user_id", userId)
      .gte("decision_date", sinceDate),
    supabase
      .from("decision_memory")
      .select("decision_date, stock, action, pnl")
      .eq("user_id", userId)
      .gte("decision_date", sinceDate),
  ]);

  if (decisionsResult.error) {
    throw new Error(decisionsResult.error.message);
  }

  if (memoryResult.error) {
    throw new Error(memoryResult.error.message);
  }

  const plannedByDate = new Map<string, { action: string; stock: string | null }>();

  for (const row of decisionsResult.data ?? []) {
    if (!row.decision_date || plannedByDate.has(row.decision_date)) {
      continue;
    }

    plannedByDate.set(row.decision_date, {
      action: normalizeAction(row.action),
      stock: row.stock ?? null,
    });
  }

  const actualByDate = new Map<
    string,
    { action: string; stock: string | null; pnl: number | null }
  >();

  for (const row of memoryResult.data ?? []) {
    if (!row.decision_date) {
      continue;
    }

    const existing = actualByDate.get(row.decision_date);
    const action = normalizeAction(row.action);
    const pnl =
      row.pnl !== null && Number.isFinite(Number(row.pnl))
        ? Math.round(Number(row.pnl))
        : null;

    if (!existing) {
      actualByDate.set(row.decision_date, {
        action,
        stock: row.stock ?? null,
        pnl,
      });
      continue;
    }

    if (pnl !== null) {
      actualByDate.set(row.decision_date, {
        action,
        stock: row.stock ?? existing.stock,
        pnl: (existing.pnl ?? 0) + pnl,
      });
    }
  }

  const rows: PlannedVsActualRow[] = [];

  for (const date of [...dayKeys].reverse()) {
    const planned = plannedByDate.get(date);
    const actual = actualByDate.get(date);
    const plannedAction = planned?.action ?? "none";
    const actualAction = actual?.action ?? null;
    const status = resolveStatus(plannedAction, actualAction);

    rows.push({
      date,
      symbol: actual?.stock ?? planned?.stock ?? null,
      planned_action: plannedAction,
      actual_action: actualAction,
      status,
      status_label: statusLabel(status),
      pnl: actual?.pnl ?? null,
    });
  }

  const summary: PlannedVsActualSummary = {
    aligned: rows.filter((row) => row.status === "aligned" || row.status === "wait_ok")
      .length,
    deviated: rows.filter((row) => row.status === "deviated").length,
    planned_only: rows.filter((row) => row.status === "planned_only").length,
    actual_only: rows.filter((row) => row.status === "actual_only").length,
  };

  return { rows, summary };
}

export function runPlannedVsActualSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Planned vs actual self-check failed: ${message}`);
    }
  };

  assert(
    resolveStatus("wait", null) === "wait_ok",
    "Wait with no fill should be wait_ok",
  );
  assert(
    resolveStatus("buy", "buy") === "aligned",
    "Matching buy should align",
  );
  assert(
    resolveStatus("wait", "buy") === "deviated",
    "Buy on wait day should deviate",
  );
}
