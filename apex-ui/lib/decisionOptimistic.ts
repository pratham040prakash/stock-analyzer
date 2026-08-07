import {
  deployableFundsForIntent,
  getAllocation,
} from "@/lib/allocation";
import { getOpportunities } from "@/lib/recommendations";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type { DailyDecisionOutput } from "@/types/decision";
import type { Intent } from "@/types/intent";

const GROW_OPPORTUNITIES = getOpportunities("grow");
const EXPLORE_OPPORTUNITIES = getOpportunities("explore");

export type OptimisticDecisionContext = {
  stock?: string;
  allocation?: number;
  availableCash?: number;
  riskLevel?: PortfolioRiskLevel;
};

function optimisticAllocation(
  intent: Intent,
  context: OptimisticDecisionContext,
): DailyDecisionOutput["recommended_allocation"] {
  const { availableCash, riskLevel = "Low" } = context;

  if (!availableCash || availableCash <= 0) {
    return [];
  }

  const deployable = deployableFundsForIntent(availableCash, intent);
  return getAllocation(deployable, intent, riskLevel);
}

/** Instant placeholder while the API refines the decision. */
export function createOptimisticDecision(
  intent: Intent,
  context: OptimisticDecisionContext = {},
): DailyDecisionOutput {
  const base = {
    confidence: 78,
    confidence_factors: [] as string[],
    actions: [] as string[],
    intent,
  };

  if (intent === "grow") {
    return {
      ...base,
      decision: "BUY_MORE",
      action: "buy",
      message: "Invest gradually to grow your portfolio",
      suggestion: "Use available funds to accumulate quality stocks",
      opportunities: GROW_OPPORTUNITIES,
      reason: "Portfolio size can be increased steadily",
      recommended_allocation: optimisticAllocation(intent, context),
    };
  }

  if (intent === "explore") {
    return {
      ...base,
      decision: "EXPLORE",
      action: "explore",
      message: "Here are opportunities for you",
      opportunities: EXPLORE_OPPORTUNITIES,
      reason: "Finding ideas aligned with your profile",
      recommended_allocation: optimisticAllocation(intent, context),
    };
  }

  const { stock, allocation } = context;

  if (stock && allocation !== undefined && allocation > 80) {
    return {
      ...base,
      decision: "REDUCE",
      action: "sell",
      stock,
      allocation,
      suggested_sell_percent: 25,
      message: "Sell 25% to reduce concentration",
      suggestion: "Reduce risk exposure",
      reason: "High concentration risk",
    };
  }

  if (stock && allocation !== undefined && allocation > 50) {
    return {
      ...base,
      decision: "REDUCE",
      action: "sell",
      stock,
      allocation,
      suggested_sell_percent: 20,
      message: `Trim ${stock} to reduce concentration`,
      suggestion: "Reduce risk exposure",
      reason: "Concentration is elevated",
    };
  }

  return {
    ...base,
    decision: "HOLD",
    action: "hold",
    message: "Hold steady while we refine your risk guidance",
    reason: "Reviewing portfolio balance and exposure",
  };
}
