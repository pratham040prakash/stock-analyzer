import { readFileSync } from "node:fs";
import { join } from "node:path";
import { chooseFrozenArtifact } from "@/types/decision";
import { projectExecutionTicket } from "@/services/execution/authorization";
import { sanitizeEvidenceContribution } from "@/services/decision/evidenceContribution";
import { mayWriteTodayFrozenArtifact } from "@/services/decision/selfLearning";
import { applyRegimeConditioning } from "@/services/decision/regimeConditioning";

function readUi(rel: string): string {
  return readFileSync(join(process.cwd(), rel), "utf8");
}

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Architecture compliance failed: ${message}`);
  }
}

export function runArchitectureComplianceSelfCheck(): void {
  const todayRoute = readUi("app/api/decision/today/route.ts");
  const brief = readUi("services/brief/assembleMorningBrief.ts");
  const askRoute = readUi("app/api/ask/answer/route.ts");
  const executeRoute = readUi("app/api/trade/execute/route.ts");
  const contractRoute = readUi("app/api/today/contract/route.ts");
  const gttRoute = readUi("app/api/trade/gtt/route.ts");
  const home = readUi("components/HomeDecisionScreen.tsx");
  const panel = readUi("components/dailyLoop/TodayExecutionPanel.tsx");
  const learning = readUi("services/decision/selfLearning.ts");
  const outcomesCron = readUi("app/api/cron/outcomes/route.ts");

  assert(
    todayRoute.includes("getDecision("),
    "Today route must be the production producer",
  );
  assert(
    !brief.includes("getDecision(") &&
      brief.includes("getTodayDailyDecision"),
    "Brief must stay read-only and project the artifact",
  );
  assert(!askRoute.includes("getDecision("), "Ask must not produce a decision");
  assert(
    executeRoute.includes("validateExecutionAgainstArtifact"),
    "Execute must authorize against the artifact",
  );
  assert(
    contractRoute.includes("getTodayDailyDecision") ||
      contractRoute.includes("artifact"),
    "Contract must bind to the artifact",
  );
  assert(
    gttRoute.includes("validateExecutionAgainstArtifact") ||
      gttRoute.includes("getTodayDailyDecision"),
    "GTT must bind to the artifact",
  );
  assert(
    !home.includes("ticketOverride") && !panel.includes("onTicketChange"),
    "Client tickets must not override approved size",
  );
  assert(
    !todayRoute.includes("from \"python") &&
      !executeRoute.includes("alpha_ai") &&
      !todayRoute.includes("analyzer/"),
    "Python must stay outside the production decision/execution graph",
  );
  assert(
    learning.includes(".not(\"exit_price\", \"is\", null)") &&
      !outcomesCron.includes("saveDailyDecision"),
    "Learning must read closed outcomes and not rewrite Today",
  );

  const now = "2026-09-11T09:00:00.000Z";
  const frozen = {
    schema_version: "1" as const,
    decision_id: "2026-09-11:arch",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "grow" as const,
    action: "buy" as const,
    symbol: { status: "known" as const, value: "HDFCBANK", observed_at: now },
    approved_size: { kind: "buy_amount" as const, amount_inr: 4000 },
    daily_verdict: "trade" as const,
    tradingLocked: false,
    entryConfirmed: true,
    capital_state: {
      status: "known" as const,
      value: { available_cash_inr: 1, portfolio_value_inr: 1 },
      observed_at: now,
    },
    broker_state: {
      status: "known" as const,
      value: { broker: "zerodha" as const, connection: "connected" as const },
      observed_at: now,
    },
    market_state: {
      status: "known" as const,
      value: { trend: "sideways" as const, session: "market_open" },
      observed_at: now,
    },
    source_timestamps: {
      portfolio: { status: "known" as const, value: now, observed_at: now },
      capital: { status: "known" as const, value: now, observed_at: now },
      broker: { status: "known" as const, value: now, observed_at: now },
      market: { status: "known" as const, value: now, observed_at: now },
      entry: { status: "known" as const, value: now, observed_at: now },
    },
    evidence_ids: [],
    evidence: [],
    blockers: [],
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision" as const,
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
    },
    frozen_portfolio: { positions: [], total_value_inr: 0, pnl_inr: 0 },
    projection: {
      decision: "BUY_MORE" as const,
      action: "buy" as const,
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
      actions: [],
      stock: "HDFCBANK",
      amount: 4000,
    },
  };

  assert(
    chooseFrozenArtifact(frozen, false) === frozen,
    "Freeze must stay immutable without refresh",
  );
  assert(
    chooseFrozenArtifact(frozen, true) === null,
    "Explicit refresh is the only replacement path",
  );
  assert(
    projectExecutionTicket(frozen) === 4000,
    "Tickets must project approved artifact size",
  );
  assert(
    sanitizeEvidenceContribution({
      id: "x",
      type: "FACT",
      source: "alpha_ai",
      summary: "note",
      action: "buy",
    }) === null,
    "Evidence providers cannot set action",
  );
  assert(
    !mayWriteTodayFrozenArtifact("2026-09-11", "2026-09-11"),
    "Learning cannot mutate today's frozen artifact",
  );
  assert(
    applyRegimeConditioning(2000, "bearish").amount === 1000,
    "Regime may reduce size in the producer only",
  );
}
