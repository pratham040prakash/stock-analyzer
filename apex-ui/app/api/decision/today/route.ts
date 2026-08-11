import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  buildExecutionPlan,
  deployableFundsForIntent,
} from "@/lib/allocation";
import { formatInr } from "@/lib/funds";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import { computeAllocationSafe } from "@/services/capital/allocationEngine";
import {
  getOpportunities,
  portfolioContextFromHoldings,
} from "@/lib/recommendations";
import { getActiveBrokerConnection } from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  fetchZerodhaMargins,
} from "@/services/brokers/zerodha";
import { getDecision } from "@/services/decision/engine";
import { logDecisionSafe } from "@/services/decision/decisionMemory";
import { getAdaptiveWeightsSafe } from "@/services/decision/selfLearning";
import { applyBearModeAmount } from "@/services/risk/riskControl";
import { getMarketRegime } from "@/services/decision/stockScoring";
import { evaluateEntryTimingSafe } from "@/services/execution/entryTiming";
import { executeTradeIfAutoEnabled } from "@/services/trade/autoExecute";
import {
  getTodayDailyDecision,
  saveDailyDecision,
} from "@/services/decision/repository";
import {
  getFinancialProfileFromDb,
  getLatestMentorOutput,
  getLatestPortfolioSnapshotWithMetrics,
} from "@/services/portfolio/repository";
import { createClient } from "@/lib/supabase/server";
import type { DailyDecisionOutput } from "@/types/decision";
import type { Intent } from "@/types/intent";
import { parseUserIntent, resolveIntent } from "@/types/intent";
import type { Portfolio } from "@/types/portfolio";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

function topAllocationPercent(holdings: Portfolio["holdings"]): number {
  const totalValue = holdings.reduce(
    (sum, holding) => sum + holding.quantity * holding.currentPrice,
    0,
  );

  if (totalValue <= 0 || holdings.length === 0) {
    return 0;
  }

  const topValue = Math.max(
    ...holdings.map((holding) => holding.quantity * holding.currentPrice),
  );

  return (topValue / totalValue) * 100;
}

async function enrichDecisionWithAllocation(
  supabase: Client,
  userId: string,
  intent: Intent,
  decision: DailyDecisionOutput,
  holdings: Portfolio["holdings"],
  portfolioValue: number,
): Promise<DailyDecisionOutput> {
  if (decision.action === "wait") {
    return { ...decision, opportunities: [], recommended_allocation: [] };
  }

  const connection = await getActiveBrokerConnection(supabase, userId);

  if (connection?.status !== "active") {
    return { ...decision, opportunities: [], recommended_allocation: [] };
  }

  const marginsResult = await fetchZerodhaMargins(connection.accessToken);

  if (marginsResult.status !== "OK") {
    return { ...decision, opportunities: [], recommended_allocation: [] };
  }

  const riskMetrics = portfolioRiskFromAllocation(
    topAllocationPercent(holdings),
  );
  const portfolio = portfolioContextFromHoldings(holdings);
  const opportunities = getOpportunities(intent, riskMetrics.risk_level, portfolio);
  const deployable = deployableFundsForIntent(
    marginsResult.marginAvailable,
    intent,
  );
  const recommended_allocation = buildExecutionPlan(
    opportunities,
    deployable,
    intent,
  );

  let enriched: DailyDecisionOutput = {
    ...decision,
    opportunities,
    recommended_allocation,
  };

  if (decision.action === "buy" && decision.stock) {
    const marketTrend = await getMarketRegime();
    const metrics = decision.confidenceMetrics;
    const allocation = computeAllocationSafe({
      probability: metrics?.probability,
      expectedReturn: metrics?.expectedReturn,
      expectedDrawdown: metrics?.expectedDrawdown,
      edgeScore: metrics?.edgeScore,
      structureScore: decision.structureScore,
      availableCash: marginsResult.marginAvailable,
    });

    let amount = Math.min(allocation.amount, deployable);
    amount = applyBearModeAmount(amount, marketTrend);

    enriched = {
      ...enriched,
      amount,
      allocationPercent: allocation.allocationPercent,
      allocationReason: allocation.reason,
      message:
        amount > 0
          ? marketTrend === "bearish"
            ? `Invest ${formatInr(amount)} in ${decision.stock} (bear mode — 50% size)`
            : `Invest ${formatInr(amount)} in ${decision.stock}`
          : allocation.reason === "Low edge"
            ? "No edge — skipping new investment today"
            : decision.message,
    };
  }

  return enriched;
}

