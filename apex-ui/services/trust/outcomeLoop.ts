import type { OutcomeEvaluationOutput } from "@/services/learning/outcomeEngine";
import type { TrustOutcomeSnapshot } from "@/services/decision/trustOutcome";
import type { PlannedVsActualRow } from "@/types/plannedVsActual";

export type OutcomeLoopView = {
  visible: boolean;
  stock: string | null;
  closed_at: string | null;
  outcome: OutcomeEvaluationOutput["outcome"] | null;
  outcome_label: string | null;
  discipline_score: number | null;
  execution_quality: number | null;
  trust_delta: number | null;
  summary: string | null;
};

export type OverrideDisciplineView = {
  window_days: number;
  override_count: number;
  wait_honored_count: number;
  follow_rate_percent: number | null;
  headline: string;
  detail: string;
};

export const OVERRIDE_WINDOW_DAYS = 14;

function formatOutcomeLabel(outcome: OutcomeEvaluationOutput["outcome"]): string {
  switch (outcome) {
    case "win":
      return "Win";
    case "loss":
      return "Loss";
    case "breakeven":
      return "Breakeven";
  }
}

export function buildOutcomeLoopView(
  trust: TrustOutcomeSnapshot,
): OutcomeLoopView {
  const evaluation = trust.lastOutcome;

  if (!evaluation || !trust.lastClosedAt) {
    return {
      visible: false,
      stock: null,
      closed_at: null,
      outcome: null,
      outcome_label: null,
      discipline_score: null,
      execution_quality: null,
      trust_delta: null,
      summary: null,
    };
  }

  return {
    visible: true,
    stock: trust.stock,
    closed_at: trust.lastClosedAt,
    outcome: evaluation.outcome,
    outcome_label: formatOutcomeLabel(evaluation.outcome),
    discipline_score: evaluation.disciplineScore,
    execution_quality: evaluation.executionQuality,
    trust_delta: trust.trustDelta,
    summary: evaluation.summary,
  };
}

export function buildOverrideDisciplineView(
  rows: PlannedVsActualRow[],
  windowDays = OVERRIDE_WINDOW_DAYS,
): OverrideDisciplineView {
  const plannedRows = rows.filter((row) => row.planned_action !== "none");
  const followed = plannedRows.filter(
    (row) => row.status === "aligned" || row.status === "wait_ok",
  ).length;
  const overrideCount = rows.filter(
    (row) =>
      row.status === "deviated" &&
      (row.planned_action === "wait" || row.planned_action === "hold"),
  ).length;
  const waitHonoredCount = rows.filter((row) => row.status === "wait_ok").length;
  const followRatePercent =
    plannedRows.length > 0
      ? Math.round((followed / plannedRows.length) * 100)
      : null;

  if (plannedRows.length === 0) {
    return {
      window_days: windowDays,
      override_count: 0,
      wait_honored_count: 0,
      follow_rate_percent: null,
      headline: "Plan memory building",
      detail: `No daily plans recorded in the last ${windowDays} days yet — receipts and commits populate this loop.`,
    };
  }

  if (overrideCount === 0) {
    return {
      window_days: windowDays,
      override_count: 0,
      wait_honored_count: waitHonoredCount,
      follow_rate_percent: followRatePercent,
      headline: "No overrides on Wait days",
      detail: `${followRatePercent ?? 0}% plan follow-through (${followed}/${plannedRows.length} days). Trading when Wait was shown: 0.`,
    };
  }

  return {
    window_days: windowDays,
    override_count: overrideCount,
    wait_honored_count: waitHonoredCount,
    follow_rate_percent: followRatePercent,
    headline: `${overrideCount} override${overrideCount === 1 ? "" : "s"} on Wait days`,
    detail: `${followRatePercent ?? 0}% plan follow-through (${followed}/${plannedRows.length} days). Overrides reduce discipline score over time — broker truth is recorded.`,
  };
}

export function runOutcomeLoopSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Outcome loop self-check failed: ${message}`);
    }
  };

  const emptyLoop = buildOutcomeLoopView({
    trustScore: 50,
    trustDelta: 0,
    trustMessage: "test",
    lastOutcome: null,
    lastClosedAt: null,
    stock: null,
  });
  assert(!emptyLoop.visible, "Empty trust must hide loop");

  const populated = buildOutcomeLoopView({
    trustScore: 55,
    trustDelta: 5,
    trustMessage: "test",
    lastOutcome: {
      outcome: "win",
      disciplineScore: 85,
      executionQuality: 80,
      trustDelta: 5,
      summary: "Strong execution.",
    },
    lastClosedAt: "2026-08-11T00:00:00.000Z",
    stock: "RELIANCE",
  });
  assert(populated.visible, "Closed outcome must show loop");
  assert(populated.outcome_label === "Win", "Outcome label must format");

  const noOverrides = buildOverrideDisciplineView([
    {
      date: "2026-08-10",
      symbol: null,
      planned_action: "wait",
      actual_action: null,
      status: "wait_ok",
      status_label: "Wait honored",
      pnl: null,
    },
  ]);
  assert(noOverrides.override_count === 0, "Wait honored is not override");

  const withOverride = buildOverrideDisciplineView([
    {
      date: "2026-08-09",
      symbol: "RELIANCE",
      planned_action: "wait",
      actual_action: "buy",
      status: "deviated",
      status_label: "Deviated",
      pnl: -100,
    },
    {
      date: "2026-08-10",
      symbol: null,
      planned_action: "wait",
      actual_action: null,
      status: "wait_ok",
      status_label: "Wait honored",
      pnl: null,
    },
  ]);
  assert(withOverride.override_count === 1, "Wait-day buy must count as override");
  assert(withOverride.follow_rate_percent === 50, "Follow rate must be 50%");
}
