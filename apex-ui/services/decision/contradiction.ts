import type { DailyDecisionArtifact } from "@/types/decision";
import { projectArtifactDecision } from "@/types/decision";
import { enforceAskArtifactAlignment } from "@/services/ask/assembleAskAnswer";
import { insightGuidance } from "@/lib/dailyInsight";
import { isCapitalDeploymentBlocked } from "@/services/capital/newCapitalWorkflow";
import { validateExecutionAgainstArtifact } from "@/services/execution/authorization";

/**
 * Shared Wave 3 contradiction assertion.
 *
 * Surfaces may format copy, but none may invent a Buy/Sell that the
 * frozen artifact does not authorise. Used by self-checks only — this
 * is not a second decision engine.
 */
export function assertSurfacesAgreeWithArtifact(
  artifact: DailyDecisionArtifact,
): void {
  const projection = projectArtifactDecision(artifact);
  const locked =
    artifact.tradingLocked || artifact.daily_verdict !== "trade";

  if (locked) {
    if (projection.action !== "wait" || projection.decision !== "WAIT") {
      throw new Error(
        "Contradiction: locked artifact must project WAIT",
      );
    }
    if (projection.amount !== undefined || projection.stock !== undefined) {
      throw new Error(
        "Contradiction: locked artifact must not expose size or symbol",
      );
    }
  }

  const askBuy = enforceAskArtifactAlignment({
    answerWord: "Buy",
    symbol:
      artifact.symbol.status === "known" ? artifact.symbol.value : "INFY",
    artifact,
  });
  const insight = insightGuidance("bullish", 0, undefined, {
    daily_verdict: artifact.daily_verdict,
    tradingLocked: artifact.tradingLocked,
    blockers: artifact.blockers,
  });
  const capital = isCapitalDeploymentBlocked(artifact);
  const execute = validateExecutionAgainstArtifact(
    artifact,
    {
      side: "buy",
      symbol: artifact.symbol.status === "known" ? artifact.symbol.value : "INFY",
      amount:
        artifact.approved_size.kind === "buy_amount"
          ? artifact.approved_size.amount_inr
          : 1,
    },
    artifact.frozen_at,
  );

  if (locked) {
    if (askBuy.answerWord !== "Wait") {
      throw new Error("Contradiction: Ask Buy must wait on a locked artifact");
    }
    if (!insight.startsWith("Today is Wait")) {
      throw new Error("Contradiction: Insight must wait on a locked artifact");
    }
    if (!capital.blocked) {
      throw new Error("Contradiction: new capital must wait on a locked artifact");
    }
    if (execute.ok) {
      throw new Error("Contradiction: execute must refuse a locked artifact");
    }
    return;
  }

  if (artifact.action === "buy" && artifact.symbol.status === "known") {
    if (askBuy.answerWord !== "Buy") {
      throw new Error("Contradiction: Ask Buy must pass for the authorised symbol");
    }
    if (execute.ok !== true) {
      throw new Error("Contradiction: execute must authorise a trading artifact");
    }
  }
}

export function runContradictionSelfCheck(): void {
  const now = "2026-09-11T09:00:00.000Z";
  const locked: DailyDecisionArtifact = {
    schema_version: "1",
    decision_id: "2026-09-11:lock",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "protect",
    action: "wait",
    symbol: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "none",
    },
    approved_size: { kind: "none" },
    daily_verdict: "wait",
    tradingLocked: true,
    entryConfirmed: false,
    capital_state: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "unknown",
    },
    broker_state: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "unknown",
    },
    market_state: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "unknown",
    },
    source_timestamps: {
      portfolio: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      capital: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      broker: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      market: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      entry: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
    },
    evidence_ids: [],
    evidence: [],
    blockers: ["Capital unknown"],
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision",
      confidence: 50,
      reason: "Wait",
      confidence_factors: [],
    },
    frozen_portfolio: { positions: [], total_value_inr: 0, pnl_inr: 0 },
    projection: {
      decision: "WAIT",
      action: "wait",
      confidence: 50,
      reason: "Wait",
      confidence_factors: [],
      actions: [],
    },
  };

  assertSurfacesAgreeWithArtifact(locked);

  const trading: DailyDecisionArtifact = {
    ...locked,
    intent: "grow",
    action: "buy",
    symbol: { status: "known", value: "HDFCBANK", observed_at: now },
    approved_size: { kind: "buy_amount", amount_inr: 5000 },
    daily_verdict: "trade",
    tradingLocked: false,
    entryConfirmed: true,
    capital_state: {
      status: "known",
      value: { available_cash_inr: 100000, portfolio_value_inr: 500000 },
      observed_at: now,
    },
    broker_state: {
      status: "known",
      value: { broker: "zerodha", connection: "connected" },
      observed_at: now,
    },
    market_state: {
      status: "known",
      value: { trend: "sideways", session: "market_open" },
      observed_at: now,
    },
    source_timestamps: {
      portfolio: { status: "known", value: now, observed_at: now },
      capital: { status: "known", value: now, observed_at: now },
      broker: { status: "known", value: now, observed_at: now },
      market: { status: "known", value: now, observed_at: now },
      entry: { status: "known", value: now, observed_at: now },
    },
    blockers: [],
    projection: {
      decision: "BUY_MORE",
      action: "buy",
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
      actions: [],
      stock: "HDFCBANK",
      amount: 5000,
    },
  };

  assertSurfacesAgreeWithArtifact(trading);
}
