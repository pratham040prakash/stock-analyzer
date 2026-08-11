import { buildAllocationPolicySummary } from "@/services/portfolio/allocationPolicy";
import { scoreAllHoldings } from "@/services/portfolio/holdingHealth";
import { getOpenMonitorPositions } from "@/services/monitor/openPositions";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioMetrics,
  enrichPortfolioQuantitiesFromNetPositions,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { formatPortfolioHoldings } from "@/services/portfolio/format";
import { getLatestPortfolioSnapshot } from "@/services/portfolio/repository";
import type { PortfolioOverviewViewModel } from "@/types/portfolioOverview";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export async function assemblePortfolioOverview(
  supabase: Client,
  userId: string,
  cashAvailableInr?: number | null,
): Promise<PortfolioOverviewViewModel> {
  const live = await fetchLiveKitePortfolioCached(supabase, userId);
  const monitor = await getOpenMonitorPositions(supabase, userId);
  const positions = monitor.positions;

  if (live.status === "NOT_CONNECTED" || live.status === "TOKEN_EXPIRED") {
    const cached = await getLatestPortfolioSnapshot(supabase, userId);
    if (!cached || cached.holdings.length === 0) {
      return {
        status: live.status === "TOKEN_EXPIRED" ? "partial" : "error",
        portfolio: {
          status: live.status,
          holdings: [],
        },
        allocation: null,
        health: [],
        positions: [],
        research_symbol: null,
        message: "Connect Zerodha to load portfolio overview.",
      };
    }

    const formatted = formatPortfolioHoldings(cached);
    const allocation = buildAllocationPolicySummary({
      holdings: formatted.holdings,
      cashAvailableInr,
      totalValue: formatted.total_value,
      topSymbol: formatted.top_symbol ?? undefined,
      topAllocationPct: formatted.top_allocation_pct,
    });

    return {
      status: "partial",
      portfolio: {
        status: live.status,
        stale: true,
        holdings: formatted.holdings,
        total_value: formatted.total_value,
        total_pnl: formatted.total_pnl,
        concentrated: formatted.concentrated,
        top_symbol: formatted.top_symbol ?? undefined,
        top_allocation_pct: formatted.top_allocation_pct,
        risk_score: formatted.risk_score,
        risk_level: formatted.risk_level,
      },
      allocation,
      health: scoreAllHoldings(formatted.holdings, {
        concentrated: formatted.concentrated,
        topSymbol: formatted.top_symbol ?? undefined,
      }),
      positions,
      research_symbol: formatted.top_symbol ?? formatted.holdings[0]?.tradingsymbol ?? null,
    };
  }

  if (live.status === "ERROR") {
    return {
      status: "error",
      portfolio: { status: "ERROR", holdings: [], message: live.message },
      allocation: null,
      health: [],
      positions,
      research_symbol: null,
      message: live.message,
    };
  }

  const portfolio = enrichPortfolioQuantitiesFromNetPositions(
    mapKiteHoldingsToPortfolio(live.holdings),
    live.netPnlPositions,
  );
  const formatted = formatPortfolioHoldings(portfolio, live.dayPositions);
  const metrics = computePortfolioMetrics(portfolio);

  const allocation = buildAllocationPolicySummary({
    holdings: formatted.holdings,
    cashAvailableInr,
    totalValue: metrics.totalValue,
    topSymbol: formatted.top_symbol ?? undefined,
    topAllocationPct: formatted.top_allocation_pct,
  });

  return {
    status: "ok",
    portfolio: {
      status: "OK",
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
    allocation,
    health: scoreAllHoldings(formatted.holdings, {
      concentrated: formatted.concentrated,
      topSymbol: formatted.top_symbol ?? undefined,
    }),
    positions,
    research_symbol: formatted.top_symbol ?? formatted.holdings[0]?.tradingsymbol ?? null,
  };
}
