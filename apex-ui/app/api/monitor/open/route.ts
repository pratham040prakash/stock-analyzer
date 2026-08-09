import { apiError, apiOk } from "@/lib/api/response";
import { getOpenMonitorPositions } from "@/services/monitor/openPositions";
import {
  computePortfolioDayPnl,
  fetchZerodhaHoldings,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { resolveZerodhaAccessToken } from "@/services/broker/accessToken";
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

  const positions = await getOpenMonitorPositions(supabase, user.id);

  let dayPnl: number | null = null;
  const token = await resolveZerodhaAccessToken(supabase, user.id);

  if (token) {
    const holdingsResult = await fetchZerodhaHoldings(token.accessToken);
    if (holdingsResult.status === "OK") {
      const portfolio = mapKiteHoldingsToPortfolio(holdingsResult.data);
      dayPnl = computePortfolioDayPnl(portfolio);
    }
  }

  return apiOk({
    positions,
    dayPnl,
  });
}
