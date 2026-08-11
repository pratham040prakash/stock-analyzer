import type { PortfolioHoldingRow } from "@/types/portfolioApi";
import type { Portfolio, Holding } from "@/types/portfolio";
import type { KiteNetPosition } from "@/services/brokers/zerodha";
import { resolveHoldingDisplayQuantity } from "@/services/brokers/zerodha";
import { resolvePortfolioDisplayValue } from "@/lib/portfolio/displayValue";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import { computePortfolioDayPnl } from "@/services/brokers/zerodha";

const CONCENTRATION_THRESHOLD = 50;

export { resolvePortfolioDisplayValue, sumPortfolioRowValues } from "@/lib/portfolio/displayValue";

function readFiniteNumber(value: unknown): number | undefined {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

/** Normalize legacy snapshot JSON (symbol or tradingsymbol keys). */
export function snapshotHoldingsToPortfolio(holdings: unknown): Portfolio {
  if (!Array.isArray(holdings)) {
    return { holdings: [] };
  }

  const rows: Holding[] = [];

  for (const raw of holdings) {
    if (!raw || typeof raw !== "object") {
      continue;
    }

    const row = raw as Record<string, unknown>;
    const symbol = String(row.symbol ?? row.tradingsymbol ?? "").trim();
    if (!symbol) {
      continue;
    }

    const settled = Math.max(0, Math.round(readFiniteNumber(row.quantity) ?? 0));
    const t1 = Math.max(
      0,
      Math.round(readFiniteNumber(row.t1Quantity ?? row.t1_quantity) ?? 0),
    );
    const quantity = resolveHoldingDisplayQuantity({
      quantity: settled,
      t1Quantity: t1 > 0 ? t1 : undefined,
    });
    const avgPrice = readFiniteNumber(row.avgPrice ?? row.average_price) ?? 0;
    const currentPrice =
      readFiniteNumber(row.currentPrice ?? row.last_price) ?? 0;

    rows.push({
      symbol,
      quantity,
      t1Quantity: undefined,
      avgPrice,
      currentPrice,
      closePrice: readFiniteNumber(row.closePrice ?? row.close_price),
      dayChange: readFiniteNumber(row.dayChange ?? row.day_change),
      dayM2m: readFiniteNumber(row.dayM2m ?? row.m2m),
    });
  }

  return { holdings: rows };
}

function holdingRowQuantity(holding: Portfolio["holdings"][number]): number {
  return resolveHoldingDisplayQuantity(holding);
}

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
    (sum, h) => sum + holdingRowQuantity(h) * h.currentPrice,
    0,
  );

  const total_pnl = portfolio.holdings.reduce(
    (sum, h) => sum + (h.currentPrice - h.avgPrice) * holdingRowQuantity(h),
    0,
  );

  const holdings: PortfolioHoldingRow[] = portfolio.holdings
    .map((h) => {
      const quantity = holdingRowQuantity(h);
      const value = quantity * h.currentPrice;
      const pnl = (h.currentPrice - h.avgPrice) * quantity;

      return {
        tradingsymbol: h.symbol,
        quantity,
        average_price: h.avgPrice,
        last_price: h.currentPrice,
        pnl,
        value,
        allocation_pct: 0,
      };
    })
    .filter((row) => row.quantity > 0)
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
