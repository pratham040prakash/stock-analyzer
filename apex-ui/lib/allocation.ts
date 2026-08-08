import { safeInvestAmount } from "@/lib/funds";
import {
  getOpportunities,
  getRecommendations,
  type RecommendationPortfolio,
} from "@/lib/recommendations";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type {
  DecisionOpportunity,
  RecommendedAllocationItem,
} from "@/types/decision";
import type { Intent } from "@/types/intent";

function weightsForCount(count: number, intent: Intent): number[] {
  if (count <= 0) {
    return [];
  }

  if (count === 1) {
    return [1];
  }

  if (count === 2) {
    return intent === "grow" ? [0.6, 0.4] : [0.55, 0.45];
  }

  if (intent === "grow") {
    return [0.5, 0.3, 0.2];
  }

  return [0.4, 0.35, 0.25];
}

function allocationStep(totalFunds: number): number {
  if (totalFunds >= 10000) {
    return 1000;
  }
  if (totalFunds >= 5000) {
    return 500;
  }
  if (totalFunds >= 1000) {
    return 100;
  }
  return 1;
}

export function roundAllocationAmount(
  amount: number,
  totalFunds?: number,
): number {
  if (amount <= 0) {
    return 0;
  }

  const step = allocationStep(totalFunds ?? amount);
  return Math.round(amount / step) * step;
}

function distributeRemainder(
  items: RecommendedAllocationItem[],
  totalFunds: number,
): RecommendedAllocationItem[] {
  let sum = items.reduce((acc, item) => acc + item.amount, 0);
  let index = 0;

  while (sum < totalFunds && index < 10_000) {
    items[index % items.length].amount += 1;
    sum += 1;
    index += 1;
  }

  return items;
}

function normalizeAllocationItems(
  items: RecommendedAllocationItem[],
  totalFunds: number,
): RecommendedAllocationItem[] {
  if (totalFunds <= 0 || items.length === 0) {
    return [];
  }

  if (totalFunds < 1000) {
    const exact = distributeRemainder(
      items.map((item) => ({
        ...item,
        amount: Math.floor(item.amount),
      })),
      totalFunds,
    );

    return exact.filter((item) => item.amount > 0);
  }

  const step = allocationStep(totalFunds);
  const rounded = items.map((item) => ({
    ...item,
    amount: Math.round(item.amount / step) * step,
  }));

  const sum = rounded.reduce((acc, item) => acc + item.amount, 0);
  const remainder = totalFunds - sum;

  if (remainder !== 0 && rounded.length > 0) {
    const last = rounded[rounded.length - 1];
    last.amount = Math.max(0, last.amount + remainder);
    last.amount = roundAllocationAmount(last.amount, totalFunds);
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

export function buildExecutionPlan(
  opportunities: DecisionOpportunity[],
  funds: number,
  intent: Intent,
): RecommendedAllocationItem[] {
  if (funds <= 0 || !opportunities.length) {
    return [];
  }

  const weights = weightsForCount(opportunities.length, intent);
  const count = Math.min(opportunities.length, weights.length);

  const items = opportunities.slice(0, count).map((opportunity, index) => ({
    name: opportunity.name,
    amount: funds * (weights[index] ?? 0),
    reason: opportunity.type,
  }));

  return normalizeAllocationItems(items, funds);
}

export function instrumentPlanWithoutFunds(
  intent: Intent,
  risk: PortfolioRiskLevel,
  portfolio: RecommendationPortfolio = {},
): RecommendedAllocationItem[] {
  return getRecommendations(intent, risk, portfolio).map((recommendation) => ({
    name: recommendation.name,
    amount: 0,
    reason: recommendation.type,
  }));
}

export function getAllocation(
  funds: number,
  intent: Intent,
  risk: PortfolioRiskLevel,
  portfolio: RecommendationPortfolio = {},
): RecommendedAllocationItem[] {
  const opportunities = getOpportunities(intent, risk, portfolio);
  return buildExecutionPlan(opportunities, funds, intent);
}

export function recommendationsToPlanItems(
  recommendations: ReturnType<typeof getRecommendations>,
  amountsByName: Map<string, number> = new Map(),
): RecommendedAllocationItem[] {
  return recommendations.map((recommendation) => ({
    name: recommendation.name,
    amount: amountsByName.get(recommendation.name) ?? 0,
    reason: recommendation.reason,
  }));
}
