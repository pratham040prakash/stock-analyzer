import {
  listZerodhaAccessTokenCandidates,
  type ResolvedZerodhaAccessToken,
} from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaNetPositions,
  mergeKiteHoldingsAndPositions,
  type KiteHolding,
} from "@/services/brokers/zerodha";
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

    return {
      status: "OK",
      holdings: mergeKiteHoldingsAndPositions(holdings, positions),
      token: candidate,
    };
  }

  if (sawExpired) {
    return { status: "TOKEN_EXPIRED" };
  }

  return { status: "ERROR", message: lastMessage };
}
