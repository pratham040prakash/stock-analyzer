import { apiError, apiOk } from "@/lib/api/response";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioDayPnl,
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
    return apiOk({ day_pnl: null });
  }

  const portfolio = mapKiteHoldingsToPortfolio(live.holdings);

  return apiOk({
    day_pnl: computePortfolioDayPnl(portfolio, live.dayPositions),
  });
}
