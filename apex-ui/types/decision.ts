export type DailyDecisionType =
  | "BUY_MORE"
  | "HOLD"
  | "REDUCE"
  | "WAIT"
  | "EXPLORE";

import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import { formatInr } from "@/lib/funds";
import type { Intent } from "@/types/intent";

export const DAILY_DECISION_ARTIFACT_SCHEMA_VERSION = "1" as const;

export type DailyVerdictV1 = "trade" | "wait" | "pause";

export type ExplicitUnknown<T> =
  | { status: "known"; value: T; observed_at: string }
  | { status: "unknown"; value: null; observed_at: null; reason: string };

export type ApprovedDecisionSize =
  | { kind: "buy_amount"; amount_inr: number }
  | { kind: "sell_percent"; percent: number }
  | { kind: "none" };

export type FrozenPortfolioPosition = {
  symbol: string;
  quantity: number;
  average_price: number;
  marked_price: number;
  market_value: number;
};

export type DecisionEvidenceMetadata = {
  id: string;
  type: "FACT" | "ASSUMPTION" | "ESTIMATE" | "OPINION";
  source: string;
  summary: string;
  observed_at: string | null;
};

/**
 * The immutable, executable decision record for one trading day.
 * Unknown source values are represented explicitly and always fail closed.
 */
export type DailyDecisionArtifact = {
  schema_version: typeof DAILY_DECISION_ARTIFACT_SCHEMA_VERSION;
  decision_id: string;
  decision_date: string;
  frozen_at: string;
  intent: Intent;
  action: DecisionActionType;
  symbol: ExplicitUnknown<string>;
  approved_size: ApprovedDecisionSize;
  daily_verdict: DailyVerdictV1;
  tradingLocked: boolean;
  entryConfirmed: boolean;
  capital_state: ExplicitUnknown<{
    available_cash_inr: number;
    portfolio_value_inr: number;
  }>;
  broker_state: ExplicitUnknown<{
    broker: "zerodha";
    connection: "connected";
  }>;
  market_state: ExplicitUnknown<{
    trend: MarketTrend;
    session: string;
  }>;
  source_timestamps: {
    portfolio: ExplicitUnknown<string>;
    capital: ExplicitUnknown<string>;
    broker: ExplicitUnknown<string>;
    market: ExplicitUnknown<string>;
    entry: ExplicitUnknown<string>;
  };
  evidence_ids: string[];
  evidence: DecisionEvidenceMetadata[];
  blockers: string[];
  decision_metadata: {
    producer: "getDecision/evaluateDailyDecision";
    confidence: number;
    reason: string;
    confidence_factors: string[];
  };
  frozen_portfolio: {
    positions: FrozenPortfolioPosition[];
    total_value_inr: number;
    pnl_inr: number;
  };
  projection: DailyDecisionOutput;
};

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
  order_id?: string;
  fill_price?: number;
  filled_at?: string;
  monitored?: boolean;
  /** execute = APEX trade button; sync = imported from Kite activity. */
  fill_source?: "execute" | "sync";
  /** Set on APEX broker-step fills — distinguishes from sync-attached ghosts. */
  apex_executed?: boolean;
  /** Auto-trade idempotency — set before broker order attempt for the trading day. */
  auto_trade_attempted?: boolean;
  /** Set when auto-trade successfully placed a broker buy today. */
  auto_executed?: boolean;
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

function isIsoTimestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    Number.isFinite(Date.parse(value))
  );
}

function isExplicitUnknown(value: unknown): value is ExplicitUnknown<unknown> {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  if (candidate.status === "unknown") {
    return (
      candidate.value === null &&
      candidate.observed_at === null &&
      typeof candidate.reason === "string" &&
      candidate.reason.length > 0
    );
  }
  return (
    candidate.status === "known" &&
    candidate.value !== null &&
    candidate.value !== undefined &&
    isIsoTimestamp(candidate.observed_at)
  );
}

