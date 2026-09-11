import { getMarketSessionPhase } from "@/lib/broker/marketSession";
import type { Intent } from "@/types/intent";
import type {
  DailyDecisionArtifact,
  DailyDecisionOutput,
  ExplicitUnknown,
  MarketTrend,
  PortfolioSnapshotInput,
} from "@/types/decision";
import { DAILY_DECISION_ARTIFACT_SCHEMA_VERSION } from "@/types/decision";
import { applyFreshnessPolicy } from "@/services/decision/freshness";

type SourceState<T> = ExplicitUnknown<T>;

export type BuildDailyArtifactInput = {
  userId: string;
  decisionDate: string;
  frozenAt: string;
  intent: Intent;
  decision: DailyDecisionOutput;
  portfolio: PortfolioSnapshotInput;
  portfolioObservedAt: string | null;
  capital: SourceState<{
    available_cash_inr: number;
    portfolio_value_inr: number;
  }>;
  broker: SourceState<{ broker: "zerodha"; connection: "connected" }>;
  market: SourceState<{ trend: MarketTrend; session: string }>;
  entry: SourceState<{ confirmed: boolean; reason: string }>;
};

function unknown<T>(reason: string): ExplicitUnknown<T> {
  return { status: "unknown", value: null, observed_at: null, reason };
}

function sourceTimestamp<T>(
  source: SourceState<T>,
): ExplicitUnknown<string> {
  return source.status === "known"
    ? {
        status: "known",
        value: source.observed_at,
        observed_at: source.observed_at,
      }
    : unknown(source.reason);
}

export function knownSource<T>(value: T, observedAt: string): ExplicitUnknown<T> {
  return { status: "known", value, observed_at: observedAt };
}

export function unknownSource<T>(reason: string): ExplicitUnknown<T> {
  return unknown(reason);
}

export function buildDailyDecisionArtifact(
  input: BuildDailyArtifactInput,
): DailyDecisionArtifact {
  const decision = input.decision;

  // Wave 2 fail-closed freshness: downgrade any source that is stale
  // beyond its allowed window before we derive blockers/verdict.
  const freshness = applyFreshnessPolicy(
    {
      portfolioObservedAt: input.portfolioObservedAt,
      capital: input.capital,
      broker: input.broker,
      market: input.market,
      entry: input.entry,
    },
    input.frozenAt,
  );
  const capital = freshness.sources.capital;
  const broker = freshness.sources.broker;
  const market = freshness.sources.market;
  const entry = freshness.sources.entry;
  const portfolioObservedAt = freshness.sources.portfolioObservedAt;

  const actionable = decision.action === "buy" || decision.action === "sell";
  const entryConfirmed =
    decision.action === "sell"
      ? true
      : entry.status === "known" && entry.value.confirmed;
  const symbol = decision.stock?.trim().toUpperCase();
  const blockers: string[] = [];

  if (!actionable) blockers.push(`Action ${decision.action} is not executable`);
  if (!symbol) blockers.push("Decision symbol is unknown");
  if (portfolioObservedAt === null) blockers.push("Portfolio source timestamp is unknown");
  if (capital.status === "unknown") blockers.push(capital.reason);
  if (broker.status === "unknown") blockers.push(broker.reason);
  if (market.status === "unknown") blockers.push(market.reason);
  for (const blocker of freshness.extraBlockers) {
    if (!blockers.includes(blocker)) blockers.push(blocker);
  }
  if (decision.action === "buy" && !entryConfirmed) {
    blockers.push(
      entry.status === "known"
        ? entry.value.reason || "Entry is not confirmed"
        : entry.reason,
    );
  }

  const approvedSize =
    decision.action === "buy" && decision.amount && decision.amount > 0
      ? { kind: "buy_amount" as const, amount_inr: Math.round(decision.amount) }
      : decision.action === "sell" &&
          decision.suggested_sell_percent &&
          decision.suggested_sell_percent > 0
        ? {
            kind: "sell_percent" as const,
            percent: Math.round(decision.suggested_sell_percent),
          }
        : { kind: "none" as const };

  if (actionable && approvedSize.kind === "none") {
    blockers.push("Approved execution size is unknown");
  }

  const tradingLocked = blockers.length > 0;
  const dailyVerdict = actionable && !tradingLocked ? "trade" : "wait";
  const supporting = [
    {
      id: `${input.decisionDate}:reason`,
      type: "FACT" as const,
      source: "decision_engine",
      summary: decision.reason,
      observed_at: input.frozenAt,
    },
    ...(decision.confidence_factors ?? []).slice(0, 3).map((summary, index) => ({
      id: `${input.decisionDate}:factor:${index + 1}`,
      type: "FACT" as const,
      source: "decision_engine",
      summary,
      observed_at: input.frozenAt,
    })),
  ];
  const conflicting =
    decision.validation?.risk_ok === false
      ? [
          {
            id: `${input.decisionDate}:risk`,
            type: "FACT" as const,
            source: "risk_control",
            summary: "Risk checks flagged caution",
            observed_at: input.frozenAt,
          },
        ]
      : [];
  const evidence = [...supporting, ...conflicting];

  return {
    schema_version: DAILY_DECISION_ARTIFACT_SCHEMA_VERSION,
    decision_id: `${input.decisionDate}:${input.userId}`,
    decision_date: input.decisionDate,
    frozen_at: input.frozenAt,
    intent: input.intent,
    action: decision.action,
    symbol: symbol
      ? knownSource(symbol, input.frozenAt)
      : unknown("Decision engine did not select a symbol"),
    approved_size: approvedSize,
    daily_verdict: dailyVerdict,
    tradingLocked,
    entryConfirmed,
    capital_state: capital,
    broker_state: broker,
    market_state: market,
    source_timestamps: {
      portfolio: portfolioObservedAt
        ? knownSource(portfolioObservedAt, portfolioObservedAt)
        : unknown("Portfolio timestamp was not available"),
      capital: sourceTimestamp(capital),
      broker: sourceTimestamp(broker),
      market: sourceTimestamp(market),
      entry: sourceTimestamp(entry),
    },
    evidence_ids: evidence.map((item) => item.id),
    evidence,
    evidence_graph: {
      supporting_ids: supporting.map((item) => item.id),
      conflicting_ids: conflicting.map((item) => item.id),
    },
    blockers,
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision",
      confidence: decision.confidence,
      reason: decision.reason,
      confidence_factors: decision.confidence_factors,
    },
    frozen_portfolio: {
      positions: input.portfolio.holdings.map((holding) => ({
        symbol: holding.symbol.trim().toUpperCase(),
        quantity: holding.quantity,
        average_price: holding.avgPrice,
        marked_price: holding.currentPrice,
        market_value: holding.quantity * holding.currentPrice,
      })),
      total_value_inr: input.portfolio.total_value,
      pnl_inr: input.portfolio.pnl ?? 0,
    },
    capital_at_freeze: capital,
    positions_at_freeze: input.portfolio.holdings.map((holding) => ({
      symbol: holding.symbol.trim().toUpperCase(),
      quantity: holding.quantity,
      average_price: holding.avgPrice,
      marked_price: holding.currentPrice,
      market_value: holding.quantity * holding.currentPrice,
    })),
    projection: decision,
  };
}

export function currentMarketState(
  trend: MarketTrend,
  observedAt: string,
): SourceState<{ trend: MarketTrend; session: string }> {
  return knownSource(
    { trend, session: getMarketSessionPhase(new Date(observedAt)) },
    observedAt,
  );
}

