import { normalizeSymbol } from "@/lib/stockPool";
import type { PortfolioHoldingRow } from "@/types/portfolioApi";

export type JourneyLiveQuote = {
  currentPriceInr: number;
  quantity: number;
};

export function buildJourneyPriceMap(
  holdings: PortfolioHoldingRow[],
): Map<string, JourneyLiveQuote> {
  const map = new Map<string, JourneyLiveQuote>();

  for (const holding of holdings) {
    if (!Number.isFinite(holding.last_price) || holding.last_price <= 0) {
      continue;
    }

    const symbol = normalizeSymbol(holding.tradingsymbol);
    if (!symbol) {
      continue;
    }

    map.set(symbol, {
      currentPriceInr: Math.round(holding.last_price),
      quantity: holding.quantity,
    });
  }

  return map;
}

export function lookupJourneyLiveQuote(
  priceMap: Map<string, JourneyLiveQuote>,
  symbol: string,
): JourneyLiveQuote | undefined {
  return priceMap.get(normalizeSymbol(symbol));
}

export function runJourneyPriceMapSelfCheck(): void {
  const map = buildJourneyPriceMap([
    {
      tradingsymbol: "RELIANCE",
      quantity: 5,
      average_price: 2500,
      last_price: 2550.4,
      pnl: 250,
      value: 12752,
      allocation_pct: 40,
    },
  ]);

  const quote = lookupJourneyLiveQuote(map, "reliance");
  if (!quote || quote.currentPriceInr !== 2550 || quote.quantity !== 5) {
    throw new Error("Journey price map self-check failed");
  }
}