async function resolveEntryTiming(decision: DailyDecisionOutput) {
  if (decision.action !== "buy" || !decision.stock) {
    return { enter: false, reason: "" };
  }

  return evaluateEntryTimingSafe(decision.stock);
}

function decisionResponsePayload(
  decision: DailyDecisionOutput,
  intent: Intent,
  extras: Record<string, unknown> = {},
) {
  const allocation = decision.recommended_allocation ?? [];

  return {
    decision,
    intent: decision.intent ?? intent,
    action: decision.action,
    message: decision.message ?? null,
    opportunities: decision.opportunities ?? null,
    allocation,
    validation: decision.validation ?? null,
    picks: decision.picks ?? null,
    amount: decision.amount ?? null,
    allocationPercent: decision.allocationPercent ?? null,
    allocationReason: decision.allocationReason ?? null,
    confidenceMetrics: decision.confidenceMetrics ?? null,
    structureScore: decision.structureScore ?? null,
    ...extras,
  };
}

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const intent = resolveIntent(parseUserIntent(searchParams.get("intent")));

  const stored = await getTodayDailyDecision(supabase, user.id);

  const snapshot = await getLatestPortfolioSnapshotWithMetrics(
    supabase,
    user.id,
  );

  if (!snapshot) {
    if (stored) {
      const { created_at, ...decision } = stored;
      const entryTiming = await resolveEntryTiming(decision);
      return NextResponse.json(
        decisionResponsePayload(decision, intent, {
          source: "database",
          created_at,
          entryTiming,
        }),
      );
    }

    return NextResponse.json({
      decision: null,
      intent: null,
      action: null,
      message: null,
      opportunities: null,
      allocation: [],
    });
  }

  const financialProfile = await getFinancialProfileFromDb(supabase, user.id);
  const lastMentorOutput = await getLatestMentorOutput(supabase, user.id);

  const metrics = computePortfolioMetrics(snapshot.portfolio);
  const adaptiveSignalWeights = await getAdaptiveWeightsSafe(
    supabase,
    user.id,
  );
  const baseDecision = await getDecision({
    portfolioSnapshot: {
      holdings: snapshot.portfolio.holdings,
      total_value: snapshot.total_value || metrics.totalValue,
      pnl: snapshot.pnl || metrics.pnl,
    },
    financialProfile,
    lastMentorOutput,
    intent,
    adaptiveSignalWeights,
    supabase,
    userId: user.id,
  });

  const decision = await enrichDecisionWithAllocation(
    supabase,
    user.id,
    intent,
    baseDecision,
    snapshot.portfolio.holdings,
    snapshot.total_value || metrics.totalValue,
  );

  const marketTrend = await getMarketRegime();
  await logDecisionSafe(supabase, decision, {
    userId: user.id,
    marketTrend,
    intent,
    portfolioSnapshot: {
      holdings: snapshot.portfolio.holdings,
      total_value: snapshot.total_value || metrics.totalValue,
      pnl: snapshot.pnl || metrics.pnl,
    },
  });

  // BUG-003: auto-trade at most once per trading day — not on every refresh/intent poll.
  if (!stored) {
    await executeTradeIfAutoEnabled(supabase, user.id, decision, {
      portfolioValue: snapshot.total_value || metrics.totalValue,
      marketTrend,
    });
  }

  try {
    await saveDailyDecision(supabase, user.id, decision);
  } catch {
    // History persistence should not block today's decision.
  }

  const storedAfterSave = await getTodayDailyDecision(supabase, user.id);
  const entryTiming = await resolveEntryTiming(decision);

  return NextResponse.json(
    decisionResponsePayload(decision, intent, {
      source: storedAfterSave ? "database" : "computed",
      created_at: storedAfterSave?.created_at ?? stored?.created_at,
      entryTiming,
    }),
  );
}
