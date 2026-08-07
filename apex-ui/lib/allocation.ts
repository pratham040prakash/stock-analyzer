import { safeInvestAmount } from "@/lib/funds";
import { getOpportunities } from "@/lib/recommendations";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type {
  DecisionOpportunity,
  RecommendedAllocationItem,
} from "@/types/decision";
import type { Intent } from "@/types/intent";

const ALLOCATION_WEIGHTS: Partial<Record<Intent, number[]>> = {
  grow: [0.6, 0.4],
  explore: [0.4, 0.3, 0.3],
};

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

export function instrumentPlanWithoutFunds(
  intent: Intent,
  risk: PortfolioRiskLevel,
): RecommendedAllocationItem[] {
  return getOpportunities(intent, risk).map((opportunity) => ({
    name: opportunity.name,
    amount: 0,
    reason: opportunity.type,
  }));
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
  const weights = ALLOCATION_WEIGHTS[intent];

  if (funds <= 0 || !weights?.length || !opportunities.length) {
    return [];
  }

  const items = opportunities.map((opportunity, index) => ({
    name: opportunity.name,
    amount: funds * (weights[index] ?? 0),
    reason: opportunity.type,
  }));

  return normalizeAllocationItems(items, funds);
}

export function getAllocation(
  funds: number,
  intent: Intent,
  risk: PortfolioRiskLevel,
): RecommendedAllocationItem[] {
  const opportunities = getOpportunities(intent, risk);
  return buildExecutionPlan(opportunities, funds, intent);
}
