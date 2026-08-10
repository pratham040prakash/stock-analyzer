import { apiError, apiOk } from "@/lib/api/response";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import { getOpenMonitorLiveSnapshot } from "@/services/monitor/openPositions";
import {
  computePortfolioDayPnl,
  computeZerodhaPositionsBreakdown,
  computeZerodhaPositionsPnl,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
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
      ? computeZerodhaPositionsPnl(live.holdings, live.netPnlPositions)
      : null;

  const positionsBreakdown =
    live.status === "OK"
      ? computeZerodhaPositionsBreakdown(live.holdings, live.netPnlPositions)
      : [];

  const quotesApplied =
    live.status === "OK"
      ? live.netPnlPositions.filter((row) => row.ltpFromQuote === true).length
      : 0;

  const holdingsLtpApplied =
    live.status === "OK"
      ? live.netPnlPositions.filter((row) => row.ltpFromHolding === true).length
      : 0;

  const quotesRequested =
    live.status === "OK" ? live.netPnlPositions.length : 0;

  const monitor = await getOpenMonitorLiveSnapshot(supabase, user.id, live);

  return apiOk({
    portfolio_day_pnl: portfolioDayPnl,
    positions_pnl: positionsPnl,
    positions_breakdown: positionsBreakdown,
    positions_net_legs:
      live.status === "OK" ? live.netPnlPositions.length : 0,
    quotes_applied: quotesApplied,
    holdings_ltp_applied: holdingsLtpApplied,
    quotes_requested: quotesRequested,
    build_sha: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? null,
    monitor_open_pnl: monitor.openPnl,
    monitor_day_pnl: monitor.dayPnl,
    position_ticks: monitor.ticks,
  });
}
