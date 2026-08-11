import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { KITE_ACCESS_TOKEN_COOKIE } from "@/lib/broker/zerodhaSession";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import { markBrokerConnectionExpired } from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  computeZerodhaPositionsPnl,
  enrichPortfolioQuantitiesFromNetPositions,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { formatPortfolioHoldings } from "@/services/portfolio/format";
import {
  getLatestPortfolioSnapshot,
  savePortfolioSnapshot,
} from "@/services/portfolio/repository";
import { syncBrokerActivityFromKite } from "@/services/trade/syncBrokerActivity";
import { createClient } from "@/lib/supabase/server";
import type { PortfolioApiResponse } from "@/types/portfolioApi";

function okResponse(
  payload: Omit<PortfolioApiResponse, "status">,
  stale = false,
): NextResponse<PortfolioApiResponse> {
  return NextResponse.json({
    status: "OK",
    stale,
    ...payload,
  });
}

function formattedCachedResponse(
  status: PortfolioApiResponse["status"],
  stale = false,
) {
  return async (
    supabase: Awaited<ReturnType<typeof createClient>>,
    userId: string,
  ) => {
    const cached = await getLatestPortfolioSnapshot(supabase, userId);
    if (!cached || cached.holdings.length === 0) {
      return null;
    }

    const formatted = formatPortfolioHoldings(cached);
    return NextResponse.json({
      status,
      stale,
      holdings: formatted.holdings,
      total_value: formatted.total_value,
      total_pnl: formatted.total_pnl,
      day_pnl: null,
      positions_pnl: null,
      concentrated: formatted.concentrated,
      top_symbol: formatted.top_symbol ?? undefined,
      top_allocation_pct: formatted.top_allocation_pct,
      risk_score: formatted.risk_score,
      risk_level: formatted.risk_level,
    });
  };
}

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json(
      { status: "NOT_CONNECTED", holdings: [], message: "Unauthorized" },
      { status: 401 },
    );
  }

  const live = await fetchLiveKitePortfolioCached(supabase, user.id);
  const fromCache = formattedCachedResponse("TOKEN_EXPIRED");

  if (live.status === "NOT_CONNECTED") {
    const cached = await fromCache(supabase, user.id);
    return cached ?? NextResponse.json({ status: "NOT_CONNECTED", holdings: [] });
  }

  if (live.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, user.id);
    const cookieStore = await cookies();
    cookieStore.delete(KITE_ACCESS_TOKEN_COOKIE);

    const cached = await fromCache(supabase, user.id);
    return cached ?? NextResponse.json({ status: "TOKEN_EXPIRED", holdings: [] });
  }

  if (live.status === "ERROR") {
    const cached = await formattedCachedResponse("OK", true)(supabase, user.id);
    if (cached) {
      return cached;
    }

    return NextResponse.json({
      status: "ERROR",
      holdings: [],
      message: live.message,
    });
  }

  let portfolio = enrichPortfolioQuantitiesFromNetPositions(
    mapKiteHoldingsToPortfolio(live.holdings),
    live.netPnlPositions,
  );

  if (portfolio.holdings.length === 0) {
    const existing = await getLatestPortfolioSnapshot(supabase, user.id);
    if (existing && existing.holdings.length > 0) {
      portfolio = enrichPortfolioQuantitiesFromNetPositions(
        existing,
        live.netPnlPositions,
      );
      const formatted = formatPortfolioHoldings(portfolio, live.dayPositions);
      const positions_pnl = computeZerodhaPositionsPnl(
        live.holdings,
        live.netPnlPositions,
      );
      return okResponse(
        {
          holdings: formatted.holdings,
          total_value: formatted.total_value,
          total_pnl: formatted.total_pnl,
          day_pnl: formatted.day_pnl,
          positions_pnl,
          portfolio_day_pnl: formatted.day_pnl,
          concentrated: formatted.concentrated,
          top_symbol: formatted.top_symbol ?? undefined,
          top_allocation_pct: formatted.top_allocation_pct,
          risk_score: formatted.risk_score,
          risk_level: formatted.risk_level,
        },
        true,
      );
    }
  }

  if (portfolio.holdings.length > 0) {
    const metrics = computePortfolioMetrics(portfolio);
    await savePortfolioSnapshot(supabase, user.id, portfolio, metrics);
    await syncBrokerActivityFromKite(supabase, user.id);
  }

  const formatted = formatPortfolioHoldings(portfolio, live.dayPositions);
  const positions_pnl = computeZerodhaPositionsPnl(live.holdings, live.netPnlPositions);
  return okResponse({
    holdings: formatted.holdings,
    total_value: formatted.total_value,
    total_pnl: formatted.total_pnl,
    day_pnl: formatted.day_pnl,
    positions_pnl,
    portfolio_day_pnl: formatted.day_pnl,
    concentrated: formatted.concentrated,
    top_symbol: formatted.top_symbol ?? undefined,
    top_allocation_pct: formatted.top_allocation_pct,
    risk_score: formatted.risk_score,
    risk_level: formatted.risk_level,
  });
}
