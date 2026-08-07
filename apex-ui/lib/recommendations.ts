import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
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

export function getExploreOpportunities(): Pick<Recommendation, "name" | "reason">[] {
  return getRecommendations("explore", "Low").map(({ name, reason }) => ({
    name,
    reason,
  }));
}
