import {
  listZerodhaAccessTokenCandidates,
  type ResolvedZerodhaAccessToken,
} from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaCncPositions,
  fetchZerodhaQuotesWithMeta,
  mergeKiteHoldingsAndPositions,
  sumNativeKiteNetCncPnl,
  type KiteHolding,
  type KiteNetPosition,
} from "@/services/brokers/zerodha";
import { normalizeSymbol } from "@/lib/stockPool";
import { LIVE_KITE_REFRESH_MS } from "@/lib/liveKiteRefresh";
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
      /** Raw sum of Kite net `pnl` before quote enrichment. */
      kiteNativePositionsPnl: number | null;
      quotesReceived: number;
      quotesVia: "direct" | "proxy" | null;
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
): Promise<{
  holdings: KiteHolding[];
  netPnl: KiteNetPosition[];
  quotesReceived: number;
  quotesVia: "direct" | "proxy" | null;
}> {
  const symbols = [
    ...new Set(
      [
        ...holdings.map((holding) => normalizeSymbol(holding.tradingsymbol)),
        ...netPnl.map((position) => normalizeSymbol(position.tradingsymbol)),
      ].filter(Boolean),
    ),
  ];

  if (symbols.length === 0) {
    return { holdings, netPnl, quotesReceived: 0, quotesVia: null };
  }

  const { quotes, via } = await fetchZerodhaQuotesWithMeta(accessToken, symbols);

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

    // Keep Kite net `pnl` — matches Zerodha Positions tab; do not recalc stale LTP.
    return position;
  });

  return {
    holdings: enrichedHoldings,
    netPnl: enrichedNetPnl,
    quotesReceived: quotes.size,
    quotesVia: quotes.size > 0 ? via : null,
  };
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
    const kiteNativePositionsPnl = sumNativeKiteNetCncPnl(netPnlPositions);
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
      kiteNativePositionsPnl,
      quotesReceived: enriched.quotesReceived,
      quotesVia: enriched.quotesVia,
      token: candidate,
    };
  }

  if (sawExpired) {
    return { status: "TOKEN_EXPIRED" };
  }

  return { status: "ERROR", message: lastMessage };
}

const PORTFOLIO_CACHE_MS = LIVE_KITE_REFRESH_MS - 500;
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
