import type { PortfolioHoldingRow } from "@/types/portfolioApi";
import type { Portfolio } from "@/types/portfolio";

const CONCENTRATION_THRESHOLD = 50;

export function formatPortfolioHoldings(
  portfolio: Portfolio,
): {
  holdings: PortfolioHoldingRow[];
  total_value: number;
  total_pnl: number;
  concentrated: boolean;
  top_symbol: string | null;
  top_allocation_pct: number;
} {
  const total_value = portfolio.holdings.reduce(
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
      const allocation_pct =
        total_value > 0 ? (value / total_value) * 100 : 0;

      return {
        tradingsymbol: h.symbol,
        quantity: h.quantity,
        average_price: h.avgPrice,
        last_price: h.currentPrice,
        pnl,
        value,
        allocation_pct,
      };
    })
    .sort((a, b) => b.value - a.value);

  const top = holdings[0];
  const top_allocation_pct = top?.allocation_pct ?? 0;
  const concentrated = top_allocation_pct > CONCENTRATION_THRESHOLD;

  return {
    holdings,
    total_value,
    total_pnl,
    concentrated,
    top_symbol: top?.tradingsymbol ?? null,
    top_allocation_pct,
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
