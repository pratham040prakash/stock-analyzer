import { safeInvestAmount } from "@/lib/funds";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type { Intent } from "@/types/intent";

export type AllocationItem = {
  label: string;
  amount: number;
};

export function roundAllocationAmount(amount: number): number {
  if (amount <= 0) {
    return 0;
  }

  const step = amount >= 10000 ? 1000 : 500;
  return Math.round(amount / step) * step;
}

function normalizeAllocationItems(
  items: AllocationItem[],
  totalFunds: number,
): AllocationItem[] {
  if (totalFunds <= 0 || items.length === 0) {
    return [];
  }

  const rounded = items.map((item) => ({
    label: item.label,
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
): AllocationItem[] {
  void risk;

  if (funds <= 0) {
    return [];
  }

  if (intent === "grow") {
    return normalizeAllocationItems(
      [
        { label: "ETF", amount: funds * 0.5 },
        { label: "Large Cap", amount: funds * 0.3 },
        { label: "Cash Buffer", amount: funds * 0.2 },
      ],
      funds,
    );
  }

  if (intent === "explore") {
    return normalizeAllocationItems(
      [
        { label: "HDFC Bank", amount: funds * 0.4 },
        { label: "Infosys", amount: funds * 0.3 },
        { label: "Nifty 50 ETF", amount: funds * 0.3 },
      ],
      funds,
    );
  }

  return [];
}
