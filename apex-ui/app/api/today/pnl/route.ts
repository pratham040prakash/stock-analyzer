import { apiError, apiOk } from "@/lib/api/response";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import { getOpenMonitorLiveSnapshot } from "@/services/monitor/openPositions";
import {
  computePortfolioDayPnl,
  computeZerodhaPositionsBreakdown,
  computeZerodhaPositionsPnl,
  enrichPortfolioQuantitiesFromNetPositions,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { formatPortfolioHoldings } from "@/services/portfolio/format";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

/** Single poll endpoint — one cached Kite fetch for portfolio + monitor Day P&L. */
export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const live = await fetchLiveKitePortfolioCached(supabase, user.id);

  const portfolioDayPnl =
    live.status === "OK"
      ? computePortfolioDayPnl(
          mapKiteHoldingsToPortfolio(live.holdings),
          live.dayPositions,
        )
      : null;

  const positionsPnl =
    live.status === "OK"
      ? (computeZerodhaPositionsPnl(live.holdings, live.netPnlPositions) ??
        live.kiteNativePositionsPnl)
      : null;

  const positionsBreakdown =
    live.status === "OK"
      ? computeZerodhaPositionsBreakdown(live.holdings, live.netPnlPositions)
      : [];

  const holdingsLive =
    live.status === "OK"
      ? formatPortfolioHoldings(
          enrichPortfolioQuantitiesFromNetPositions(
            mapKiteHoldingsToPortfolio(live.holdings),
            live.netPnlPositions,
          ),
          live.dayPositions,
        )
      : null;

  const quotesApplied =
    live.status === "OK"
      ? live.netPnlPositions.filter((row) => row.ltpFromQuote === true).length
      : 0;

  const quotesRequested =
    live.status === "OK" ? live.netPnlPositions.length : 0;

  const kiteNativePnl =
    live.status === "OK" ? live.kiteNativePositionsPnl : null;

  const monitor = await getOpenMonitorLiveSnapshot(supabase, user.id, live);

  return apiOk({
    portfolio_day_pnl: portfolioDayPnl,
    positions_pnl: positionsPnl,
    positions_breakdown: positionsBreakdown,
    holdings_live: holdingsLive?.holdings ?? [],
    holdings_total_value: holdingsLive?.total_value ?? null,
    holdings_total_pnl: holdingsLive?.total_pnl ?? null,
    positions_net_legs:
      live.status === "OK" ? live.netPnlPositions.length : 0,
    live_kite_status: live.status,
    live_kite_message:
      live.status === "ERROR" ? live.message : undefined,
    quotes_applied: quotesApplied,
    quotes_requested: quotesRequested,
    quotes_received:
      live.status === "OK" ? live.quotesReceived : 0,
    quotes_via: live.status === "OK" ? live.quotesVia : null,
    kite_native_pnl: kiteNativePnl,
    build_sha: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? null,
    monitor_open_pnl: monitor.openPnl,
    monitor_day_pnl: monitor.dayPnl,
    position_ticks: monitor.ticks,
  });
}
