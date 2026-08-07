import axios from "axios";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import type { Portfolio } from "@/types/portfolio";

export type KiteHolding = {
  tradingsymbol: string;
  quantity: number;
  average_price: number;
  last_price: number;
};

export type FetchHoldingsResult =
  | { status: "OK"; data: KiteHolding[] }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export function mapKiteHoldingsToPortfolio(holdings: KiteHolding[]): Portfolio {
  return {
    holdings: holdings.map((h) => ({
      symbol: h.tradingsymbol,
      quantity: h.quantity,
      avgPrice: h.average_price,
      currentPrice: h.last_price,
    })),
  };
}

export function computePortfolioMetrics(portfolio: Portfolio): {
  totalValue: number;
  pnl: number;
} {
  const totalValue = portfolio.holdings.reduce(
    (sum, h) => sum + h.quantity * h.currentPrice,
    0,
  );

  const pnl = portfolio.holdings.reduce(
    (sum, h) => sum + (h.currentPrice - h.avgPrice) * h.quantity,
    0,
  );

  return { totalValue, pnl };
}

export async function fetchZerodhaHoldings(
  accessToken: string,
): Promise<FetchHoldingsResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  try {
    const res = await axios.get("https://api.kite.trade/portfolio/holdings", {
      headers: {
        Authorization: `token ${config.apiKey}:${accessToken}`,
        "X-Kite-Version": "3",
      },
    });

    return { status: "OK", data: res.data.data as KiteHolding[] };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    const message =
      err instanceof Error ? err.message : "Failed to fetch Zerodha holdings";
    return { status: "ERROR", message };
  }
}
