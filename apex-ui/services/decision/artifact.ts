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
  const actionable = decision.action === "buy" || decision.action === "sell";
  const entryConfirmed =
    decision.action === "sell"
      ? true
      : input.entry.status === "known" && input.entry.value.confirmed;
  const symbol = decision.stock?.trim().toUpperCase();
  const blockers: string[] = [];

  if (!actionable) blockers.push(`Action ${decision.action} is not executable`);
  if (!symbol) blockers.push("Decision symbol is unknown");
  if (input.portfolioObservedAt === null) blockers.push("Portfolio source timestamp is unknown");
  if (input.capital.status === "unknown") blockers.push(input.capital.reason);
  if (input.broker.status === "unknown") blockers.push(input.broker.reason);
  if (input.market.status === "unknown") blockers.push(input.market.reason);
  if (decision.action === "buy" && !entryConfirmed) {
    blockers.push(
      input.entry.status === "known"
        ? input.entry.value.reason || "Entry is not confirmed"
        : input.entry.reason,
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
  const evidence = [
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
    capital_state: input.capital,
    broker_state: input.broker,
    market_state: input.market,
    source_timestamps: {
      portfolio: input.portfolioObservedAt
        ? knownSource(input.portfolioObservedAt, input.portfolioObservedAt)
        : unknown("Portfolio timestamp was not available"),
      capital: sourceTimestamp(input.capital),
      broker: sourceTimestamp(input.broker),
      market: sourceTimestamp(input.market),
      entry: sourceTimestamp(input.entry),
    },
    evidence_ids: evidence.map((item) => item.id),
    evidence,
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

