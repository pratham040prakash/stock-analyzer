import axios from "axios";
import { brokerError, brokerLog } from "@/lib/broker/log";
import {
  buildKiteOrderProxyAxiosConfig,
  formatStaticIpOrderError,
  getKiteOrderProxyStatus,
} from "@/lib/broker/kiteOrderProxy";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import {
  parseZerodhaEquityFunds,
  type ZerodhaEquityFunds,
} from "@/lib/broker/zerodhaFunds";
import type { Portfolio } from "@/types/portfolio";
import { normalizeSymbol } from "@/lib/stockPool";

export type KiteHolding = {
  tradingsymbol: string;
  quantity: number;
  /** Same-day purchase qty — not in `quantity` until settled. */
  t1_quantity?: number;
  average_price: number;
  last_price: number;
  close_price?: number;
  day_change?: number;
  /** Daily mark-to-market P&L from Kite positions, when available. */
  m2m?: number;
  /** Unrealised P&L from Kite net positions (LTP − avg). */
  pnl?: number;
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

export function effectiveKiteHoldingQuantity(holding: {
  quantity: number;
  t1_quantity?: number;
}): number {
  const settled = Math.max(0, Math.round(holding.quantity));
  const t1 = Math.max(0, Math.round(holding.t1_quantity ?? 0));
  return settled + t1;
}

export function mapKiteHoldingsToPortfolio(holdings: KiteHolding[]): Portfolio {
  return {
    holdings: holdings.map((h) => ({
      symbol: h.tradingsymbol,
      quantity: h.quantity,
      t1Quantity:
        typeof h.t1_quantity === "number" && Number.isFinite(h.t1_quantity)
          ? h.t1_quantity
          : undefined,
      avgPrice: h.average_price,
      currentPrice: resolveKiteLastPrice(h),
      closePrice:
        typeof h.close_price === "number" && h.close_price > 0
          ? h.close_price
          : undefined,
      dayChange:
        typeof h.day_change === "number" && Number.isFinite(h.day_change)
          ? h.day_change
          : undefined,
      dayM2m:
        typeof h.m2m === "number" && Number.isFinite(h.m2m) ? h.m2m : undefined,
    })),
  };
}

type KitePriceRow = {
  last_price: number;
  close_price?: number;
  day_change?: number;
};

/** Prefer live last_price; derive close+day_change only when LTP missing. */
export function resolveKiteLastPrice(row: KitePriceRow): number {
  if (row.last_price > 0) {
    return row.last_price;
  }

  if (
    typeof row.close_price === "number" &&
    row.close_price > 0 &&
    typeof row.day_change === "number" &&
    Number.isFinite(row.day_change) &&
    row.day_change !== 0
  ) {
    const derived = row.close_price + row.day_change;
    if (derived > 0) {
      return derived;
    }
  }

  return row.last_price;
}

export type KiteNetPosition = {
  tradingsymbol: string;
  product: string;
  quantity: number;
  average_price: number;
  last_price: number;
  close_price?: number;
  day_change?: number;
  m2m?: number;
  pnl?: number;
};

export type FetchNetPositionsResult =
  | { status: "OK"; data: KiteNetPosition[] }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export async function fetchZerodhaNetPositions(
  accessToken: string,
): Promise<FetchNetPositionsResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  try {
    const res = await axios.get("https://api.kite.trade/portfolio/positions", {
      headers: kiteAuthHeaders(config.apiKey, accessToken),
    });
    const net = (res.data?.data?.net ?? []) as KiteNetPosition[];

    return {
      status: "OK",
      data: net.filter(
        (position) => position.product === "CNC" && position.quantity > 0,
      ),
    };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    const message =
      err instanceof Error ? err.message : "Failed to fetch Zerodha positions";
    return { status: "ERROR", message };
  }
}

