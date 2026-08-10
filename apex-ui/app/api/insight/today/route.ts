import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { buildDailyInsight } from "@/lib/dailyInsight";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioDayPnl,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { fetchMarketTrend } from "@/services/market/trend";
import { formatPortfolioHoldings } from "@/services/portfolio/format";
import { getLatestPortfolioSnapshot } from "@/services/portfolio/repository";
import { createClient } from "@/lib/supabase/server";
import type { DailyInsight } from "@/types/dailyInsight";

async function resolvePortfolioDayPnl(
  userId: string,
): Promise<number | null> {
  const supabase = await createClient();
  const live = await fetchLiveKitePortfolioCached(supabase, userId);

  if (live.status === "OK") {
    const portfolio = mapKiteHoldingsToPortfolio(live.holdings);
    return computePortfolioDayPnl(portfolio, live.dayPositions);
  }

  const cached = await getLatestPortfolioSnapshot(supabase, userId);
  if (cached && cached.holdings.length > 0) {
    return formatPortfolioHoldings(cached).day_pnl;
  }

  return null;
}

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const [market, dayPnl] = await Promise.all([
    fetchMarketTrend(),
    resolvePortfolioDayPnl(user.id),
  ]);

  const insight: DailyInsight = buildDailyInsight(dayPnl, market);

  return NextResponse.json({ insight });
}
