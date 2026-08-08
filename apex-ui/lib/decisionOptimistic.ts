import {
  deployableFundsForIntent,
  getAllocation,
  recommendationsToPlanItems,
} from "@/lib/allocation";
import {
  getAllRecommendations,
  getOpportunities,
  getRecommendations,
  type RecommendationPortfolio,
} from "@/lib/recommendations";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type { DailyDecisionOutput } from "@/types/decision";
import type { Intent } from "@/types/intent";

export type OptimisticDecisionContext = {
  stock?: string;
  allocation?: number;
  availableCash?: number;
  riskLevel?: PortfolioRiskLevel;
  holdings?: { symbol: string; allocation_pct?: number }[];
};

function portfolioFromContext(
  context: OptimisticDecisionContext,
): RecommendationPortfolio {
  if (context.holdings?.length) {
    const top = [...context.holdings].sort(
      (a, b) => (b.allocation_pct ?? 0) - (a.allocation_pct ?? 0),
    )[0];

    return {
      holdings: context.holdings,
      top_symbol: top?.symbol ?? context.stock,
      top_allocation_pct: top?.allocation_pct ?? context.allocation,
    };
  }

  return {
    top_symbol: context.stock,
    top_allocation_pct: context.allocation,
    holdings: context.stock
      ? [{ symbol: context.stock, allocation_pct: context.allocation }]
      : [],
  };
}

function optimisticAllocation(
  intent: Intent,
  context: OptimisticDecisionContext,
): DailyDecisionOutput["recommended_allocation"] {
  const { availableCash, riskLevel = "Low" } = context;
  const portfolio = portfolioFromContext(context);

  if (!availableCash || availableCash <= 0) {
    return recommendationsToPlanItems(getRecommendations(intent, riskLevel, portfolio));
  }

  const deployable = deployableFundsForIntent(availableCash, intent);
  return getAllocation(deployable, intent, riskLevel, portfolio);
}

/** Instant placeholder while the API refines the decision. */
export function createOptimisticDecision(
  intent: Intent,
  context: OptimisticDecisionContext = {},
): DailyDecisionOutput {
  const riskLevel = context.riskLevel ?? "Low";
  const portfolio = portfolioFromContext(context);
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
      opportunities: getOpportunities("grow", riskLevel, portfolio),
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
      opportunities: getOpportunities("explore", riskLevel, portfolio),
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
