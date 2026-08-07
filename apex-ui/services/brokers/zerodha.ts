import axios from "axios";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import type { Portfolio } from "@/types/portfolio";

export type KiteHolding = {
  tradingsymbol: string;
  quantity: number;
  average_price: number;
  last_price: number;
  close_price?: number;
};

export type FetchHoldingsResult =
  | { status: "OK"; data: KiteHolding[] }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export type FetchMarginsResult =
  | { status: "OK"; availableCash: number }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

type KiteMarginsResponse = {
  data?: {
    equity?: {
      available?: {
        cash?: number;
      };
    };
  };
};

export function mapKiteHoldingsToPortfolio(holdings: KiteHolding[]): Portfolio {
  return {
    holdings: holdings.map((h) => ({
      symbol: h.tradingsymbol,
      quantity: h.quantity,
      avgPrice: h.average_price,
      currentPrice: h.last_price,
      closePrice:
        typeof h.close_price === "number" && h.close_price > 0
          ? h.close_price
          : undefined,
    })),
  };
}

export function computePortfolioDayPnl(portfolio: Portfolio): number | null {
  let total = 0;
  let hasDayData = false;

  for (const h of portfolio.holdings) {
    if (h.closePrice === undefined) {
      continue;
    }
    hasDayData = true;
    total += (h.currentPrice - h.closePrice) * h.quantity;
  }

  return hasDayData ? total : null;
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
      headers: kiteAuthHeaders(config.apiKey, accessToken),
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

function kiteAuthHeaders(apiKey: string, accessToken: string) {
  return {
    Authorization: `token ${apiKey}:${accessToken}`,
    "X-Kite-Version": "3",
  };
}

export async function fetchZerodhaMargins(
  accessToken: string,
): Promise<FetchMarginsResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  try {
    const res = await axios.get<KiteMarginsResponse>(
      "https://api.kite.trade/user/margins",
      {
        headers: kiteAuthHeaders(config.apiKey, accessToken),
      },
    );

    const cash = res.data?.data?.equity?.available?.cash;
    if (typeof cash !== "number" || Number.isNaN(cash)) {
      return { status: "ERROR", message: "Invalid margins response from Zerodha" };
    }

    return { status: "OK", availableCash: Math.max(0, Math.round(cash)) };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    const message =
      err instanceof Error ? err.message : "Failed to fetch Zerodha margins";
    return { status: "ERROR", message };
  }
}
