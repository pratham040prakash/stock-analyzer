import { safeInvestAmount } from "@/lib/funds";
import { getRecommendations } from "@/lib/recommendations";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type { RecommendedAllocationItem } from "@/types/decision";
import type { Intent } from "@/types/intent";

const ALLOCATION_WEIGHTS: Partial<Record<Intent, number[]>> = {
  grow: [0.6, 0.4],
  explore: [0.4, 0.3, 0.3],
};

export function roundAllocationAmount(amount: number): number {
  if (amount <= 0) {
    return 0;
  }

  const step = amount >= 10000 ? 1000 : 500;
  return Math.round(amount / step) * step;
}

function normalizeAllocationItems(
  items: RecommendedAllocationItem[],
  totalFunds: number,
): RecommendedAllocationItem[] {
  if (totalFunds <= 0 || items.length === 0) {
    return [];
  }

  const rounded = items.map((item) => ({
    ...item,
    amount: roundAllocationAmount(item.amount),
  }));

  const sum = rounded.reduce((acc, item) => acc + item.amount, 0);
  const remainder = totalFunds - sum;

  if (remainder !== 0 && rounded.length > 0) {
    const last = rounded[rounded.length - 1];
    last.amount = Math.max(0, last.amount + remainder);
    last.amount = roundAllocationAmount(last.amount);
  }

  return rounded.filter((item) => item.amount > 0);
}

export function deployableFundsForIntent(
  funds: number,
  intent: Intent,
): number {
  if (funds <= 0) {
    return 0;
  }

  if (intent === "grow") {
    return safeInvestAmount(funds);
  }

  if (intent === "explore") {
    return funds;
  }

  return 0;
}

export function getAllocation(
  funds: number,
  intent: Intent,
  risk: PortfolioRiskLevel,
): RecommendedAllocationItem[] {
  if (funds <= 0) {
    return [];
  }

  const recommendations = getRecommendations(intent, risk);
  const weights = ALLOCATION_WEIGHTS[intent];

  if (!recommendations.length || !weights) {
    return [];
  }

  const items = recommendations.map((recommendation, index) => ({
    name: recommendation.name,
    amount: funds * (weights[index] ?? 0),
    reason: recommendation.reason,
  }));

  return normalizeAllocationItems(items, funds);
}
