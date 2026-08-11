import type { PortfolioHoldingRow } from "@/types/portfolioApi";

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
