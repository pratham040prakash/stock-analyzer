import { apiError, apiOk } from "@/lib/api/response";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import { getOpenMonitorDayPnl } from "@/services/monitor/openPositions";
import {
  computePortfolioDayPnl,
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
      ? computePortfolioDayPnl(mapKiteHoldingsToPortfolio(live.holdings))
      : null;

  const monitorDayPnl = await getOpenMonitorDayPnl(supabase, user.id, live);

  return apiOk({
    portfolio_day_pnl: portfolioDayPnl,
    monitor_day_pnl: monitorDayPnl,
  });
}
