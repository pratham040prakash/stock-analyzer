export type DailyDecisionType =
  | "BUY_MORE"
  | "HOLD"
  | "REDUCE"
  | "WAIT"
  | "EXPLORE";

import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import type { Intent } from "@/types/intent";

export type DecisionActionType =
  | "reduce"
  | "buy"
  | "hold"
  | "wait"
  | "explore";

export type DecisionOpportunity = {
  name: string;
  reason: string;
};

export type DailyDecisionOutput = {
  decision: DailyDecisionType;
  action: DecisionActionType;
  intent?: Intent | null;
  stock?: string;
  confidence: number;
  allocation?: number;
  suggested_sell_percent?: number;
  suggestion?: string;
  message?: string;
  opportunities?: DecisionOpportunity[];
  reason: string;
  confidence_factors: string[];
  actions: string[];
  /** @deprecated use stock */
  focusSymbol?: string;
  /** @deprecated use allocation */
  focusAllocationPct?: number;
};

export type PortfolioSnapshotInput = {
  holdings: import("@/types/portfolio").Portfolio["holdings"];
  total_value: number;
  pnl?: number;
};

export type DecisionEngineInput = {
  portfolioSnapshot: PortfolioSnapshotInput;
  financialProfile: import("@/lib/financialProfile").FinancialProfile | null;
  lastMentorOutput?: import("@/types/mentorDecision").MentorDecision | null;
  intent?: Intent | null;
};

export function decisionActionLabel(action: DecisionActionType): string {
  switch (action) {
    case "reduce":
      return "Reduce";
    case "buy":
      return "Buy more";
    case "wait":
      return "Wait";
    case "explore":
      return "Explore";
    default:
      return "Hold";
  }
}

export function dailyDecisionTypeToAction(
  decision: DailyDecisionType,
): DecisionActionType {
  switch (decision) {
    case "REDUCE":
      return "reduce";
    case "BUY_MORE":
      return "buy";
    case "WAIT":
      return "wait";
    case "EXPLORE":
      return "explore";
    default:
      return "hold";
  }
}

export function decisionHeadline(decision: DailyDecisionOutput): string {
  const confidence = displayConfidencePercent(decision.confidence);

  if (decision.action === "explore") {
    return `Explore opportunities (${confidence}%)`;
  }

  if (
    decision.action === "reduce" &&
    decision.stock &&
    decision.suggested_sell_percent !== undefined
  ) {
    if (decision.suggestion === "Book partial profit") {
      return `Book profit · ${decision.stock} (${confidence}%)`;
    }
    if (decision.suggestion === "Reduce risk exposure") {
      return `Trim risk · ${decision.stock} (${confidence}%)`;
    }
    return `Sell ${decision.suggested_sell_percent}% ${decision.stock} (${confidence}%)`;
  }

  const label = decisionActionLabel(decision.action);
  if (decision.stock) {
    return `${label} ${decision.stock} (${confidence}%)`;
  }
  return `${label} (${confidence}%)`;
}

export function decisionAllocationHint(
  allocation: number,
  sellPercent: number,
): string {
  const nextAllocation = Math.round(allocation * (1 - sellPercent / 100));
  return `Reducing ${sellPercent}% will bring allocation from ${allocation}% → ${nextAllocation}%`;
}

const BASE_SELL_PERCENTS = [10, 20, 50];

export function buildSellPercentOptions(suggested?: number): number[] {
  const options =
    suggested !== undefined
      ? [...BASE_SELL_PERCENTS, suggested]
      : [...BASE_SELL_PERCENTS];

  return [...new Set(options)].sort((a, b) => a - b);
}

/** Never show 100% — cap displayed confidence at 90. */
export function displayConfidencePercent(confidence: number): number {
  return Math.min(90, Math.max(0, Math.round(confidence)));
}

export function decisionConfidenceBadge(confidence: number): string {
  const display = displayConfidencePercent(confidence);

  if (confidence >= 90) {
    return `Very high confidence (${display}%)`;
  }
  if (confidence >= 80) {
    return `High confidence (${display}%)`;
  }
  if (confidence >= 60) {
    return `Moderate confidence (${display}%)`;
  }
  return `Low confidence (${display}%)`;
}

export function decisionHeroActionText(
  decision: DailyDecisionOutput,
  sellPercent?: number,
): string {
  if (decision.action === "explore") {
    return decision.message ?? "Explore opportunities aligned with you";
  }

  if (decision.action === "reduce" && decision.stock) {
    const pct = sellPercent ?? decision.suggested_sell_percent ?? 20;
    return `Sell ${pct}% of ${decision.stock}`;
  }

  if (decision.action === "buy") {
    return decision.message ?? "Invest your monthly surplus steadily";
  }

  if (decision.action === "wait") {
    return "Pause new investments for now";
  }

  return "Hold steady — no change today";
}

export function decisionRiskMicrocopy(
  allocation: number,
  sellPercent: number,
): string {
  const current = portfolioRiskFromAllocation(allocation).risk_level;
  const next = portfolioRiskFromAllocation(
    Math.round(allocation * (1 - sellPercent / 100)),
  ).risk_level;
  return `This reduces your risk from ${current.toUpperCase()} → ${next.toUpperCase()}`;
}