/** Holdings omit same-day CNC buys until settlement — merge open CNC positions. */
export function mergeKiteHoldingsAndPositions(
  holdings: KiteHolding[],
  positions: KiteNetPosition[],
): KiteHolding[] {
  const merged = new Map<string, KiteHolding>();

  for (const holding of holdings) {
    if (holding.quantity <= 0) {
      continue;
    }

    const symbol = normalizeSymbol(holding.tradingsymbol);
    merged.set(symbol, {
      ...holding,
      last_price: resolveKiteLastPrice(holding),
    });
  }

  for (const position of positions) {
    if (position.product !== "CNC" || position.quantity <= 0) {
      continue;
    }

    const symbol = normalizeSymbol(position.tradingsymbol);
    const positionLast = resolveKiteLastPrice(position);
    const positionDayChange =
      typeof position.day_change === "number" && Number.isFinite(position.day_change)
        ? position.day_change
        : typeof position.close_price === "number" &&
            position.close_price > 0 &&
            positionLast > 0
          ? positionLast - position.close_price
          : undefined;

    if (merged.has(symbol)) {
      const existing = merged.get(symbol)!;
      merged.set(symbol, {
        ...existing,
        average_price:
          position.average_price > 0
            ? position.average_price
            : existing.average_price,
        last_price: positionLast > 0 ? positionLast : existing.last_price,
        close_price: position.close_price ?? existing.close_price,
        day_change: positionDayChange ?? existing.day_change,
        m2m:
          typeof position.m2m === "number" && Number.isFinite(position.m2m)
            ? position.m2m
            : existing.m2m,
        pnl:
          typeof position.pnl === "number" && Number.isFinite(position.pnl)
            ? position.pnl
            : existing.pnl,
      });
      continue;
    }

    merged.set(symbol, {
      tradingsymbol: position.tradingsymbol,
      quantity: position.quantity,
      average_price: position.average_price,
      last_price: positionLast,
      close_price: position.close_price,
      day_change: positionDayChange,
      m2m: position.m2m,
      pnl: position.pnl,
    });
  }

  return [...merged.values()];
}

function effectivePortfolioQuantity(holding: {
  quantity: number;
  t1Quantity?: number;
}): number {
  const settled = Math.max(0, Math.round(holding.quantity));
  const t1 = Math.max(0, Math.round(holding.t1Quantity ?? 0));
  return settled + t1;
}

/** Align with Zerodha: position m2m when present, else day_change × (qty + t1). */
export function computePortfolioDayPnl(portfolio: Portfolio): number | null {
  let total = 0;
  let hasDayData = false;

  for (const h of portfolio.holdings) {
    const qty = effectivePortfolioQuantity(h);
    if (qty <= 0) {
      continue;
    }

    if (h.dayM2m !== undefined && Number.isFinite(h.dayM2m)) {
      hasDayData = true;
      total += h.dayM2m;
      continue;
    }

    if (h.dayChange !== undefined && Number.isFinite(h.dayChange)) {
      hasDayData = true;
      total += h.dayChange * qty;
      continue;
    }

    if (h.closePrice !== undefined && h.closePrice > 0) {
      hasDayData = true;
      total += (h.currentPrice - h.closePrice) * qty;
    }
  }

  return hasDayData ? Math.round(total * 10) / 10 : null;
}

