import {
  listZerodhaAccessTokenCandidates,
  type ResolvedZerodhaAccessToken,
} from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaCncPositions,
  fetchZerodhaQuotes,
  mergeKiteHoldingsAndPositions,
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

/** One /quote batch for holdings + net legs — avoids stale Kite position LTP. */
async function enrichKitePortfolioPrices(
  accessToken: string,
  holdings: KiteHolding[],
  netPnl: KiteNetPosition[],
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

  const ltpBySymbol = new Map<string, number>();
  for (const holding of enrichedHoldings) {
    const symbol = normalizeSymbol(holding.tradingsymbol);
    if (symbol && holding.last_price > 0) {
      ltpBySymbol.set(symbol, holding.last_price);
    }
  }

  const enrichedNetPnl = netPnl.map((position) => {
    const symbol = normalizeSymbol(position.tradingsymbol);
    const ltp =
      ltpBySymbol.get(symbol) ??
      quotes.get(symbol)?.lastPrice ??
      position.last_price;

    if (!ltp || ltp <= 0) {
      return position;
    }

    return {
      ...position,
      last_price: ltp,
      pnl: roundPnl((ltp - position.average_price) * position.quantity),
    };
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
    const enriched = await enrichKitePortfolioPrices(
      candidate.accessToken,
      merged,
      netPnlPositions,
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
