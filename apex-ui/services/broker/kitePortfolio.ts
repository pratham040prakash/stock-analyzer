import {
  listZerodhaAccessTokenCandidates,
  type ResolvedZerodhaAccessToken,
} from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaCncPositions,
  fetchZerodhaQuotes,
  mergeKiteHoldingsAndPositions,
  resolveKiteLastPrice,
  type KiteHolding,
  type KiteNetPosition,
} from "@/services/brokers/zerodha";
import { normalizeSymbol } from "@/lib/stockPool";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type LiveKitePortfolioResult =
  | {
      status: "OK";
      holdings: KiteHolding[];
      /** CNC net legs for Zerodha Positions P&L (qty may be negative). */
      netPnlPositions: KiteNetPosition[];
      dayPositions: KiteNetPosition[];
      token: ResolvedZerodhaAccessToken;
    }
  | { status: "NOT_CONNECTED" }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

function roundPnl(value: number): number {
  return Math.round(value * 10) / 10;
}

function holdingLtpBySymbol(holdings: KiteHolding[]): Map<string, number> {
  const map = new Map<string, number>();

  for (const holding of holdings) {
    const symbol = normalizeSymbol(holding.tradingsymbol);
    const ltp = resolveKiteLastPrice(holding);
    if (symbol && ltp > 0) {
      map.set(symbol, ltp);
    }
  }

  return map;
}

/** One /quote batch for holdings + net legs — avoids stale Kite position LTP. */
async function enrichKitePortfolioPrices(
  accessToken: string,
  holdings: KiteHolding[],
  netPnl: KiteNetPosition[],
  rawHoldingLtp: Map<string, number>,
): Promise<{ holdings: KiteHolding[]; netPnl: KiteNetPosition[] }> {
  const symbols = [
    ...new Set(
      [
        ...holdings.map((holding) => normalizeSymbol(holding.tradingsymbol)),
        ...netPnl.map((position) => normalizeSymbol(position.tradingsymbol)),
      ].filter(Boolean),
    ),
  ];

  if (symbols.length === 0) {
    return { holdings, netPnl };
  }

  const quotes = await fetchZerodhaQuotes(accessToken, symbols);

  const enrichedHoldings = holdings.map((holding) => {
    const quote = quotes.get(normalizeSymbol(holding.tradingsymbol));
    if (!quote?.lastPrice) {
      return holding;
    }

    const close = quote.previousClose ?? holding.close_price;
    const dayChange =
      typeof close === "number" && close > 0
        ? quote.lastPrice - close
        : holding.day_change;

    return {
      ...holding,
      last_price: quote.lastPrice,
      close_price: close ?? holding.close_price,
      day_change: dayChange ?? holding.day_change,
    };
  });

  const quotedHoldingLtp = holdingLtpBySymbol(enrichedHoldings);

  const enrichedNetPnl = netPnl.map((position) => {
    const symbol = normalizeSymbol(position.tradingsymbol);
    const quoteLtp = quotes.get(symbol)?.lastPrice;

    if (quoteLtp && quoteLtp > 0) {
      return {
        ...position,
        last_price: quoteLtp,
        ltpFromQuote: true as const,
        pnl: roundPnl((quoteLtp - position.average_price) * position.quantity),
      };
    }

    // Holdings /quote LTP is usually fresher than net position last_price.
    const holdingLtp =
      quotedHoldingLtp.get(symbol) ?? rawHoldingLtp.get(symbol);
    if (
      position.quantity > 0 &&
      typeof holdingLtp === "number" &&
      holdingLtp > 0
    ) {
      return {
        ...position,
        last_price: holdingLtp,
        ltpFromHolding: true as const,
        pnl: roundPnl(
          (holdingLtp - position.average_price) * position.quantity,
        ),
      };
    }

    // Short legs (e.g. JIOFIN −1) — keep Kite native pnl, not stale LTP recalc.
    return position;
  });

  return { holdings: enrichedHoldings, netPnl: enrichedNetPnl };
}

/** Load CNC holdings + same-day positions using every usable Zerodha token. */
export async function fetchLiveKitePortfolio(
  supabase: Client,
  userId: string,
): Promise<LiveKitePortfolioResult> {
  const candidates = await listZerodhaAccessTokenCandidates(supabase, userId);

  if (candidates.length === 0) {
    return { status: "NOT_CONNECTED" };
  }

  let sawExpired = false;
  let lastMessage = "Could not load Zerodha portfolio";

  for (const candidate of candidates) {
    const [holdingsResult, positionsResult] = await Promise.all([
      fetchZerodhaHoldings(candidate.accessToken),
      fetchZerodhaCncPositions(candidate.accessToken),
    ]);

    if (
      holdingsResult.status === "TOKEN_EXPIRED" ||
      positionsResult.status === "TOKEN_EXPIRED"
    ) {
      sawExpired = true;
      continue;
    }

    if (holdingsResult.status === "ERROR" && positionsResult.status === "ERROR") {
      lastMessage = holdingsResult.message;
      continue;
    }

    const holdings =
      holdingsResult.status === "OK" ? holdingsResult.data : [];
    const netPositions =
      positionsResult.status === "OK" ? positionsResult.net : [];
    const netPnlPositions =
      positionsResult.status === "OK" ? positionsResult.netPnl : [];
    const dayPositions: KiteNetPosition[] =
      positionsResult.status === "OK" ? positionsResult.day : [];
    const merged = mergeKiteHoldingsAndPositions(holdings, netPositions);
    const rawHoldingLtp = holdingLtpBySymbol(holdings);
    const enriched = await enrichKitePortfolioPrices(
      candidate.accessToken,
      merged,
      netPnlPositions,
      rawHoldingLtp,
    );

    return {
      status: "OK",
      holdings: enriched.holdings,
      netPnlPositions: enriched.netPnl,
      dayPositions,
      token: candidate,
    };
  }

  if (sawExpired) {
    return { status: "TOKEN_EXPIRED" };
  }

  return { status: "ERROR", message: lastMessage };
}

const PORTFOLIO_CACHE_MS = 5_000;
const portfolioCache = new Map<
  string,
  { expiresAt: number; value: LiveKitePortfolioResult }
>();
const portfolioInflight = new Map<string, Promise<LiveKitePortfolioResult>>();

/** Short TTL cache — one Kite fetch shared by P&L polls and funds. */
export async function fetchLiveKitePortfolioCached(
  supabase: Client,
  userId: string,
): Promise<LiveKitePortfolioResult> {
  const now = Date.now();
  const cached = portfolioCache.get(userId);

  if (cached && cached.expiresAt > now) {
    return cached.value;
  }

  const inflight = portfolioInflight.get(userId);
  if (inflight) {
    return inflight;
  }

  const request = fetchLiveKitePortfolio(supabase, userId)
    .then((result) => {
      portfolioCache.set(userId, {
        expiresAt: Date.now() + PORTFOLIO_CACHE_MS,
        value: result,
      });
      return result;
    })
    .finally(() => {
      portfolioInflight.delete(userId);
    });

  portfolioInflight.set(userId, request);
  return request;
}
