import type { PortfolioHoldingRow } from "@/types/portfolioApi";
import type { Portfolio } from "@/types/portfolio";
import type { KiteNetPosition } from "@/services/brokers/zerodha";
import { resolvePortfolioDisplayValue } from "@/lib/portfolio/displayValue";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import { computePortfolioDayPnl } from "@/services/brokers/zerodha";

const CONCENTRATION_THRESHOLD = 50;

export { resolvePortfolioDisplayValue, sumPortfolioRowValues } from "@/lib/portfolio/displayValue";

export function formatPortfolioHoldings(
  portfolio: Portfolio,
  dayPositions: KiteNetPosition[] = [],
): {
  holdings: PortfolioHoldingRow[];
  total_value: number;
  total_pnl: number;
  day_pnl: number | null;
  concentrated: boolean;
  top_symbol: string | null;
  top_allocation_pct: number;
  risk_score: number;
  risk_level: import("@/lib/portfolioRisk").PortfolioRiskLevel;
} {
  const rawTotal = portfolio.holdings.reduce(
    (sum, h) => sum + h.quantity * h.currentPrice,
    0,
  );

  const total_pnl = portfolio.holdings.reduce(
    (sum, h) => sum + (h.currentPrice - h.avgPrice) * h.quantity,
    0,
  );

  const holdings: PortfolioHoldingRow[] = portfolio.holdings
    .map((h) => {
      const value = h.quantity * h.currentPrice;
      const pnl = (h.currentPrice - h.avgPrice) * h.quantity;

      return {
        tradingsymbol: h.symbol,
        quantity: h.quantity,
        average_price: h.avgPrice,
        last_price: h.currentPrice,
        pnl,
        value,
        allocation_pct: 0,
      };
    })
    .sort((a, b) => b.value - a.value);

  const total_value = resolvePortfolioDisplayValue(rawTotal, holdings);
  const holdingsWithAllocation = holdings.map((row) => ({
    ...row,
    allocation_pct:
      total_value > 0 ? (Math.max(row.value, 0) / total_value) * 100 : 0,
  }));
  const top = holdingsWithAllocation[0];
  const top_allocation_pct = top?.allocation_pct ?? 0;
  const concentrated = top_allocation_pct > CONCENTRATION_THRESHOLD;
  const { risk_score, risk_level } = portfolioRiskFromAllocation(top_allocation_pct);
  const day_pnl = computePortfolioDayPnl(portfolio, dayPositions);

  return {
    holdings: holdingsWithAllocation,
    total_value,
    total_pnl,
    day_pnl,
    concentrated,
    top_symbol: top?.tradingsymbol ?? null,
    top_allocation_pct,
    risk_score,
    risk_level,
  };
}

export function getTopHoldingSymbol(
  holdings: Portfolio["holdings"],
): { symbol: string; allocationPct: number } | null {
  const formatted = formatPortfolioHoldings({ holdings });
  if (!formatted.top_symbol) return null;
  return {
    symbol: formatted.top_symbol,
    allocationPct: formatted.top_allocation_pct,
  };
}
