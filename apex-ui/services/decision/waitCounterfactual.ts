import type { DailyDecisionArtifact } from "@/types/decision";

export type WaitCounterfactualFill = {
  symbol: string;
  side: "buy" | "sell";
  amount?: number | null;
  sourceKnown: boolean;
};

export type WaitCounterfactual = {
  decision_date: string;
  status: "honored" | "overridden" | "unknown";
  summary: string;
  fills: Array<{ symbol: string; side: "buy" | "sell"; amount?: number | null }>;
};

function wasWaitDay(artifact: DailyDecisionArtifact): boolean {
  return (
    artifact.daily_verdict !== "trade" ||
    artifact.tradingLocked ||
    artifact.action === "wait" ||
    artifact.action === "hold" ||
    artifact.action === "explore"
  );
}

/**
 * Score a prior-day WAIT against broker fill records.
 * Honored: no prohibited incremental buy.
 * Overridden: a buy fill exists.
 * Unknown: broker outcome is not known.
 */
export function evaluateWaitCounterfactual(params: {
  artifact: DailyDecisionArtifact | null;
  fills: WaitCounterfactualFill[];
}): WaitCounterfactual | null {
  const artifact = params.artifact;
  if (!artifact || !wasWaitDay(artifact)) {
    return null;
  }

  if (params.fills.some((fill) => !fill.sourceKnown)) {
    return {
      decision_date: artifact.decision_date,
      status: "unknown",
      summary:
        "Broker outcome is unknown — cannot score yesterday's WAIT.",
      fills: [],
    };
  }

  const buys = params.fills.filter((fill) => fill.side === "buy");
  if (buys.length === 0) {
    return {
      decision_date: artifact.decision_date,
      status: "honored",
      summary: "WAIT was honored — no prohibited fill.",
      fills: [],
    };
  }

  return {
    decision_date: artifact.decision_date,
    status: "overridden",
    summary: `WAIT was overridden — bought ${buys
      .map((fill) => fill.symbol)
      .join(", ")}.`,
    fills: buys.map((fill) => ({
      symbol: fill.symbol,
      side: fill.side,
      amount: fill.amount ?? null,
    })),
  };
}

export function runWaitCounterfactualSelfCheck(): void {
  const now = "2026-09-10T09:00:00.000Z";
  const waitArtifact: DailyDecisionArtifact = {
    schema_version: "1",
    decision_id: "2026-09-10:wait",
    decision_date: "2026-09-10",
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
    blockers: ["Wait"],
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

  const honored = evaluateWaitCounterfactual({
    artifact: waitArtifact,
    fills: [],
  });
  if (honored?.status !== "honored") {
    throw new Error("WAIT counterfactual self-check failed: empty fills must honor");
  }

  const overridden = evaluateWaitCounterfactual({
    artifact: waitArtifact,
    fills: [{ symbol: "INFY", side: "buy", amount: 2000, sourceKnown: true }],
  });
  if (overridden?.status !== "overridden" || !overridden.summary.includes("INFY")) {
    throw new Error("WAIT counterfactual self-check failed: buy fill must override");
  }

  const unknown = evaluateWaitCounterfactual({
    artifact: waitArtifact,
    fills: [{ symbol: "INFY", side: "buy", sourceKnown: false }],
  });
  if (unknown?.status !== "unknown") {
    throw new Error("WAIT counterfactual self-check failed: unknown broker must stay unknown");
  }

  const tradeDay = evaluateWaitCounterfactual({
    artifact: { ...waitArtifact, daily_verdict: "trade", tradingLocked: false, action: "buy" },
    fills: [],
  });
  if (tradeDay !== null) {
    throw new Error("WAIT counterfactual self-check failed: trade days have no WAIT score");
  }
}
