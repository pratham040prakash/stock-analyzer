import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type { DecisionOpportunity } from "@/types/decision";
import type { Intent } from "@/types/intent";

export type Recommendation = {
  name: string;
  type: string;
  reason: string;
};

export function getRecommendations(
  intent: Intent,
  risk: PortfolioRiskLevel,
): Recommendation[] {
  void risk;

  if (intent === "grow") {
    return [
      {
        name: "NIFTYBEES",
        type: "ETF",
        reason: "Broad market diversification",
      },
      {
        name: "HDFC Bank",
        type: "Large Cap",
        reason: "Stable large cap",
      },
    ];
  }

  if (intent === "explore") {
    return [
      {
        name: "Reliance",
        type: "Market Leader",
        reason: "Market Leader",
      },
      {
        name: "Infosys",
        type: "IT Growth",
        reason: "IT Growth",
      },
      {
        name: "Tata Motors",
        type: "Momentum",
        reason: "Momentum",
      },
    ];
  }

  return [];
}

export function getOpportunities(
  intent: Intent,
  risk: PortfolioRiskLevel = "Low",
): DecisionOpportunity[] {
  return getRecommendations(intent, risk).map(({ name, type }) => ({
    name,
    type,
  }));
}
