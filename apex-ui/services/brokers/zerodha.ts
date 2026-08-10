import axios from "axios";
import { brokerError, brokerLog } from "@/lib/broker/log";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import {
  parseZerodhaEquityFunds,
  type ZerodhaEquityFunds,
} from "@/lib/broker/zerodhaFunds";
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
  | ({ status: "OK" } & ZerodhaEquityFunds & {
      /** Deployable CNC balance — alias for marginAvailable. */
      availableCash: number;
    })
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

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

export type FetchQuoteResult =
  | { status: "OK"; lastPrice: number }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export async function fetchZerodhaQuote(
  accessToken: string,
  tradingsymbol: string,
  exchange = "NSE",
): Promise<FetchQuoteResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  try {
    const instrument = `${exchange}:${tradingsymbol}`;
    const res = await axios.get(
      `https://api.kite.trade/quote?i=${encodeURIComponent(instrument)}`,
      {
        headers: kiteAuthHeaders(config.apiKey, accessToken),
      },
    );

    const quote = res.data?.data?.[instrument];
    const lastPrice = quote?.last_price;

    if (typeof lastPrice !== "number" || Number.isNaN(lastPrice) || lastPrice <= 0) {
      return { status: "ERROR", message: "Invalid quote response from Zerodha" };
    }

    return { status: "OK", lastPrice };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    const message =
      err instanceof Error ? err.message : "Failed to fetch Zerodha quote";
    return { status: "ERROR", message };
  }
}

export type PlaceOrderResult =
  | { status: "OK"; orderId: string }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export async function placeZerodhaOrder(
  accessToken: string,
  params: {
    tradingsymbol: string;
    exchange?: string;
    transaction_type: "BUY" | "SELL";
    quantity: number;
    order_type?: "MARKET" | "LIMIT" | "SL-M";
    product?: "CNC" | "MIS";
    price?: number;
    trigger_price?: number;
    validity?: "DAY";
  },
): Promise<PlaceOrderResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  if (params.quantity < 1) {
    return { status: "ERROR", message: "Order quantity must be at least 1" };
  }

  try {
    const form = new URLSearchParams({
      exchange: params.exchange ?? "NSE",
      tradingsymbol: params.tradingsymbol,
      transaction_type: params.transaction_type,
      quantity: String(params.quantity),
      order_type: params.order_type ?? "MARKET",
      product: params.product ?? "CNC",
      validity: params.validity ?? "DAY",
    });

    if (params.price !== undefined && Number.isFinite(params.price)) {
      form.set("price", String(params.price));
    }

    if (
      params.trigger_price !== undefined &&
      Number.isFinite(params.trigger_price)
    ) {
      form.set("trigger_price", String(params.trigger_price));
    }

    const res = await axios.post(
      "https://api.kite.trade/orders/regular",
      form.toString(),
      {
        headers: {
          ...kiteAuthHeaders(config.apiKey, accessToken),
          "Content-Type": "application/x-www-form-urlencoded",
        },
      },
    );

    const orderId = res.data?.data?.order_id;
    if (orderId === undefined || orderId === null || orderId === "") {
      return { status: "ERROR", message: "Invalid order response from Zerodha" };
    }

    return { status: "OK", orderId: String(orderId) };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    const kiteMessage =
      axios.isAxiosError(err) &&
      typeof err.response?.data === "object" &&
      err.response.data !== null &&
      "message" in err.response.data
        ? String((err.response.data as { message?: string }).message)
        : null;

    const message =
      kiteMessage ??
      (err instanceof Error ? err.message : "Failed to place Zerodha order");
    return { status: "ERROR", message };
  }
}

function unwrapKiteEnvelope(body: unknown): unknown {
  if (!body || typeof body !== "object") {
    return body;
  }

  const record = body as Record<string, unknown>;
  if (record.data && typeof record.data === "object") {
    return record.data;
  }

  return body;
}

function extractEquityMargins(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return undefined;
  }

  const record = payload as Record<string, unknown>;
  if (record.equity && typeof record.equity === "object") {
    return record.equity;
  }

  if ("available" in record || "net" in record || "utilised" in record) {
    return record;
  }

  return undefined;
}

function kiteErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const payload = err.response?.data;
    if (payload && typeof payload === "object" && "message" in payload) {
      return String((payload as { message?: string }).message ?? err.message);
    }
    return err.message;
  }

  return err instanceof Error ? err.message : "Failed to fetch Zerodha margins";
}

export async function fetchZerodhaMargins(
  accessToken: string,
): Promise<FetchMarginsResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  const headers = kiteAuthHeaders(config.apiKey, accessToken);

  try {
    const res = await axios.get("https://api.kite.trade/user/margins", { headers });
    const payload = unwrapKiteEnvelope(res.data);
    let funds = parseZerodhaEquityFunds(extractEquityMargins(payload));

    if (!funds) {
      const segmentRes = await axios.get(
        "https://api.kite.trade/user/margins/equity",
        { headers },
      );
      const segmentPayload = unwrapKiteEnvelope(segmentRes.data);
      funds = parseZerodhaEquityFunds(extractEquityMargins(segmentPayload));
    }

    if (!funds) {
      brokerError("Zerodha margins parse failed", {
        payload_keys:
          payload && typeof payload === "object"
            ? Object.keys(payload as Record<string, unknown>)
            : [],
      });
      return { status: "ERROR", message: "Invalid margins response from Zerodha" };
    }

    brokerLog("Zerodha margins parsed", {
      margin_available: funds.marginAvailable,
      ledger_cash: funds.ledgerCash,
      collateral: funds.collateral,
    });

    return {
      status: "OK",
      ...funds,
      availableCash: funds.marginAvailable,
    };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    brokerError("Zerodha margins request failed", {
      message: kiteErrorMessage(err),
      status: axios.isAxiosError(err) ? err.response?.status : undefined,
    });
    return { status: "ERROR", message: kiteErrorMessage(err) };
  }
}
