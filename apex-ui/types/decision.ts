export type DailyDecisionType =
  | "BUY_MORE"
  | "HOLD"
  | "REDUCE"
  | "WAIT"
  | "EXPLORE";

import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import { formatInr } from "@/lib/funds";
import type { Intent } from "@/types/intent";

export type DecisionActionType =
  | "sell"
  | "reduce"
  | "buy"
  | "hold"
  | "wait"
  | "explore";

export type DecisionOpportunity = {
  name: string;
  type: string;
};

export type RecommendedAllocationItem = {
  name: string;
  amount: number;
  reason: string;
};

export type Signals = {
  trend: number;
  momentum: number;
  volume: number;
};

export type MarketTrend = "bullish" | "bearish" | "sideways";

export type DecisionValidationBreakdown = {
  signal_strength: number;
  signal_agreement: boolean;
  market_alignment: boolean;
  risk_ok: boolean;
};

export type ValidationResult = {
  confidence: number;
  isValid: boolean;
  breakdown: DecisionValidationBreakdown;
};

export type ConfidenceResult = {
  probability: number;
  expectedReturn: number;
  expectedDrawdown: number;
  edgeScore: number;
};

export type StockPick = {
  stock: string;
  score: number;
  signals: Signals;
  /** Latest price when market data is available. */
  price?: number;
  /** Recent range high — activation level for breakout confirmation. */
  activationLevel?: number;
};

export type DailyDecisionOutput = {
  decision: DailyDecisionType;
  action: DecisionActionType;
  intent?: Intent | null;
  stock?: string;
  confidence: number;
  /** Top holding weight % — not fund allocation suggestions. */
  allocation?: number;
  suggested_sell_percent?: number;
  suggestion?: string;
  message?: string;
  opportunities?: DecisionOpportunity[];
  recommended_allocation?: RecommendedAllocationItem[];
  reason: string;
  confidence_factors: string[];
  actions: string[];
  /** @deprecated use stock */
  focusSymbol?: string;
  /** @deprecated use allocation */
  focusAllocationPct?: number;
  validation?: DecisionValidationBreakdown;
  picks?: StockPick[];
  /** Suggested invest amount for the primary pick (buy intent). */
  amount?: number;
  /** Edge-based allocation as a fraction of portfolio (0–0.2). */
  allocationPercent?: number;
  /** Why this allocation size was chosen. */
  allocationReason?: string;
  /** Probabilistic confidence metrics from the confidence engine. */
  confidenceMetrics?: ConfidenceResult;
  /** Price structure score (0–100) from support/resistance positioning. */
  structureScore?: number;
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
  adaptiveSignalWeights?: {
    trend: number;
    momentum: number;
    volume: number;
  } | null;
  supabase?: import("@supabase/supabase-js").SupabaseClient<
    import("@/types/database").Database
  >;
  userId?: string;
};

export function isSellAction(action: DecisionActionType): boolean {
  return action === "sell" || action === "reduce";
}

export function decisionActionLabel(action: DecisionActionType): string {
  switch (action) {
    case "sell":
      return "Sell";
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
    isSellAction(decision.action) &&
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

  if (isSellAction(decision.action) && decision.stock) {
    const pct = sellPercent ?? decision.suggested_sell_percent ?? 20;
    return decision.message ?? `Sell ${pct}% of ${decision.stock}`;
  }

  if (decision.action === "buy") {
    if (decision.stock && decision.amount && decision.amount > 0) {
      return `Invest ${formatInr(decision.amount)} in ${decision.stock}`;
    }
    return decision.message ?? "Invest gradually to grow your portfolio";
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
