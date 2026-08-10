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

async function enrichHoldingsWithLiveQuotes(
  accessToken: string,
  holdings: KiteHolding[],
): Promise<KiteHolding[]> {
  if (holdings.length === 0) {
    return holdings;
  }

  const quotes = await fetchZerodhaQuotes(
    accessToken,
    holdings.map((holding) => holding.tradingsymbol),
  );

  if (quotes.size === 0) {
    return holdings;
  }

  return holdings.map((holding) => {
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
}

async function enrichNetPositionsWithLiveQuotes(
  accessToken: string,
  positions: KiteNetPosition[],
): Promise<KiteNetPosition[]> {
  if (positions.length === 0) {
    return positions;
  }

  const quotes = await fetchZerodhaQuotes(
    accessToken,
    positions.map((position) => position.tradingsymbol),
  );

  if (quotes.size === 0) {
    return positions;
  }

  return positions.map((position) => {
    const quote = quotes.get(normalizeSymbol(position.tradingsymbol));
    if (!quote?.lastPrice) {
      return position;
    }

    const ltp = quote.lastPrice;
    const avg = position.average_price;
    const pnl = (ltp - avg) * position.quantity;

    return {
      ...position,
      last_price: ltp,
      pnl: roundPnl(pnl),
    };
  });
}

function roundPnl(value: number): number {
  return Math.round(value * 10) / 10;
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
    const [enriched, enrichedNetPnl] = await Promise.all([
      enrichHoldingsWithLiveQuotes(candidate.accessToken, merged),
      enrichNetPositionsWithLiveQuotes(candidate.accessToken, netPnlPositions),
    ]);

    return {
      status: "OK",
      holdings: enriched,
      netPnlPositions: enrichedNetPnl,
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
