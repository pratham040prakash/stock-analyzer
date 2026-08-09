import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { KITE_ACCESS_TOKEN_COOKIE } from "@/lib/broker/zerodhaSession";
import { computeTotalCapital } from "@/lib/broker/zerodhaFunds";
import {
  resolveAlternateZerodhaAccessToken,
  resolveZerodhaAccessToken,
} from "@/services/broker/accessToken";
import {
  markBrokerConnectionExpired,
} from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  fetchZerodhaHoldings,
  fetchZerodhaMargins,
  mapKiteHoldingsToPortfolio,
  type FetchMarginsResult,
} from "@/services/brokers/zerodha";
import { createClient } from "@/lib/supabase/server";

function emptyFunds(status: string, extra?: Record<string, unknown>) {
  return NextResponse.json({
    ledger_cash: 0,
    collateral: 0,
    margin_available: 0,
    live_balance: 0,
    portfolio_value: 0,
    total_capital: 0,
    available_cash: 0,
    status,
    ...extra,
  });
}

function resolvePortfolioValue(
  holdingsResult: Awaited<ReturnType<typeof fetchZerodhaHoldings>>,
): number {
  if (holdingsResult.status !== "OK") {
    return 0;
  }

  const portfolio = mapKiteHoldingsToPortfolio(holdingsResult.data);
  return computePortfolioMetrics(portfolio).totalValue;
}

async function fetchMarginsWithRetry(
  supabase: Awaited<ReturnType<typeof createClient>>,
  userId: string,
): Promise<FetchMarginsResult> {
  const resolved = await resolveZerodhaAccessToken(supabase, userId);
  if (!resolved) {
    return { status: "ERROR", message: "Zerodha not connected" };
  }

  let marginsResult = await fetchZerodhaMargins(resolved.accessToken);

  if (
    marginsResult.status === "TOKEN_EXPIRED" ||
    marginsResult.status === "ERROR"
  ) {
    const alternate = await resolveAlternateZerodhaAccessToken(
      supabase,
      userId,
      resolved,
    );
    if (alternate) {
      marginsResult = await fetchZerodhaMargins(alternate.accessToken);
    }
  }

  return marginsResult;
}

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return emptyFunds("NOT_CONNECTED", { statusCode: 401 });
  }

  const resolved = await resolveZerodhaAccessToken(supabase, user.id);
  if (!resolved) {
    return emptyFunds("NOT_CONNECTED");
  }

  const [marginsResult, holdingsResult] = await Promise.all([
    fetchMarginsWithRetry(supabase, user.id),
    fetchZerodhaHoldings(resolved.accessToken),
  ]);

  if (marginsResult.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, user.id);
    const cookieStore = await cookies();
    cookieStore.delete(KITE_ACCESS_TOKEN_COOKIE);
    return emptyFunds("TOKEN_EXPIRED", {
      message: "Zerodha session expired. Reconnect to refresh funds.",
    });
  }

  const portfolioValue = resolvePortfolioValue(holdingsResult);

  if (marginsResult.status === "ERROR") {
    return NextResponse.json({
      ledger_cash: 0,
      collateral: 0,
      margin_available: 0,
      live_balance: 0,
      portfolio_value: portfolioValue,
      total_capital: computeTotalCapital(portfolioValue, 0),
      available_cash: 0,
      status: portfolioValue > 0 ? "PARTIAL" : "ERROR",
      message: marginsResult.message,
    });
  }

  const totalCapital = computeTotalCapital(
    portfolioValue,
    marginsResult.ledgerCash,
  );

  return NextResponse.json({
    ledger_cash: marginsResult.ledgerCash,
    collateral: marginsResult.collateral,
    margin_available: marginsResult.marginAvailable,
    live_balance: marginsResult.liveBalance,
    portfolio_value: portfolioValue,
    total_capital: totalCapital,
    /** Deployable CNC balance — matches Zerodha Cash + Collateral. */
    available_cash: marginsResult.marginAvailable,
    status: "OK",
  });
}
