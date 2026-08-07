import {
  portfolioRiskFromAllocation,
  type PortfolioRiskLevel,
} from "@/lib/portfolioRisk";

export type SellImpact = {
  sellPercent: number;
  currentAllocation: number;
  newAllocation: number;
  currentRisk: PortfolioRiskLevel;
  newRisk: PortfolioRiskLevel;
  cashIncrease: number;
};

export function computeSellImpact(
  allocation: number,
  sellPercent: number,
  totalValue: number,
): SellImpact {
  const newAllocation = Math.round(allocation * (1 - sellPercent / 100));
  const holdingValue = totalValue * (allocation / 100);
  const cashIncrease = holdingValue * (sellPercent / 100);

  return {
    sellPercent,
    currentAllocation: allocation,
    newAllocation,
    currentRisk: portfolioRiskFromAllocation(allocation).risk_level,
    newRisk: portfolioRiskFromAllocation(newAllocation).risk_level,
    cashIncrease,
  };
}

export function formatInr(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Math.round(value));
}
