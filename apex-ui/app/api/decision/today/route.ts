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
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioMetrics,
  enrichPortfolioQuantitiesFromNetPositions,
  fetchZerodhaMargins,
  mapKiteHoldingsToPortfolio,
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
  buildDailyDecisionArtifact,
  currentMarketState,
  knownSource,
  unknownSource,
} from "@/services/decision/artifact";
import { projectArtifactDecision } from "@/types/decision";
import {
  getFinancialProfileFromDb,
  getLatestMentorOutput,
  getLatestPortfolioSnapshotWithMetrics,
} from "@/services/portfolio/repository";
import { buildUnconnectedWaitDecision } from "@/lib/onboarding/unconnectedTodayDecision";
import { createClient } from "@/lib/supabase/server";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { logger } from "@/lib/logging/logger";
import type {
  DailyDecisionArtifact,
  DailyDecisionOutput,
} from "@/types/decision";
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

type AllocationEnrichment = {
  decision: DailyDecisionOutput;
  availableCash: number | null;
  observedAt: string | null;
  brokerConnected: boolean;
};

async function enrichDecisionWithAllocation(
  supabase: Client,
  userId: string,
  intent: Intent,
  decision: DailyDecisionOutput,
  holdings: Portfolio["holdings"],
  _portfolioValue: number,
): Promise<AllocationEnrichment> {
  if (decision.action === "wait") {
    return {
      decision: { ...decision, opportunities: [], recommended_allocation: [] },
      availableCash: null,
      observedAt: null,
      brokerConnected: false,
    };
  }

  const connection = await getActiveBrokerConnection(supabase, userId);
  const brokerConnected = connection?.status === "active";

  if (!brokerConnected || !connection?.accessToken) {
    return {
      decision: { ...decision, opportunities: [], recommended_allocation: [] },
      availableCash: null,
      observedAt: null,
      brokerConnected: false,
    };
  }

  const marginsResult = await fetchZerodhaMargins(connection.accessToken);

  if (marginsResult.status !== "OK") {
    return {
      decision: { ...decision, opportunities: [], recommended_allocation: [] },
      availableCash: null,
      observedAt: null,
      brokerConnected: true,
    };
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

  return {
    decision: enriched,
    availableCash: marginsResult.marginAvailable,
    observedAt: new Date().toISOString(),
    brokerConnected: true,
  };
}

async function resolveEntryTiming(
  decision: DailyDecisionOutput,
): Promise<{ enter: boolean; reason: string }> {
  if (decision.action !== "buy" || !decision.stock) {
    return { enter: false, reason: "" };
  }

  return evaluateEntryTimingSafe(decision.stock);
}

function decisionResponsePayload(
  decision: DailyDecisionOutput,
  intent: Intent,
  artifact: DailyDecisionArtifact | null,
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
    artifact: artifact
      ? {
          schema_version: artifact.schema_version,
          decision_id: artifact.decision_id,
          decision_date: artifact.decision_date,
          frozen_at: artifact.frozen_at,
          intent: artifact.intent,
          action: artifact.action,
          symbol:
            artifact.symbol.status === "known" ? artifact.symbol.value : null,
          approved_size: artifact.approved_size,
          daily_verdict: artifact.daily_verdict,
          tradingLocked: artifact.tradingLocked,
          entryConfirmed: artifact.entryConfirmed,
          blockers: artifact.blockers,
          capital_state: artifact.capital_state,
          broker_state: artifact.broker_state,
          market_state: artifact.market_state,
          source_timestamps: artifact.source_timestamps,
          evidence_ids: artifact.evidence_ids,
        }
      : null,
    daily_verdict: artifact?.daily_verdict ?? null,
    trading_locked: artifact?.tradingLocked ?? null,
    entry_confirmed: artifact?.entryConfirmed ?? null,
    blockers: artifact?.blockers ?? [],
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
  const refresh = searchParams.get("refresh") === "1";

  const stored = await getTodayDailyDecision(supabase, user.id);

  // Wave 1 invariant: freeze-once. A valid stored artifact is the single
  // authority for today. Never recompute, never auto-execute again, never
  // overwrite unless an explicit ?refresh=1 arrives.
  if (stored && !refresh) {
    const projected = projectArtifactDecision(stored);
    const entryTiming = await resolveEntryTiming(projected);
    return NextResponse.json(
      decisionResponsePayload(projected, intent, stored, {
        source: "artifact",
        created_at: stored.frozen_at,
        entryTiming,
      }),
    );
  }

  let snapshot = await getLatestPortfolioSnapshotWithMetrics(
    supabase,
    user.id,
  );
  let portfolioObservedAt: string | null = null;

  const livePortfolio = await fetchLiveKitePortfolioCached(supabase, user.id);
  if (livePortfolio.status === "OK" && livePortfolio.holdings.length > 0) {
    const portfolio = enrichPortfolioQuantitiesFromNetPositions(
      mapKiteHoldingsToPortfolio(livePortfolio.holdings),
      livePortfolio.netPnlPositions,
    );
    const metrics = computePortfolioMetrics(portfolio);
    snapshot = {
      portfolio,
      total_value: metrics.totalValue,
      pnl: metrics.pnl,
    };
    portfolioObservedAt = new Date().toISOString();
  }

  if (!snapshot) {
    const onboardingDecision = buildUnconnectedWaitDecision(intent);
    return NextResponse.json(
      decisionResponsePayload(onboardingDecision, intent, null, {
        source: "onboarding",
      }),
    );
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

  const enrichment = await enrichDecisionWithAllocation(
    supabase,
    user.id,
    intent,
    baseDecision,
    snapshot.portfolio.holdings,
    snapshot.total_value || metrics.totalValue,
  );
  const decision = enrichment.decision;

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

  const entryTiming = await resolveEntryTiming(decision);
  const frozenAt = new Date().toISOString();
  const decisionDate = tradingDateKey();

  const artifact = buildDailyDecisionArtifact({
    userId: user.id,
    decisionDate,
    frozenAt,
    intent,
    decision,
    portfolio: {
      holdings: snapshot.portfolio.holdings,
      total_value: snapshot.total_value || metrics.totalValue,
      pnl: snapshot.pnl || metrics.pnl,
    },
    portfolioObservedAt,
    capital:
      enrichment.availableCash !== null && enrichment.observedAt
        ? knownSource(
            {
              available_cash_inr: Math.round(enrichment.availableCash),
              portfolio_value_inr: Math.round(
                snapshot.total_value || metrics.totalValue,
              ),
            },
            enrichment.observedAt,
          )
        : unknownSource(
            enrichment.brokerConnected
              ? "Broker margins unavailable"
              : "Broker not connected",
          ),
    broker: enrichment.brokerConnected
      ? knownSource(
          { broker: "zerodha", connection: "connected" },
          enrichment.observedAt ?? frozenAt,
        )
      : unknownSource("Broker not connected"),
    market: currentMarketState(marketTrend, frozenAt),
    entry:
      decision.action === "buy"
        ? entryTiming.enter
          ? knownSource(
              { confirmed: true, reason: entryTiming.reason || "Entry confirmed" },
              frozenAt,
            )
          : knownSource(
              { confirmed: false, reason: entryTiming.reason || "Entry not confirmed" },
              frozenAt,
            )
        : knownSource(
            { confirmed: true, reason: "Non-buy action" },
            frozenAt,
          ),
  });

  let persisted: DailyDecisionArtifact | null = null;
  try {
    await saveDailyDecision(supabase, user.id, artifact);
    persisted = await getTodayDailyDecision(supabase, user.id);
  } catch (error) {
    logger.warn("daily_decision_persist_failed", {
      route: "api/decision/today",
      userId: user.id,
      message: error instanceof Error ? error.message : "unknown",
    });
  }

  // Auto-execute only after the artifact has been persisted, and only
  // when it authorises the exact BUY. The autoExecute path validates.
  await executeTradeIfAutoEnabled(supabase, user.id, persisted, {
    portfolioValue: snapshot.total_value || metrics.totalValue,
    marketTrend,
  });

  const projection = persisted
    ? projectArtifactDecision(persisted)
    : decision;

  return NextResponse.json(
    decisionResponsePayload(projection, intent, persisted, {
      source: persisted ? "artifact" : "computed",
      created_at: persisted?.frozen_at ?? frozenAt,
      entryTiming,
    }),
  );
}
