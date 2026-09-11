import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { buildDailyInsight } from "@/lib/dailyInsight";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioDayPnl,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { getTapeRegimeSafe } from "@/services/market/regime";
import { fetchMarketTrend } from "@/services/market/trend";
import { formatPortfolioHoldings } from "@/services/portfolio/format";
import { getLatestPortfolioSnapshot } from "@/services/portfolio/repository";
import { createClient } from "@/lib/supabase/server";
import type { DailyInsight } from "@/types/dailyInsight";
import { getTodayDailyDecision } from "@/services/decision/repository";

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

  const [market, tape, dayPnl, artifact] = await Promise.all([
    fetchMarketTrend(),
    getTapeRegimeSafe(),
    resolvePortfolioDayPnl(user.id),
    getTodayDailyDecision(supabase, user.id),
  ]);

  const insight: DailyInsight = buildDailyInsight(
    dayPnl,
    market,
    tape,
    artifact
      ? {
          daily_verdict: artifact.daily_verdict,
          tradingLocked: artifact.tradingLocked,
          blockers: artifact.blockers,
        }
      : null,
  );

  return NextResponse.json({ insight });
}
