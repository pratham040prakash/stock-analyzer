import { buildCapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import { buildDailyInsight } from "@/lib/dailyInsight";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import {
  resolveTodayHero,
  resolveVerdictWord,
  type TodayExecutionKind,
} from "@/lib/dailyLoop/todaySurface";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
import { getDisciplineStreak } from "@/services/discipline/streak";
import { buildDisciplineProcessScore } from "@/services/review/disciplineScore";
import type { MorningBriefViewModel } from "@/types/morningBrief";
import type { DailyDecisionOutput } from "@/types/decision";
import type { Intent } from "@/types/intent";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";
import { getMarketSessionPhase } from "@/lib/broker/marketSession";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import { getUserTrustSnapshot } from "@/services/decision/trustOutcome";
import { getDecision } from "@/services/decision/engine";
import { getAdaptiveWeightsSafe } from "@/services/decision/selfLearning";
import { getTodayDailyDecision } from "@/services/decision/repository";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioDayPnl,
  computePortfolioMetrics,
  computeZerodhaPositionsPnl,
  enrichPortfolioQuantitiesFromNetPositions,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { fetchMarketTrend } from "@/services/market/trend";
import { formatPortfolioHoldings } from "@/services/portfolio/format";
import {
  getFinancialProfileFromDb,
  getLatestMentorOutput,
  getLatestPortfolioSnapshotWithMetrics,
} from "@/services/portfolio/repository";

type Client = SupabaseClient<Database>;

function confidenceBand(level: number): string {
  if (level >= 75) {
    return "High";
  }

  if (level >= 55) {
    return "Moderate";
  }

  return "Low";
}

function mapExecutionKind(
  action: string,
  capitalKind: TodayExecutionKind,
): TodayExecutionKind {
  if (capitalKind !== "WAIT") {
    return capitalKind;
  }

  if (action === "buy") {
    return "BUY";
  }

  if (action === "sell") {
    return "SELL";
  }

  if (action === "wait") {
    return "WAIT";
  }

  return "OBSERVE";
}

function buildEvidence(decision: DailyDecisionOutput): MorningBriefViewModel["evidence"] {
  const keyReasons: string[] = [];

  if (decision.reason) {
    keyReasons.push(decision.reason);
  }

  for (const factor of decision.confidence_factors ?? []) {
    if (keyReasons.length >= 3) {
      break;
    }

    keyReasons.push(factor);
  }

  const supporting = (decision.confidence_factors ?? []).slice(0, 3).map((factor) => ({
    label: "Signal",
    value: factor,
    type: "FACT" as const,
    source: "decision_engine",
    confidence: confidenceBand(decision.confidence ?? 50),
  }));

  const conflicting: MorningBriefViewModel["evidence"]["conflicting_signals"] = [];

  if (decision.validation && decision.validation.risk_ok === false) {
    conflicting.push({
      label: "Risk",
      value: "Risk checks flagged caution",
      type: "FACT",
      source: "risk_control",
      confidence: "High",
    });
  }

  return {
    key_reasons: keyReasons,
    supporting_signals: supporting,
    conflicting_signals: conflicting,
    evidence_packet_id: `brief-${tradingDateKey()}`,
    evidence_available: keyReasons.length > 0,
    gap_note:
      keyReasons.length === 0
        ? "Evidence is limited today — treat guidance as low confidence."
        : "",
  };
}

async function loadDecisionReadOnly(
  supabase: Client,
  userId: string,
  intent: Intent,
): Promise<{
  decision: DailyDecisionOutput | null;
  portfolioValue: number;
  topAllocationPct: number;
  brokerSyncState: MorningBriefViewModel["trust"]["broker_sync_state"];
}> {
  const stored = await getTodayDailyDecision(supabase, userId);
  let snapshot = await getLatestPortfolioSnapshotWithMetrics(supabase, userId);
  let brokerSyncState: MorningBriefViewModel["trust"]["broker_sync_state"] =
    "NOT_CONNECTED";

  const livePortfolio = await fetchLiveKitePortfolioCached(supabase, userId);

  if (livePortfolio.status === "TOKEN_EXPIRED") {
    brokerSyncState = "TOKEN_EXPIRED";
  } else if (livePortfolio.status === "OK") {
    brokerSyncState = "CONNECTED";
    if (livePortfolio.holdings.length > 0) {
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
    }
  } else if (livePortfolio.status === "ERROR") {
    brokerSyncState = "STALE";
  }

  if (!snapshot) {
    if (stored) {
      const { created_at: _createdAt, ...decision } = stored;
      return {
        decision,
        portfolioValue: 0,
        topAllocationPct: 0,
        brokerSyncState,
      };
    }

    return {
      decision: null,
      portfolioValue: 0,
      topAllocationPct: 0,
      brokerSyncState,
    };
  }

  const financialProfile = await getFinancialProfileFromDb(supabase, userId);
  const lastMentorOutput = await getLatestMentorOutput(supabase, userId);
  const metrics = computePortfolioMetrics(snapshot.portfolio);
  const adaptiveSignalWeights = await getAdaptiveWeightsSafe(supabase, userId);

  const decision =
    stored ??
    (await getDecision({
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
      userId,
    }));

  const formatted = formatPortfolioHoldings(snapshot.portfolio);

  return {
    decision,
    portfolioValue: snapshot.total_value || metrics.totalValue,
    topAllocationPct: formatted.top_allocation_pct ?? 0,
    brokerSyncState,
  };
}

export async function assembleMorningBrief(
  supabase: Client,
  userId: string,
  intent: Intent,
): Promise<MorningBriefViewModel> {
  const builtAt = new Date().toISOString();
  const sessionPhase = getMarketSessionPhase(new Date());

  const [decisionBundle, trust, market, historyBundle, live, streakSnapshot] =
    await Promise.all([
      loadDecisionReadOnly(supabase, userId, intent),
      getUserTrustSnapshot(supabase, userId),
      fetchMarketTrend(),
      getDisciplineHistory(supabase, userId, 14),
      fetchLiveKitePortfolioCached(supabase, userId),
      getDisciplineStreak(supabase, userId),
    ]);

  const decision = decisionBundle.decision;
  const processScore = buildDisciplineProcessScore(
    historyBundle.summary,
    streakSnapshot.streakCount,
  );
  const dayPnl =
    live.status === "OK"
      ? computePortfolioDayPnl(
          mapKiteHoldingsToPortfolio(live.holdings),
          live.dayPositions,
        )
      : null;
  const openPnl =
    live.status === "OK"
      ? computeZerodhaPositionsPnl(live.holdings, live.netPnlPositions)
      : null;

  const insight = buildDailyInsight(dayPnl, market);

  if (!decision) {
    return {
      status: "partial",
      meta: {
        built_at: builtAt,
        scenario: intent,
        market: market.label,
        session_phase: sessionPhase,
      },
      decision: {
        verdict: "WAIT",
        verdict_display: "WAIT",
        verdict_key: "WAIT",
        reason: "Connect your broker and complete your profile to unlock today's brief.",
        confidence_level: 0,
        confidence_band: "Low",
        last_updated: builtAt,
        valid_until: builtAt,
        cta_label: "Connect broker",
        cta_action: "connect_broker",
        decision_id: `brief-${tradingDateKey()}`,
        decision_source: "none",
        headline: "Today's brief unavailable",
        subline: "We need portfolio context before recommending an action.",
      },
      evidence: {
        key_reasons: [],
        supporting_signals: [],
        conflicting_signals: [],
        evidence_packet_id: `brief-${tradingDateKey()}`,
        evidence_available: false,
        gap_note: "No decision available.",
      },
      trust: {
        why_this_is_recommended: trust.trustMessage,
        recommendation_confidence: "Low",
        trust_score: trust.trustScore,
        trust_delta: trust.trustDelta,
        trust_message: trust.trustMessage,
        broker_sync_state: decisionBundle.brokerSyncState,
        broker_last_sync: builtAt,
        portfolio_personalized: false,
        portfolio_scope: "none",
        portfolio_summary: "Portfolio not synced",
        stale: decisionBundle.brokerSyncState !== "CONNECTED",
        stale_label: "Connect Zerodha for personalized guidance.",
        gaps: ["portfolio"],
      },
      opportunity: { visible: false, symbol: "", setup: "", lane: "" },
      portfolio: {
        ready: false,
        holdings_count: 0,
        cash_available_inr: null,
        tactical_pool_inr: null,
        sacred_core_excluded: true,
        summary: "Portfolio unavailable",
        day_pnl: dayPnl,
        open_pnl: openPnl,
      },
      risk: {
        level: "Low",
        warnings: [],
        session_ribbon: [sessionPhase],
      },
      discipline: {
        process_score: processScore.score,
        streak_count: processScore.streakCount,
        streak_message: processScore.message,
        followed_days: historyBundle.summary.followedDays,
        wait_days: historyBundle.summary.waitDays,
      },
      market: insight,
      failure_message: "Decision unavailable",
      trust_snapshot: trust,
    };
  }

  const capitalDecision = buildCapitalDecision({
    intent,
    action: decision.action,
    stock: decision.stock,
    picks: decision.picks,
    allocationPercent: decision.allocationPercent,
    suggested_sell_percent: decision.suggested_sell_percent,
    topAllocationPct: decisionBundle.topAllocationPct,
    availableCash: undefined,
    portfolioValue: decisionBundle.portfolioValue,
    entryTiming: { enter: decision.action === "buy" },
    confidence: decision.confidence,
  });

  const hero = resolveTodayHero(capitalDecision, {
    suggestedSellPercent: decision.suggested_sell_percent,
  });
  const executionKind = mapExecutionKind(decision.action, hero.executionKind);
  const verdictDisplay = resolveVerdictWord(executionKind);
  const risk = portfolioRiskFromAllocation(decisionBundle.topAllocationPct);

  const stale =
    decisionBundle.brokerSyncState === "TOKEN_EXPIRED" ||
    decisionBundle.brokerSyncState === "STALE" ||
    decisionBundle.brokerSyncState === "NOT_CONNECTED";

  const warnings: string[] = [];
  if (risk.risk_level === "High") {
    warnings.push("Portfolio concentration is elevated.");
  }
  if (decision.validation?.risk_ok === false) {
    warnings.push("Risk controls flagged today's setup.");
  }
  if (stale) {
    warnings.push("Live broker data may be stale.");
  }

  const topOpportunity = decision.opportunities?.[0];

  return {
    status: stale ? "partial" : "ok",
    meta: {
      built_at: builtAt,
      scenario: intent,
      market: market.label,
      session_phase: sessionPhase,
    },
    decision: {
      verdict: decision.action,
      verdict_display: verdictDisplay,
      verdict_key: executionKind,
      reason: decision.reason ?? decision.message ?? capitalDecision.primaryActionDetail,
      confidence_level: Math.round(decision.confidence ?? 50),
      confidence_band: confidenceBand(decision.confidence ?? 50),
      last_updated: builtAt,
      valid_until: builtAt,
      cta_label:
        executionKind === "BUY"
          ? "Review entry plan"
          : executionKind === "SELL"
            ? "Review trim plan"
            : "Stay patient",
      cta_action: executionKind.toLowerCase(),
      decision_id: `brief-${tradingDateKey()}-${decision.stock ?? "none"}`,
      decision_source: "decision_engine",
      headline: hero.headline,
      subline: hero.subline,
    },
    evidence: buildEvidence(decision),
    trust: {
      why_this_is_recommended: trust.trustMessage,
      recommendation_confidence: confidenceBand(decision.confidence ?? 50),
      trust_score: trust.trustScore,
      trust_delta: trust.trustDelta,
      trust_message: trust.trustMessage,
      broker_sync_state: decisionBundle.brokerSyncState,
      broker_last_sync: builtAt,
      portfolio_personalized: decisionBundle.brokerSyncState === "CONNECTED",
      portfolio_scope: decisionBundle.brokerSyncState === "CONNECTED" ? "live" : "cached",
      portfolio_summary:
        decisionBundle.brokerSyncState === "CONNECTED"
          ? "Synced with Zerodha holdings."
          : "Using cached portfolio context.",
      stale,
      stale_label: stale ? "Live data may be stale — reconnect if numbers look off." : "",
      gaps: stale ? ["broker_sync"] : [],
    },
    opportunity: {
      visible: Boolean(topOpportunity?.name ?? decision.stock),
      symbol: topOpportunity?.name ?? decision.stock ?? "",
      setup: topOpportunity?.type ?? decision.reason ?? "",
      lane: intent,
    },
    portfolio: {
      ready: decisionBundle.portfolioValue > 0,
      holdings_count: live.status === "OK" ? live.holdings.length : 0,
      cash_available_inr: null,
      tactical_pool_inr: decision.amount ?? null,
      sacred_core_excluded: true,
      summary:
        decisionBundle.portfolioValue > 0
          ? `Portfolio value ~₹${Math.round(decisionBundle.portfolioValue).toLocaleString("en-IN")}.`
          : "Portfolio value unavailable.",
      day_pnl: dayPnl,
      open_pnl: openPnl,
    },
    risk: {
      level: risk.risk_level,
      warnings,
      session_ribbon: [sessionPhase, market.label],
    },
    discipline: {
      process_score: processScore.score,
      streak_count: processScore.streakCount,
      streak_message: processScore.message,
      followed_days: historyBundle.summary.followedDays,
      wait_days: historyBundle.summary.waitDays,
    },
    market: insight,
    failure_message: null,
    raw_decision: decision,
    trust_snapshot: trust,
  };
}

export function runMorningBriefSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Morning brief self-check failed: ${message}`);
    }
  };

  const evidence = buildEvidence({
    decision: "WAIT",
    action: "wait",
    actions: ["wait"],
    confidence: 62,
    reason: "Market regime is mixed.",
    confidence_factors: ["Trend neutral", "Volume stable"],
  });

  assert(evidence.key_reasons.length >= 2, "Evidence must include reason and factors");
  assert(evidence.evidence_available, "Evidence must be available when reasons exist");
}
