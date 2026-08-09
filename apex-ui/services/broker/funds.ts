import type { SupabaseClient } from "@supabase/supabase-js";
import {
  listZerodhaAccessTokenCandidates,
  type ResolvedZerodhaAccessToken,
} from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaMargins,
  type FetchHoldingsResult,
  type FetchMarginsResult,
} from "@/services/brokers/zerodha";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type ZerodhaFundsFetchResult =
  | {
      status: "OK";
      margins: Extract<FetchMarginsResult, { status: "OK" }>;
      holdings: Extract<FetchHoldingsResult, { status: "OK" }> | null;
      token: ResolvedZerodhaAccessToken;
    }
  | {
      status: "NOT_CONNECTED";
      message: string;
    }
  | {
      status: "TOKEN_EXPIRED";
      message: string;
      holdings: Extract<FetchHoldingsResult, { status: "OK" }> | null;
    }
  | {
      status: "ERROR";
      message: string;
      holdings: Extract<FetchHoldingsResult, { status: "OK" }> | null;
    };

async function fetchHoldingsWithCandidates(
  candidates: ResolvedZerodhaAccessToken[],
): Promise<FetchHoldingsResult> {
  let lastResult: FetchHoldingsResult = {
    status: "ERROR",
    message: "Zerodha not connected",
  };

  for (const candidate of candidates) {
    const result = await fetchZerodhaHoldings(candidate.accessToken);
    if (result.status === "OK") {
      return result;
    }
    lastResult = result;
    if (result.status === "TOKEN_EXPIRED") {
      continue;
    }
  }

  return lastResult;
}

/** Fetch live Zerodha margins using every usable token (DB + session cookie). */
export async function fetchZerodhaFundsForUser(
  supabase: Client,
  userId: string,
): Promise<ZerodhaFundsFetchResult> {
  const candidates = await listZerodhaAccessTokenCandidates(supabase, userId);

  if (candidates.length === 0) {
    return {
      status: "NOT_CONNECTED",
      message: "Connect Zerodha to sync available balance.",
    };
  }

  let lastMargins: FetchMarginsResult = {
    status: "ERROR",
    message: "Could not load Zerodha funds.",
  };
  let sawExpired = false;

  for (const candidate of candidates) {
    const margins = await fetchZerodhaMargins(candidate.accessToken);
    if (margins.status === "OK") {
      const holdings = await fetchZerodhaHoldings(candidate.accessToken);
      return {
        status: "OK",
        margins,
        holdings: holdings.status === "OK" ? holdings : null,
        token: candidate,
      };
    }

    lastMargins = margins;
    if (margins.status === "TOKEN_EXPIRED") {
      sawExpired = true;
    }
  }

  const holdingsResult = await fetchHoldingsWithCandidates(candidates);
  const holdings = holdingsResult.status === "OK" ? holdingsResult : null;

  if (sawExpired) {
    return {
      status: "TOKEN_EXPIRED",
      message: "Zerodha session expired. Reconnect to refresh funds.",
      holdings,
    };
  }

  return {
    status: "ERROR",
    message:
      lastMargins.status === "ERROR"
        ? lastMargins.message
        : "Could not load Zerodha funds.",
    holdings,
  };
}
