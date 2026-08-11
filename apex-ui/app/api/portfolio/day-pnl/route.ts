import { apiError, apiOk } from "@/lib/api/response";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioDayPnl,
  computeZerodhaPositionsPnl,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const live = await fetchLiveKitePortfolioCached(supabase, user.id);

  if (live.status !== "OK") {
    return apiOk({
      day_pnl: null,
      positions_pnl: null,
      portfolio_day_pnl: null,
    });
  }

  const portfolio = mapKiteHoldingsToPortfolio(live.holdings);
  const day_pnl = computePortfolioDayPnl(portfolio, live.dayPositions);
  const positions_pnl = computeZerodhaPositionsPnl(
    live.holdings,
    live.netPnlPositions,
  );

  return apiOk({
    day_pnl,
    positions_pnl,
    portfolio_day_pnl: day_pnl,
  });
}
