import {
  listZerodhaAccessTokenCandidates,
  type ResolvedZerodhaAccessToken,
} from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaNetPositions,
  fetchZerodhaQuotes,
  mergeKiteHoldingsAndPositions,
  type KiteHolding,
} from "@/services/brokers/zerodha";
import { normalizeSymbol } from "@/lib/stockPool";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type LiveKitePortfolioResult =
  | {
      status: "OK";
      holdings: KiteHolding[];
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
      fetchZerodhaNetPositions(candidate.accessToken),
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
    const positions =
      positionsResult.status === "OK" ? positionsResult.data : [];
    const merged = mergeKiteHoldingsAndPositions(holdings, positions);
    const enriched = await enrichHoldingsWithLiveQuotes(
      candidate.accessToken,
      merged,
    );

    return {
      status: "OK",
      holdings: enriched,
      token: candidate,
    };
  }

  if (sawExpired) {
    return { status: "TOKEN_EXPIRED" };
  }

  return { status: "ERROR", message: lastMessage };
}
