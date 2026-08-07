import type { DailyDecisionOutput, DecisionOpportunity } from "@/types/decision";
import type { Intent } from "@/types/intent";

const EXPLORE_OPPORTUNITIES: DecisionOpportunity[] = [
  { name: "HDFC Bank", reason: "Stable large cap" },
  { name: "Infosys", reason: "Strong IT sector" },
  { name: "Nifty 50 ETF", reason: "Diversification" },
];

export type OptimisticDecisionContext = {
  stock?: string;
  allocation?: number;
};

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
      reason: "Portfolio size can be increased steadily",
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
