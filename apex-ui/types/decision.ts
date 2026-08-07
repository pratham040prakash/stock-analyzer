export type DailyDecisionType = "BUY_MORE" | "HOLD" | "REDUCE" | "WAIT";

export type DecisionActionType = "reduce" | "buy" | "hold" | "wait";

export type DailyDecisionOutput = {
  decision: DailyDecisionType;
  action: DecisionActionType;
  stock?: string;
  confidence: number;
  allocation?: number;
  suggested_sell_percent?: number;
  suggestion?: string;
  message?: string;
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
};

export function decisionActionLabel(action: DecisionActionType): string {
  switch (action) {
    case "reduce":
      return "Reduce";
    case "buy":
      return "Buy more";
    case "wait":
      return "Wait";
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
    default:
      return "hold";
  }
}

export function decisionHeadline(decision: DailyDecisionOutput): string {
  if (
    decision.action === "reduce" &&
    decision.stock &&
    decision.suggested_sell_percent !== undefined
  ) {
    if (decision.suggestion === "Book partial profit") {
      return `Book profit · ${decision.stock} (${decision.confidence}%)`;
    }
    if (decision.suggestion === "Reduce risk exposure") {
      return `Trim risk · ${decision.stock} (${decision.confidence}%)`;
    }
    return `Sell ${decision.suggested_sell_percent}% ${decision.stock} (${decision.confidence}%)`;
  }

  const label = decisionActionLabel(decision.action);
  if (decision.stock) {
    return `${label} ${decision.stock} (${decision.confidence}%)`;
  }
  return `${label} (${decision.confidence}%)`;
}

export function decisionAllocationHint(
  allocation: number,
  sellPercent: number,
): string {
  const nextAllocation = Math.round(allocation * (1 - sellPercent / 100));
  return `Reducing ${sellPercent}% will bring allocation from ${allocation}% → ${nextAllocation}%`;
}
