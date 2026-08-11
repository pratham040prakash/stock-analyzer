import type { PortfolioHoldingRow } from "@/types/portfolioApi";
import type { Portfolio } from "@/types/portfolio";

const DEMO_PORTFOLIO_SYMBOLS = ["TCS", "INFY", "HDFC"] as const;

function holdingSymbol(holding: {
  symbol?: string;
  tradingsymbol?: string;
}): string {
  return (holding.tradingsymbol ?? holding.symbol ?? "").trim().toUpperCase();
}

/** Placeholder portfolio used only for unconfigured demo mode — never real Zerodha data. */
export function isDemoPortfolioHoldings(
  holdings: { symbol?: string; tradingsymbol?: string }[],
): boolean {
  if (holdings.length !== DEMO_PORTFOLIO_SYMBOLS.length) {
    return false;
  }

  const symbols = new Set(holdings.map((holding) => holdingSymbol(holding)));
  return DEMO_PORTFOLIO_SYMBOLS.every((symbol) => symbols.has(symbol));
}

export function filterRealPortfolioHoldings<
  T extends { symbol?: string; tradingsymbol?: string },
>(holdings: T[]): T[] {
  if (isDemoPortfolioHoldings(holdings)) {
    return [];
  }

  return holdings;
}

export function filterRealPortfolio(portfolio: Portfolio): Portfolio {
  return {
    holdings: filterRealPortfolioHoldings(portfolio.holdings),
  };
}

export function sumPortfolioRowValues(
  holdings: Pick<PortfolioHoldingRow, "value" | "quantity" | "last_price">[],
): number {
  return holdings.reduce((sum, row) => {
    if (row.value > 0) {
      return sum + row.value;
    }

    if (row.quantity > 0 && row.last_price > 0) {
      return sum + row.quantity * row.last_price;
    }

    return sum;
  }, 0);
}

/** Prefer row sums — API `total_value: 0` is common pre-open when LTP is missing. */
export function resolvePortfolioDisplayValue(
  totalValue: number | null | undefined,
  holdings: Pick<PortfolioHoldingRow, "value" | "quantity" | "last_price">[],
): number {
  const rowSum = sumPortfolioRowValues(holdings);
  if (rowSum > 0) {
    return rowSum;
  }

  if (typeof totalValue === "number" && Number.isFinite(totalValue)) {
    return Math.max(0, totalValue);
  }

  return 0;
}