export function validateDailyDecisionArtifact(
  value: unknown,
): value is DailyDecisionArtifact {
  if (!value || typeof value !== "object") return false;
  const artifact = value as Record<string, unknown>;
  const actions: DecisionActionType[] = [
    "sell",
    "reduce",
    "buy",
    "hold",
    "wait",
    "explore",
  ];
  const verdicts: DailyVerdictV1[] = ["trade", "wait", "pause"];
  const size = artifact.approved_size as Record<string, unknown> | undefined;
  const validSize =
    size?.kind === "none" ||
    (size?.kind === "buy_amount" &&
      typeof size.amount_inr === "number" &&
      Number.isFinite(size.amount_inr) &&
      size.amount_inr > 0) ||
    (size?.kind === "sell_percent" &&
      typeof size.percent === "number" &&
      Number.isFinite(size.percent) &&
      size.percent > 0 &&
      size.percent <= 100);
  const timestamps = artifact.source_timestamps as
    | Record<string, unknown>
    | undefined;
  const metadata = artifact.decision_metadata as
    | Record<string, unknown>
    | undefined;
  const frozen = artifact.frozen_portfolio as
    | Record<string, unknown>
    | undefined;

  return Boolean(
    artifact.schema_version === DAILY_DECISION_ARTIFACT_SCHEMA_VERSION &&
      typeof artifact.decision_id === "string" &&
      /^\d{4}-\d{2}-\d{2}$/.test(String(artifact.decision_date)) &&
      isIsoTimestamp(artifact.frozen_at) &&
      ["grow", "protect", "explore"].includes(String(artifact.intent)) &&
      actions.includes(artifact.action as DecisionActionType) &&
      verdicts.includes(artifact.daily_verdict as DailyVerdictV1) &&
      typeof artifact.tradingLocked === "boolean" &&
      typeof artifact.entryConfirmed === "boolean" &&
      isExplicitUnknown(artifact.symbol) &&
      validSize &&
      isExplicitUnknown(artifact.capital_state) &&
      isExplicitUnknown(artifact.broker_state) &&
      isExplicitUnknown(artifact.market_state) &&
      timestamps &&
      ["portfolio", "capital", "broker", "market", "entry"].every((key) =>
        isExplicitUnknown(timestamps[key]),
      ) &&
      Array.isArray(artifact.evidence_ids) &&
      Array.isArray(artifact.evidence) &&
      Array.isArray(artifact.blockers) &&
      metadata?.producer === "getDecision/evaluateDailyDecision" &&
      typeof metadata.confidence === "number" &&
      typeof metadata.reason === "string" &&
      Array.isArray(metadata.confidence_factors) &&
      Array.isArray(frozen?.positions) &&
      typeof frozen?.total_value_inr === "number" &&
      typeof frozen?.pnl_inr === "number" &&
      artifact.projection &&
      typeof artifact.projection === "object",
  );
}

export function projectArtifactDecision(
  artifact: DailyDecisionArtifact,
): DailyDecisionOutput {
  const projection = artifact.projection;
  const symbol =
    artifact.symbol.status === "known" ? artifact.symbol.value : undefined;
  const authorized =
    !artifact.tradingLocked && artifact.daily_verdict === "trade";
  const amount =
    authorized && artifact.approved_size.kind === "buy_amount"
      ? artifact.approved_size.amount_inr
      : undefined;
  const suggestedSellPercent =
    authorized && artifact.approved_size.kind === "sell_percent"
      ? artifact.approved_size.percent
      : undefined;
  const action: DecisionActionType = authorized ? artifact.action : "wait";
  const decision: DailyDecisionType = authorized
    ? projection.decision
    : "WAIT";

  return {
    ...projection,
    intent: artifact.intent,
    decision,
    action,
    stock: authorized ? symbol : undefined,
    amount,
    suggested_sell_percent: suggestedSellPercent,
  };
}

export function chooseFrozenArtifact(
  stored: DailyDecisionArtifact | null,
  refresh: boolean,
): DailyDecisionArtifact | null {
  return stored && !refresh ? stored : null;
}

export function runDecisionArtifactSelfCheck(): void {
  const now = "2026-09-11T09:00:00.000Z";
  const unknown = {
    status: "unknown" as const,
    value: null,
    observed_at: null,
    reason: "not available",
  };
  const artifact: DailyDecisionArtifact = {
    schema_version: DAILY_DECISION_ARTIFACT_SCHEMA_VERSION,
    decision_id: "2026-09-11-user",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "grow",
    action: "wait",
    symbol: unknown,
    approved_size: { kind: "none" },
    daily_verdict: "wait",
    tradingLocked: true,
    entryConfirmed: false,
    capital_state: unknown,
    broker_state: unknown,
    market_state: unknown,
    source_timestamps: {
      portfolio: unknown,
      capital: unknown,
      broker: unknown,
      market: unknown,
      entry: unknown,
    },
    evidence_ids: ["reason"],
    evidence: [
      {
        id: "reason",
        type: "FACT",
        source: "decision_engine",
        summary: "Wait",
        observed_at: now,
      },
    ],
    blockers: ["Capital state unknown"],
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
  if (!validateDailyDecisionArtifact(artifact)) {
    throw new Error("Decision artifact self-check failed: valid v1 rejected");
  }
  if (chooseFrozenArtifact(artifact, false) !== artifact) {
    throw new Error("Decision artifact self-check failed: freeze changed artifact");
  }
  if (chooseFrozenArtifact(artifact, true) !== null) {
    throw new Error("Decision artifact self-check failed: refresh did not recompute");
  }

  // Wave 2 fail-closed projection: a locked artifact must project to
  // WAIT with no amount/sellPercent and no exposed symbol.
  const lockedProjection = projectArtifactDecision(artifact);
  if (
    lockedProjection.action !== "wait" ||
    lockedProjection.decision !== "WAIT" ||
    lockedProjection.stock !== undefined ||
    lockedProjection.amount !== undefined ||
    lockedProjection.suggested_sell_percent !== undefined
  ) {
    throw new Error(
      "Decision artifact self-check failed: locked artifact must project WAIT with no size",
    );
  }

  const tradingArtifact: DailyDecisionArtifact = {
    ...artifact,
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
  const tradingProjection = projectArtifactDecision(tradingArtifact);
  if (
    tradingProjection.action !== "buy" ||
    tradingProjection.stock !== "HDFCBANK" ||
    tradingProjection.amount !== 5000
  ) {
    throw new Error(
      "Decision artifact self-check failed: trading artifact must project BUY with size",
    );
  }
}

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
