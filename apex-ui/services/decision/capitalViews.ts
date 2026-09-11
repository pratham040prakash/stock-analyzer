import type {
  DailyDecisionArtifact,
  FrozenPortfolioPosition,
} from "@/types/decision";
import { hydrateArtifactViews } from "@/types/decision";

export type LabeledCapitalView = {
  label: "at_freeze" | "current";
  cash_inr: number | null;
  portfolio_value_inr: number | null;
  positions: FrozenPortfolioPosition[] | null;
  unknown_reason: string | null;
};

export type FreezeAndCurrentCapital = {
  at_freeze: LabeledCapitalView;
  current: LabeledCapitalView;
};

export function labelFreezeAndCurrentCapital(
  artifact: DailyDecisionArtifact,
  current: {
    cash_inr?: number | null;
    portfolio_value_inr?: number | null;
    positions?: FrozenPortfolioPosition[] | null;
  } | null,
): FreezeAndCurrentCapital {
  const hydrated = hydrateArtifactViews(artifact);
  const freezeCapital = hydrated.capital_at_freeze ?? hydrated.capital_state;
  const freezePositions =
    hydrated.positions_at_freeze ?? hydrated.frozen_portfolio.positions;

  return {
    at_freeze: {
      label: "at_freeze",
      cash_inr:
        freezeCapital.status === "known"
          ? freezeCapital.value.available_cash_inr
          : null,
      portfolio_value_inr:
        freezeCapital.status === "known"
          ? freezeCapital.value.portfolio_value_inr
          : hydrated.frozen_portfolio.total_value_inr,
      positions: freezePositions,
      unknown_reason:
        freezeCapital.status === "unknown" ? freezeCapital.reason : null,
    },
    current: {
      label: "current",
      cash_inr:
        current && current.cash_inr !== undefined && current.cash_inr !== null
          ? current.cash_inr
          : null,
      portfolio_value_inr:
        current &&
        current.portfolio_value_inr !== undefined &&
        current.portfolio_value_inr !== null
          ? current.portfolio_value_inr
          : null,
      positions: current?.positions ?? null,
      unknown_reason:
        current == null
          ? "Current broker truth is read separately from the frozen artifact."
          : null,
    },
  };
}

export function runCapitalViewsSelfCheck(): void {
  const now = "2026-09-11T09:00:00.000Z";
  const artifact: DailyDecisionArtifact = {
    schema_version: "1",
    decision_id: "2026-09-11:cap",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "grow",
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
      status: "known",
      value: { available_cash_inr: 10000, portfolio_value_inr: 50000 },
      observed_at: now,
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
      portfolio: { status: "known", value: now, observed_at: now },
      capital: { status: "known", value: now, observed_at: now },
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
    blockers: [],
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision",
      confidence: 50,
      reason: "Wait",
      confidence_factors: [],
    },
    frozen_portfolio: {
      positions: [
        {
          symbol: "INFY",
          quantity: 2,
          average_price: 10,
          marked_price: 12,
          market_value: 24,
        },
      ],
      total_value_inr: 50000,
      pnl_inr: 0,
    },
    projection: {
      decision: "WAIT",
      action: "wait",
      confidence: 50,
      reason: "Wait",
      confidence_factors: [],
      actions: [],
    },
  };

  const views = labelFreezeAndCurrentCapital(artifact, {
    cash_inr: 8000,
    portfolio_value_inr: 52000,
    positions: [],
  });

  if (views.at_freeze.cash_inr !== 10000) {
    throw new Error("Capital views self-check failed: freeze cash must stay 10000");
  }
  if (views.current.cash_inr !== 8000) {
    throw new Error("Capital views self-check failed: current cash must be 8000");
  }
  if (views.at_freeze.positions?.[0]?.symbol !== "INFY") {
    throw new Error("Capital views self-check failed: freeze positions must persist");
  }

  const unknownCurrent = labelFreezeAndCurrentCapital(artifact, null);
  if (!unknownCurrent.current.unknown_reason) {
    throw new Error(
      "Capital views self-check failed: missing current must stay explicit unknown",
    );
  }
}