export function runKiteDayPnlSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Kite Day P&L self-check failed: ${message}`);
    }
  };

  const t1Only = computePortfolioDayPnl(
    mapKiteHoldingsToPortfolio([
      {
        tradingsymbol: "TITAN",
        quantity: 0,
        t1_quantity: 2,
        average_price: 3500,
        last_price: 3520,
        close_price: 3510,
        day_change: 10,
      },
    ]),
  );
  assert(t1Only === 20, "T1 quantity must count toward Day P&L");

  const merged = mergeKiteHoldingsAndPositions(
    [
      {
        tradingsymbol: "HEROMOTOCO",
        quantity: 1,
        average_price: 5000,
        last_price: 5100,
        close_price: 5050,
        day_change: 50,
      },
    ],
    [
      {
        tradingsymbol: "HEROMOTOCO",
        product: "CNC",
        quantity: 1,
        average_price: 5000,
        last_price: 5100,
        close_price: 5050,
        m2m: 48.5,
      },
    ],
  );
  assert(merged[0]?.m2m === 48.5, "Merged holding must inherit net position m2m");

  const fromM2m = computePortfolioDayPnl(mapKiteHoldingsToPortfolio(merged));
  assert(fromM2m === 48.5, "Day P&L must prefer broker m2m over day_change");

  const overlaid = mergeKiteHoldingsAndPositions(
    [
      {
        tradingsymbol: "HEROMOTOCO",
        quantity: 1,
        average_price: 5856.1,
        last_price: 5801.4,
        close_price: 5800,
        day_change: 1.4,
      },
    ],
    [
      {
        tradingsymbol: "HEROMOTOCO",
        product: "CNC",
        quantity: 1,
        average_price: 5856.1,
        last_price: 5860,
        close_price: 5800,
        pnl: 3.9,
      },
    ],
  );
  assert(
    overlaid[0]?.last_price === 5860 && overlaid[0]?.pnl === 3.9,
    "Merged holding must prefer live CNC position LTP and pnl over stale holdings",
  );

  const dayChangeOnly = computePortfolioDayPnl(
    mapKiteHoldingsToPortfolio([
      {
        tradingsymbol: "RELIANCE",
        quantity: 3,
        average_price: 1400,
        last_price: 1410,
        close_price: 1400,
        day_change: 10,
      },
    ]),
  );
  assert(dayChangeOnly === 30, "Day P&L must use day_change × effective quantity");
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

export type ZerodhaLiveQuote = {
  lastPrice: number;
  previousClose: number | null;
};

function parseKiteQuotePayload(payload: unknown): ZerodhaLiveQuote | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const record = payload as {
    last_price?: number;
    ohlc?: { close?: number };
  };
  const lastPrice = record.last_price;

  if (typeof lastPrice !== "number" || Number.isNaN(lastPrice) || lastPrice <= 0) {
    return null;
  }

  const previousClose = record.ohlc?.close;
  return {
    lastPrice,
    previousClose:
      typeof previousClose === "number" &&
      Number.isFinite(previousClose) &&
      previousClose > 0
        ? previousClose
        : null,
  };
}

function buildInstrumentQuery(
  symbols: string[],
  exchange: string,
): string {
  return symbols
    .map((symbol) => {
      const instrument = `${exchange}:${symbol}`;
      return `i=${encodeURIComponent(instrument)}`;
    })
    .join("&");
}

async function fetchZerodhaLtpOhlcBatch(
  accessToken: string,
  symbols: string[],
  exchange: string,
  quotes: Map<string, ZerodhaLiveQuote>,
): Promise<void> {
  if (symbols.length === 0) {
    return;
  }

  const config = getZerodhaConfig();
  if (!config.configured) {
    return;
  }

  const query = buildInstrumentQuery(symbols, exchange);
  const headers = kiteAuthHeaders(config.apiKey, accessToken);

  try {
    const [ltpRes, ohlcRes] = await Promise.all([
      axios.get(`https://api.kite.trade/quote/ltp?${query}`, { headers }),
      axios.get(`https://api.kite.trade/quote/ohlc?${query}`, { headers }),
    ]);

    for (const symbol of symbols) {
      const instrument = `${exchange}:${symbol}`;
      const lastPrice = (
        ltpRes.data?.data?.[instrument] as { last_price?: number } | undefined
      )?.last_price;
      const previousClose = (
        ohlcRes.data?.data?.[instrument] as
          | { ohlc?: { close?: number } }
          | undefined
      )?.ohlc?.close;

      if (
        typeof lastPrice !== "number" ||
        Number.isNaN(lastPrice) ||
        lastPrice <= 0
      ) {
        continue;
      }

      quotes.set(symbol, {
        lastPrice,
        previousClose:
          typeof previousClose === "number" &&
          Number.isFinite(previousClose) &&
          previousClose > 0
            ? previousClose
            : null,
      });
    }
  } catch (err) {
    brokerError(
      "fetchZerodhaLtpOhlcBatch failed",
      err instanceof Error ? err.message : err,
    );
  }
}

async function fetchZerodhaLiveQuote(
  accessToken: string,
  tradingsymbol: string,
  exchange = "NSE",
): Promise<ZerodhaLiveQuote | null> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return null;
  }

  const instrument = `${exchange}:${tradingsymbol}`;
  const headers = kiteAuthHeaders(config.apiKey, accessToken);

  try {
    const res = await axios.get(
      `https://api.kite.trade/quote?i=${encodeURIComponent(instrument)}`,
      { headers },
    );

    const parsed = parseKiteQuotePayload(res.data?.data?.[instrument]);
    if (parsed) {
      return parsed;
    }
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return null;
    }

    brokerError(
      `fetchZerodhaLiveQuote failed for ${tradingsymbol}`,
      err instanceof Error ? err.message : err,
    );
  }

  const fallback = new Map<string, ZerodhaLiveQuote>();
  await fetchZerodhaLtpOhlcBatch(
    accessToken,
    [tradingsymbol],
    exchange,
    fallback,
  );
  return fallback.get(tradingsymbol) ?? null;
}

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
    const quote = await fetchZerodhaLiveQuote(accessToken, tradingsymbol, exchange);

    if (!quote) {
      return { status: "ERROR", message: "Invalid quote response from Zerodha" };
    }

    return { status: "OK", lastPrice: quote.lastPrice };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    const message =
      err instanceof Error ? err.message : "Failed to fetch Zerodha quote";
    return { status: "ERROR", message };
  }
}

