import axios from "axios";
import { brokerError, brokerLog } from "@/lib/broker/log";
import {
  buildKiteAxiosConfig,
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

export function effectivePortfolioQuantity(holding: {
  quantity: number;
  t1Quantity?: number;
}): number {
  const settled = Math.max(0, Math.round(holding.quantity));
  const t1 = Math.max(0, Math.round(holding.t1Quantity ?? 0));
  return settled + t1;
}

export function mapKiteHoldingsToPortfolio(holdings: KiteHolding[]): Portfolio {
  return {
    holdings: holdings.map((h) => ({
      symbol: h.tradingsymbol,
      quantity: effectiveKiteHoldingQuantity(h),
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

  // Pre-open / illiquid — Kite may return last_price 0; use prior close for valuation.
  if (typeof row.close_price === "number" && row.close_price > 0) {
    return row.close_price;
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
  realised?: number;
  unrealised?: number;
  /** Set when last_price came from a live /quote batch. */
  ltpFromQuote?: boolean;
};

export type FetchNetPositionsResult =
  | { status: "OK"; data: KiteNetPosition[] }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export type FetchCncPositionsResult =
  | {
      status: "OK";
      /** Open CNC legs only — merged into holdings for portfolio value. */
      net: KiteNetPosition[];
      /** All CNC net legs with qty ≠ 0 — Positions tab P&L (incl. sold qty). */
      netPnl: KiteNetPosition[];
      day: KiteNetPosition[];
    }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

function isCncProduct(product: string | undefined): boolean {
  return (product ?? "").trim().toUpperCase() === "CNC";
}

function readFiniteNumber(value: unknown): number | undefined {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function normalizeKiteNetPosition(raw: unknown): KiteNetPosition | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }

  const row = raw as Record<string, unknown>;
  const tradingsymbol =
    typeof row.tradingsymbol === "string" ? row.tradingsymbol : "";
  const quantity = readFiniteNumber(row.quantity);

  if (!tradingsymbol || quantity === undefined || quantity === 0) {
    return null;
  }

  const pnl = readFiniteNumber(row.pnl);
  const unrealised = readFiniteNumber(row.unrealised);

  return {
    tradingsymbol,
    product: typeof row.product === "string" ? row.product : "CNC",
    quantity,
    average_price: readFiniteNumber(row.average_price) ?? 0,
    last_price: readFiniteNumber(row.last_price) ?? 0,
    close_price: readFiniteNumber(row.close_price),
    day_change: readFiniteNumber(row.day_change),
    m2m: readFiniteNumber(row.m2m),
    pnl: pnl ?? unrealised,
    unrealised,
    realised: readFiniteNumber(row.realised),
  };
}

function parseKiteNetPositions(raw: unknown): KiteNetPosition[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((row) => normalizeKiteNetPosition(row))
    .filter((row): row is KiteNetPosition => row !== null);
}

function filterOpenCncNetPositions(net: KiteNetPosition[]): KiteNetPosition[] {
  return net.filter(
    (position) => isCncProduct(position.product) && position.quantity > 0,
  );
}

/** All CNC net rows with qty ≠ 0 — includes sold legs (e.g. JIOFIN −1). */
export function filterCncNetPositionsForPnl(
  net: KiteNetPosition[],
): KiteNetPosition[] {
  return net.filter(
    (position) => isCncProduct(position.product) && position.quantity !== 0,
  );
}

function filterCncDayPositions(day: KiteNetPosition[]): KiteNetPosition[] {
  return day.filter((position) => isCncProduct(position.product));
}

function roundPnl(value: number): number {
  return Math.round(value * 10) / 10;
}

export type ZerodhaPositionPnlRow = {
  symbol: string;
  quantity: number;
  average_price: number;
  last_price: number;
  pnl: number;
  live_quote?: boolean;
  ltp_source?: "quote" | "kite";
};

function netPositionRowPnl(position: KiteNetPosition, ltp: number): number {
  const fromLtp = roundPnl((ltp - position.average_price) * position.quantity);

  if (position.ltpFromQuote) {
    return fromLtp;
  }

  if (typeof position.pnl === "number" && Number.isFinite(position.pnl)) {
    return roundPnl(position.pnl);
  }

  return fromLtp;
}

/** Sum of raw Kite net CNC `pnl` before any LTP recalc. */
export function sumNativeKiteNetCncPnl(
  netPositions: KiteNetPosition[],
): number | null {
  let total = 0;
  let hasRow = false;

  for (const position of netPositions) {
    if (!isCncProduct(position.product) || position.quantity === 0) {
      continue;
    }

    if (typeof position.pnl !== "number" || !Number.isFinite(position.pnl)) {
      continue;
    }

    hasRow = true;
    total += position.pnl;
  }

  return hasRow ? roundPnl(total) : null;
}

/** Sum of Kite net CNC `pnl` — same field as Zerodha Positions tab. */
export function sumKiteNetCncPositionPnl(
  netPositions: KiteNetPosition[],
): number | null {
  let total = 0;
  let hasRow = false;

  for (const position of netPositions) {
    if (!isCncProduct(position.product) || position.quantity === 0) {
      continue;
    }

    hasRow = true;
    const ltp = resolveKiteLastPrice(position);
    total += netPositionRowPnl(position, ltp);
  }

  return hasRow ? roundPnl(total) : null;
}

/** Per-symbol rows matching Zerodha Positions tab — net CNC legs only. */
export function computeZerodhaPositionsBreakdown(
  _holdings: KiteHolding[],
  netPositions: KiteNetPosition[],
): ZerodhaPositionPnlRow[] {
  const rows: ZerodhaPositionPnlRow[] = [];

  for (const position of netPositions) {
    if (!isCncProduct(position.product) || position.quantity === 0) {
      continue;
    }

    const symbol = normalizeSymbol(position.tradingsymbol);
    if (!symbol) {
      continue;
    }

    const ltp = resolveKiteLastPrice(position);
    rows.push({
      symbol,
      quantity: position.quantity,
      average_price: position.average_price,
      last_price: ltp,
      pnl: netPositionRowPnl(position, ltp),
      live_quote: position.ltpFromQuote === true,
      ltp_source: position.ltpFromQuote ? "quote" : "kite",
    });
  }

  rows.sort((left, right) => left.symbol.localeCompare(right.symbol));
  return rows;
}

/** Matches Zerodha Positions tab total P&L. */
export function computeZerodhaPositionsPnl(
  holdings: KiteHolding[],
  netPositions: KiteNetPosition[],
): number | null {
  const fromNet = sumKiteNetCncPositionPnl(netPositions);
  if (fromNet !== null) {
    return fromNet;
  }

  const rows = computeZerodhaPositionsBreakdown(holdings, netPositions);
  if (rows.length === 0) {
    return null;
  }

  return roundPnl(rows.reduce((sum, row) => sum + row.pnl, 0));
}

export async function fetchZerodhaCncPositions(
  accessToken: string,
): Promise<FetchCncPositionsResult> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return { status: "ERROR", message: "Zerodha is not configured" };
  }

  try {
    const res = await axios.get("https://api.kite.trade/portfolio/positions", {
      ...kiteReadRequestConfig(config.apiKey, accessToken),
    });
    const net = parseKiteNetPositions(res.data?.data?.net);
    const day = parseKiteNetPositions(res.data?.data?.day);

    return {
      status: "OK",
      net: filterOpenCncNetPositions(net),
      netPnl: filterCncNetPositionsForPnl(net),
      day: filterCncDayPositions(day),
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

export async function fetchZerodhaNetPositions(
  accessToken: string,
): Promise<FetchNetPositionsResult> {
  const result = await fetchZerodhaCncPositions(accessToken);

  if (result.status !== "OK") {
    return result;
  }

  return { status: "OK", data: result.net };
}

/** Holdings omit same-day CNC buys until settlement — merge open CNC positions. */
export function mergeKiteHoldingsAndPositions(
  holdings: KiteHolding[],
  positions: KiteNetPosition[],
): KiteHolding[] {
  const merged = new Map<string, KiteHolding>();

  for (const holding of holdings) {
    const effectiveQty = effectiveKiteHoldingQuantity(holding);
    if (effectiveQty <= 0) {
      continue;
    }

    const symbol = normalizeSymbol(holding.tradingsymbol);
    merged.set(symbol, {
      ...holding,
      quantity: effectiveQty,
      last_price: resolveKiteLastPrice(holding),
    });
  }

  for (const position of positions) {
    if (!isCncProduct(position.product) || position.quantity <= 0) {
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
        quantity: Math.max(existing.quantity, position.quantity),
        average_price:
          position.average_price > 0
            ? position.average_price
            : existing.average_price,
        // Holdings LTP is usually fresher than net position last_price.
        last_price:
          existing.last_price > 0
            ? existing.last_price
            : positionLast > 0
              ? positionLast
              : existing.last_price,
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

/** Repair snapshot rows with prices but missing/zero qty using open CNC legs. */
export function enrichPortfolioQuantitiesFromNetPositions(
  portfolio: Portfolio,
  netPnlPositions: KiteNetPosition[],
): Portfolio {
  const longQtyBySymbol = new Map<string, number>();

  for (const position of netPnlPositions) {
    if (!isCncProduct(position.product) || position.quantity <= 0) {
      continue;
    }

    const symbol = normalizeSymbol(position.tradingsymbol);
    longQtyBySymbol.set(
      symbol,
      Math.max(longQtyBySymbol.get(symbol) ?? 0, position.quantity),
    );
  }

  const holdings = portfolio.holdings
    .map((holding) => {
      const effectiveQty = effectivePortfolioQuantity(holding);
      if (effectiveQty > 0) {
        return { ...holding, quantity: effectiveQty };
      }

      const fromPosition = longQtyBySymbol.get(normalizeSymbol(holding.symbol));
      if (fromPosition && fromPosition > 0) {
        return { ...holding, quantity: fromPosition };
      }

      return holding;
    })
    .filter((holding) => holding.quantity > 0 && holding.symbol.trim().length > 0);

  return { holdings };
}

function contributionFromDayPosition(position: KiteNetPosition): number | null {
  if (typeof position.m2m === "number" && Number.isFinite(position.m2m)) {
    return position.m2m;
  }

  const realised =
    typeof position.realised === "number" && Number.isFinite(position.realised)
      ? position.realised
      : 0;
  const unrealised =
    typeof position.unrealised === "number" &&
    Number.isFinite(position.unrealised)
      ? position.unrealised
      : 0;

  if (realised !== 0 || unrealised !== 0) {
    return realised + unrealised;
  }

  if (typeof position.pnl === "number" && Number.isFinite(position.pnl)) {
    return position.pnl;
  }

  if (
    typeof position.day_change === "number" &&
    Number.isFinite(position.day_change) &&
    position.quantity !== 0
  ) {
    return position.day_change * Math.abs(position.quantity);
  }

  return null;
}

/** Align with Zerodha dashboard: day-bucket m2m + overnight holdings not traded today. */
export function computePortfolioDayPnl(
  portfolio: Portfolio,
  dayPositions: KiteNetPosition[] = [],
): number | null {
  let total = 0;
  let hasDayData = false;
  const tradedToday = new Set<string>();

  for (const position of dayPositions) {
    if (!isCncProduct(position.product)) {
      continue;
    }

    const symbol = normalizeSymbol(position.tradingsymbol);
    if (!symbol) {
      continue;
    }

    tradedToday.add(symbol);
    const contribution = contributionFromDayPosition(position);

    if (contribution !== null) {
      hasDayData = true;
      total += contribution;
    }
  }

  for (const h of portfolio.holdings) {
    const symbol = normalizeSymbol(h.symbol);
    if (tradedToday.has(symbol)) {
      continue;
    }

    const qty = effectivePortfolioQuantity(h);
    if (qty <= 0) {
      continue;
    }

    if (h.closePrice !== undefined && h.closePrice > 0 && h.currentPrice > 0) {
      hasDayData = true;
      total += (h.currentPrice - h.closePrice) * qty;
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
  assert(fromM2m === 50, "Day P&L must use live LTP vs prior close for overnight holdings");

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
    overlaid[0]?.last_price === 5801.4,
    "Merged holding must keep holdings LTP over stale CNC position last_price",
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

  const withClosedTrade = computePortfolioDayPnl(
    mapKiteHoldingsToPortfolio([
      {
        tradingsymbol: "GRASIM",
        quantity: 1,
        average_price: 3393,
        last_price: 3380,
        close_price: 3393,
        day_change: -13,
      },
    ]),
    [
      {
        tradingsymbol: "JIOFIN",
        product: "CNC",
        quantity: 0,
        average_price: 0,
        last_price: 300,
        m2m: -75,
      },
      {
        tradingsymbol: "TITAN",
        product: "CNC",
        quantity: 1,
        average_price: 5058.7,
        last_price: 5090,
        m2m: 31.3,
      },
    ],
  );
  assert(
    withClosedTrade !== null && Math.abs(withClosedTrade - (-56.7)) < 0.01,
    "Day P&L must include day-bucket closed trades and skip double-counting traded symbols in holdings",
  );

  const positionsPnl = computeZerodhaPositionsPnl([
    {
      tradingsymbol: "GRASIM",
      quantity: 1,
      average_price: 3393.3,
      last_price: 3380.5,
    },
    {
      tradingsymbol: "HEROMOTOCO",
      quantity: 1,
      average_price: 5856.1,
      last_price: 5860,
    },
    {
      tradingsymbol: "JIOFIN",
      quantity: -1,
      average_price: 255.9,
      last_price: 254,
    },
    {
      tradingsymbol: "TITAN",
      quantity: 1,
      average_price: 5058.7,
      last_price: 5090,
    },
  ], [
    {
      tradingsymbol: "GRASIM",
      product: "CNC",
      quantity: 1,
      average_price: 3393.3,
      last_price: 3380.5,
    },
    {
      tradingsymbol: "HEROMOTOCO",
      product: "CNC",
      quantity: 1,
      average_price: 5856.1,
      last_price: 5860,
    },
    {
      tradingsymbol: "JIOFIN",
      product: "CNC",
      quantity: -1,
      average_price: 255.9,
      last_price: 254,
    },
    {
      tradingsymbol: "TITAN",
      product: "CNC",
      quantity: 1,
      average_price: 5058.7,
      last_price: 5090,
    },
  ]);
  assert(
    positionsPnl !== null && Math.abs(positionsPnl - 24.3) < 0.01,
    "Positions P&L must match Zerodha Positions export total",
  );

  const holdingsOnly = computeZerodhaPositionsPnl(
    [
      {
        tradingsymbol: "GRASIM",
        quantity: 1,
        average_price: 3393.3,
        last_price: 3380.5,
      },
    ],
    [],
  );
  assert(
    holdingsOnly === null,
    "Positions P&L must use Zerodha net legs only, not holdings-only rows",
  );

  const fromLtpOnly = computeZerodhaPositionsPnl([], [
    {
      tradingsymbol: "TITAN",
      product: "CNC",
      quantity: 1,
      average_price: 5058.7,
      last_price: 5090,
    },
  ]);
  assert(
    fromLtpOnly !== null && Math.abs(fromLtpOnly - 31.3) < 0.01,
    "Positions P&L must derive from LTP and avg when Kite pnl is absent",
  );

  const preferNetPnl = computeZerodhaPositionsPnl(
    [],
    [
      {
        tradingsymbol: "HEROMOTOCO",
        product: "CNC",
        quantity: 1,
        average_price: 5856.1,
        last_price: 5860,
        pnl: -55,
        ltpFromQuote: true,
      },
    ],
  );
  assert(
    preferNetPnl !== null && Math.abs(preferNetPnl - 3.9) < 0.01,
    "Positions P&L must derive from live quote LTP when ltpFromQuote is set",
  );

  const preferKitePnl = computeZerodhaPositionsPnl(
    [],
    [
      {
        tradingsymbol: "HEROMOTOCO",
        product: "CNC",
        quantity: 1,
        average_price: 5856.1,
        last_price: 5801,
        pnl: 3.9,
      },
    ],
  );
  assert(
    preferKitePnl !== null && Math.abs(preferKitePnl - 3.9) < 0.01,
    "Positions P&L must trust Kite pnl when quote LTP is unavailable",
  );

  const nativeSum = sumNativeKiteNetCncPnl([
    {
      tradingsymbol: "HEROMOTOCO",
      product: "CNC",
      quantity: 1,
      average_price: 5856.1,
      last_price: 5801,
      pnl: 3.9,
    },
    {
      tradingsymbol: "JIOFIN",
      product: "CNC",
      quantity: -1,
      average_price: 255.9,
      last_price: 254,
      pnl: 1.9,
    },
  ]);
  assert(
    nativeSum !== null && Math.abs(nativeSum - 5.8) < 0.01,
    "Native Kite pnl sum must match Zerodha Positions tab fields",
  );

  const breakdown = computeZerodhaPositionsBreakdown(
    [],
    [
      {
        tradingsymbol: "TITAN",
        product: "CNC",
        quantity: 1,
        average_price: 5058.7,
        last_price: 5090,
        pnl: 31.3,
      },
      {
        tradingsymbol: "JIOFIN",
        product: "CNC",
        quantity: -1,
        average_price: 255.9,
        last_price: 254,
        pnl: 1.9,
      },
    ],
  );
  assert(
    breakdown.length === 2 &&
      breakdown.some(
        (row) => row.symbol === "JIOFIN" && row.quantity === -1 && row.pnl === 1.9,
      ) &&
      Math.abs(
        breakdown.reduce((sum, row) => sum + row.pnl, 0) -
          (computeZerodhaPositionsPnl(
            [],
            [
              {
                tradingsymbol: "TITAN",
                product: "CNC",
                quantity: 1,
                average_price: 5058.7,
                last_price: 5090,
                pnl: 31.3,
              },
              {
                tradingsymbol: "JIOFIN",
                product: "CNC",
                quantity: -1,
                average_price: 255.9,
                last_price: 254,
                pnl: 1.9,
              },
            ],
          ) ?? 0),
      ) < 0.01,
    "Positions breakdown must include short legs and sum to total Open P&L",
  );
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
      ...kiteReadRequestConfig(config.apiKey, accessToken),
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

function kiteReadRequestConfig(apiKey: string, accessToken: string) {
  return kiteDirectRequestConfig(apiKey, accessToken);
}

/** Proxied reads — only when direct quote fetch returns nothing (whitelisted IP). */
function kiteProxiedRequestConfig(apiKey: string, accessToken: string) {
  return {
    headers: kiteAuthHeaders(apiKey, accessToken),
    timeout: 12_000,
    ...buildKiteAxiosConfig(),
  };
}

/** @deprecated Use kiteReadRequestConfig for reads; proxy is for orders only. */
function kiteRequestConfig(apiKey: string, accessToken: string) {
  return kiteReadRequestConfig(apiKey, accessToken);
}

function kiteDirectRequestConfig(apiKey: string, accessToken: string) {
  return {
    headers: kiteAuthHeaders(apiKey, accessToken),
    timeout: 12_000,
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

function readKiteResponseData(payload: unknown): Record<string, unknown> | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const envelope = payload as {
    status?: string;
    message?: string;
    data?: unknown;
  };

  if (envelope.status === "error") {
    brokerError("Kite API error", envelope.message ?? "unknown");
    return null;
  }

  if (!envelope.data || typeof envelope.data !== "object") {
    return null;
  }

  return envelope.data as Record<string, unknown>;
}

async function fetchZerodhaLtpBatch(
  symbols: string[],
  exchange: string,
  quotes: Map<string, ZerodhaLiveQuote>,
  requestConfig: ReturnType<typeof kiteReadRequestConfig>,
): Promise<void> {
  if (symbols.length === 0) {
    return;
  }

  const query = buildInstrumentQuery(symbols, exchange);

  let ltpData: Record<string, unknown> | null = null;
  try {
    const ltpRes = await axios.get(
      `https://api.kite.trade/quote/ltp?${query}`,
      requestConfig,
    );
    ltpData = readKiteResponseData(ltpRes.data);
  } catch (err) {
    brokerError(
      "fetchZerodhaLtpBatch failed",
      err instanceof Error ? err.message : err,
    );
    return;
  }

  if (!ltpData) {
    return;
  }

  let ohlcData: Record<string, unknown> | null = null;
  try {
    const ohlcRes = await axios.get(
      `https://api.kite.trade/quote/ohlc?${query}`,
      requestConfig,
    );
    ohlcData = readKiteResponseData(ohlcRes.data);
  } catch {
    // OHLC is optional — never block LTP.
  }

  for (const symbol of symbols) {
    const instrument = `${exchange}:${symbol}`;
    const lastPrice = (
      ltpData[instrument] as { last_price?: number } | undefined
    )?.last_price;
    const previousClose = (
      ohlcData?.[instrument] as { ohlc?: { close?: number } } | undefined
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
}

/** @deprecated Use fetchZerodhaLtpBatch */
async function fetchZerodhaLtpOhlcBatch(
  accessToken: string,
  symbols: string[],
  exchange: string,
  quotes: Map<string, ZerodhaLiveQuote>,
  requestConfig: ReturnType<typeof kiteReadRequestConfig>,
): Promise<void> {
  void accessToken;
  await fetchZerodhaLtpBatch(symbols, exchange, quotes, requestConfig);
}

async function fetchZerodhaLiveQuote(
  accessToken: string,
  tradingsymbol: string,
  exchange = "NSE",
  requestConfig?: ReturnType<typeof kiteReadRequestConfig>,
): Promise<ZerodhaLiveQuote | null> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return null;
  }

  const instrument = `${exchange}:${tradingsymbol}`;
  const axiosConfig =
    requestConfig ?? kiteReadRequestConfig(config.apiKey, accessToken);

  try {
    const res = await axios.get(
      `https://api.kite.trade/quote?i=${encodeURIComponent(instrument)}`,
      axiosConfig,
    );

    const parsed = parseKiteQuotePayload(
      readKiteResponseData(res.data)?.[instrument],
    );
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
  const normalized = normalizeSymbol(tradingsymbol);
  await fetchZerodhaLtpBatch([normalized], exchange, fallback, axiosConfig);
  return fallback.get(normalized) ?? null;
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

async function loadZerodhaQuotesWithConfig(
  symbols: string[],
  exchange: string,
  requestConfig: ReturnType<typeof kiteReadRequestConfig>,
): Promise<Map<string, ZerodhaLiveQuote>> {
  const quotes = new Map<string, ZerodhaLiveQuote>();

  if (symbols.length === 0) {
    return quotes;
  }

  try {
    const query = buildInstrumentQuery(symbols, exchange);
    const res = await axios.get(
      `https://api.kite.trade/quote?${query}`,
      requestConfig,
    );
    const data = readKiteResponseData(res.data);

    if (data) {
      for (const symbol of symbols) {
        const instrument = `${exchange}:${symbol}`;
        const parsed = parseKiteQuotePayload(data[instrument]);
        if (parsed) {
          quotes.set(symbol, parsed);
        }
      }
    }
  } catch (err) {
    brokerError(
      "fetchZerodhaQuotes full batch failed",
      err instanceof Error ? err.message : err,
    );
  }

  const missingAfterLtp = symbols.filter((symbol) => !quotes.has(symbol));
  if (missingAfterLtp.length > 0) {
    await fetchZerodhaLtpBatch(
      missingAfterLtp,
      exchange,
      quotes,
      requestConfig,
    );
  }

  return quotes;
}

export type ZerodhaQuoteFetchResult = {
  quotes: Map<string, ZerodhaLiveQuote>;
  via: "direct" | "proxy";
};

export async function fetchZerodhaQuotesWithMeta(
  accessToken: string,
  tradingsymbols: string[],
  exchange = "NSE",
): Promise<ZerodhaQuoteFetchResult> {
  const symbols = [
    ...new Set(
      tradingsymbols.map((symbol) => normalizeSymbol(symbol)).filter(Boolean),
    ),
  ];

  if (symbols.length === 0) {
    return { quotes: new Map(), via: "direct" };
  }

  const config = getZerodhaConfig();
  if (!config.configured) {
    return { quotes: new Map(), via: "direct" };
  }

  let via: "direct" | "proxy" = "direct";
  let quotes = await loadZerodhaQuotesWithConfig(
    symbols,
    exchange,
    kiteReadRequestConfig(config.apiKey, accessToken),
  );

  if (quotes.size === 0 && getKiteOrderProxyStatus().configured) {
    brokerLog("fetchZerodhaQuotes: direct returned 0, retrying via proxy");
    quotes = await loadZerodhaQuotesWithConfig(
      symbols,
      exchange,
      kiteProxiedRequestConfig(config.apiKey, accessToken),
    );
    via = "proxy";
  }

  if (quotes.size === 0) {
    brokerError(
      "fetchZerodhaQuotes returned no symbols",
      symbols.join(","),
    );
  }

  return { quotes, via };
}

export async function fetchZerodhaQuotes(
  accessToken: string,
  tradingsymbols: string[],
  exchange = "NSE",
): Promise<Map<string, ZerodhaLiveQuote>> {
  const result = await fetchZerodhaQuotesWithMeta(
    accessToken,
    tradingsymbols,
    exchange,
  );
  return result.quotes;
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
