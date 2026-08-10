import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { KITE_ACCESS_TOKEN_COOKIE } from "@/lib/broker/zerodhaSession";
import {
  getActiveBrokerConnection,
  markBrokerConnectionExpired,
} from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  fetchZerodhaHoldings,
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

  const connection = await getActiveBrokerConnection(supabase, user.id);

  if (!connection || connection.status !== "active") {
    const cached = await getLatestPortfolioSnapshot(supabase, user.id);
    if (cached && cached.holdings.length > 0) {
      const formatted = formatPortfolioHoldings(cached);
      return NextResponse.json({
        status: "TOKEN_EXPIRED",
        holdings: formatted.holdings,
        total_value: formatted.total_value,
        total_pnl: formatted.total_pnl,
        day_pnl: formatted.day_pnl,
        concentrated: formatted.concentrated,
        top_symbol: formatted.top_symbol ?? undefined,
        top_allocation_pct: formatted.top_allocation_pct,
        risk_score: formatted.risk_score,
        risk_level: formatted.risk_level,
      });
    }

    return NextResponse.json({ status: "NOT_CONNECTED", holdings: [] });
  }

  const holdingsResult = await fetchZerodhaHoldings(connection.accessToken);

  if (holdingsResult.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, user.id);
    const cookieStore = await cookies();
    cookieStore.delete(KITE_ACCESS_TOKEN_COOKIE);

    const cached = await getLatestPortfolioSnapshot(supabase, user.id);
    if (cached && cached.holdings.length > 0) {
      const formatted = formatPortfolioHoldings(cached);
      return NextResponse.json({
        status: "TOKEN_EXPIRED",
        holdings: formatted.holdings,
        total_value: formatted.total_value,
        total_pnl: formatted.total_pnl,
        day_pnl: formatted.day_pnl,
        concentrated: formatted.concentrated,
        top_symbol: formatted.top_symbol ?? undefined,
        top_allocation_pct: formatted.top_allocation_pct,
        risk_score: formatted.risk_score,
        risk_level: formatted.risk_level,
      });
    }

    return NextResponse.json({ status: "TOKEN_EXPIRED", holdings: [] });
  }

  if (holdingsResult.status === "ERROR") {
    const cached = await getLatestPortfolioSnapshot(supabase, user.id);
    if (cached && cached.holdings.length > 0) {
      const formatted = formatPortfolioHoldings(cached);
      return okResponse(
        {
          holdings: formatted.holdings,
          total_value: formatted.total_value,
          total_pnl: formatted.total_pnl,
          day_pnl: formatted.day_pnl,
          concentrated: formatted.concentrated,
          top_symbol: formatted.top_symbol ?? undefined,
          top_allocation_pct: formatted.top_allocation_pct,
          risk_score: formatted.risk_score,
          risk_level: formatted.risk_level,
        },
        true,
      );
    }

    return NextResponse.json({
      status: "ERROR",
      holdings: [],
      message: holdingsResult.message,
    });
  }

  const portfolio = mapKiteHoldingsToPortfolio(holdingsResult.data);
  const metrics = computePortfolioMetrics(portfolio);
  await savePortfolioSnapshot(supabase, user.id, portfolio, metrics);
  await syncBrokerActivityFromKite(supabase, user.id);

  const formatted = formatPortfolioHoldings(portfolio);
  return okResponse({
    holdings: formatted.holdings,
    total_value: formatted.total_value,
    total_pnl: formatted.total_pnl,
    day_pnl: formatted.day_pnl,
    concentrated: formatted.concentrated,
    top_symbol: formatted.top_symbol ?? undefined,
    top_allocation_pct: formatted.top_allocation_pct,
    risk_score: formatted.risk_score,
    risk_level: formatted.risk_level,
  });
}