/** Live LTP (+ prior close) for multiple NSE symbols; falls back per symbol on batch miss. */
export async function fetchZerodhaQuotes(
  accessToken: string,
  tradingsymbols: string[],
  exchange = "NSE",
): Promise<Map<string, ZerodhaLiveQuote>> {
  const quotes = new Map<string, ZerodhaLiveQuote>();
  const symbols = [
    ...new Set(
      tradingsymbols.map((symbol) => normalizeSymbol(symbol)).filter(Boolean),
    ),
  ];

  if (symbols.length === 0) {
    return quotes;
  }

  const config = getZerodhaConfig();

  if (!config.configured) {
    return quotes;
  }

  try {
    const query = buildInstrumentQuery(symbols, exchange);
    const res = await axios.get(`https://api.kite.trade/quote?${query}`, {
      headers: kiteAuthHeaders(config.apiKey, accessToken),
    });

    for (const symbol of symbols) {
      const instrument = `${exchange}:${symbol}`;
      const parsed = parseKiteQuotePayload(res.data?.data?.[instrument]);
      if (parsed) {
        quotes.set(symbol, parsed);
      }
    }
  } catch (err) {
    brokerError(
      "fetchZerodhaQuotes batch failed",
      err instanceof Error ? err.message : err,
    );
  }

  const missingAfterFull = symbols.filter((symbol) => !quotes.has(symbol));
  if (missingAfterFull.length > 0) {
    await fetchZerodhaLtpOhlcBatch(
      accessToken,
      missingAfterFull,
      exchange,
      quotes,
    );
  }

  for (const symbol of symbols) {
    if (quotes.has(symbol)) {
      continue;
    }

    const parsed = await fetchZerodhaLiveQuote(accessToken, symbol, exchange);
    if (parsed) {
      quotes.set(symbol, parsed);
    }
  }

  return quotes;
}

export type PlaceOrderResult =
  | { status: "OK"; orderId: string }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export type KiteTrade = {
  trade_id: string;
  order_id: string;
  tradingsymbol: string;
  transaction_type: "BUY" | "SELL" | string;
  quantity: number;
  average_price: number;
  fill_timestamp: string;
};

export type FetchTradesResult =
  | { status: "OK"; data: KiteTrade[] }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export async function fetchZerodhaTrades(
  accessToken: string,
): Promise<FetchTradesResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  try {
    const res = await axios.get("https://api.kite.trade/trades", {
      headers: kiteAuthHeaders(config.apiKey, accessToken),
    });

    const data = res.data?.data;
    if (!Array.isArray(data)) {
      return { status: "ERROR", message: "Invalid trades response from Zerodha" };
    }

    return { status: "OK", data: data as KiteTrade[] };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    return { status: "ERROR", message: kiteErrorMessage(err) };
  }
}

export type KiteOrder = {
  order_id: string;
  tradingsymbol: string;
  transaction_type: "BUY" | "SELL" | string;
  status: string;
  quantity: number;
  filled_quantity: number;
  average_price: number;
  order_timestamp: string;
};

export type FetchOrdersResult =
  | { status: "OK"; data: KiteOrder[] }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export async function fetchZerodhaOrders(
  accessToken: string,
): Promise<FetchOrdersResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  try {
    const res = await axios.get("https://api.kite.trade/orders", {
      headers: kiteAuthHeaders(config.apiKey, accessToken),
    });

    const data = res.data?.data;
    if (!Array.isArray(data)) {
      return { status: "ERROR", message: "Invalid orders response from Zerodha" };
    }

    return { status: "OK", data: data as KiteOrder[] };
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return { status: "TOKEN_EXPIRED" };
    }

    return { status: "ERROR", message: kiteErrorMessage(err) };
  }
}

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

  const proxyStatus = getKiteOrderProxyStatus();
  const requireProxy =
    process.env.VERCEL === "1" || process.env.NODE_ENV === "production";

  if (requireProxy && !proxyStatus.configured) {
    return {
      status: "ERROR",
      message:
        "Order proxy is not configured. Set KITE_ORDER_PROXY_URL to your Oracle VM and whitelist that IP in the Kite developer console.",
    };
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
        ...buildKiteOrderProxyAxiosConfig(),
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

    const message = formatStaticIpOrderError(
      kiteMessage ??
        (err instanceof Error ? err.message : "Failed to place Zerodha order"),
    );
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
