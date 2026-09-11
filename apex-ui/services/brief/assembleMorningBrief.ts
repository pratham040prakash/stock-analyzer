import {
  buildDailyVerdictPresentation,
  countConsecutiveLossDays,
} from "@/lib/dailyLoop/dailyVerdict";
import { buildCapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import { buildDailyInsight } from "@/lib/dailyInsight";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import {
  resolveTodayHero,
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
import { getTodayDailyDecision } from "@/services/decision/repository";
import { projectArtifactDecision } from "@/types/decision";
import type { DailyDecisionArtifact } from "@/types/decision";
import { fetchLiveKitePortfolioCached } from "@/services/broker/kitePortfolio";
import {
  computePortfolioDayPnl,
  computePortfolioMetrics,
  computeZerodhaPositionsPnl,
  enrichPortfolioQuantitiesFromNetPositions,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { getTapeRegimeSafe } from "@/services/market/regime";
import { fetchMarketTrend } from "@/services/market/trend";
import { formatPortfolioHoldings } from "@/services/portfolio/format";
import { isSacredCoreSymbol } from "@/services/portfolio/allocationPolicy";
import {
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
  _intent: Intent,
): Promise<{
  artifact: DailyDecisionArtifact | null;
  decision: DailyDecisionOutput | null;
  portfolioValue: number;
  topAllocationPct: number;
  brokerSyncState: MorningBriefViewModel["trust"]["broker_sync_state"];
}> {
  // Wave 1 invariant: Brief is projection-only. It never produces a
  // decision — it reads the frozen artifact or falls back to WAIT.
  const artifact = await getTodayDailyDecision(supabase, userId);
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

  const decision = artifact ? projectArtifactDecision(artifact) : null;

  if (!snapshot) {
    const frozenValue = artifact?.frozen_portfolio.total_value_inr ?? 0;
    return {
      artifact,
      decision,
      portfolioValue: frozenValue,
      topAllocationPct: 0,
      brokerSyncState,
    };
  }

  const metrics = computePortfolioMetrics(snapshot.portfolio);
  const formatted = formatPortfolioHoldings(snapshot.portfolio);

  return {
    artifact,
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

  const [decisionBundle, trust, market, tape, historyBundle, live, streakSnapshot] =
    await Promise.all([
      loadDecisionReadOnly(supabase, userId, intent),
      getUserTrustSnapshot(supabase, userId),
      fetchMarketTrend(),
      getTapeRegimeSafe(),
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

  const insight = buildDailyInsight(dayPnl, market, tape);

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
        verdict_display: "Wait",
        daily_verdict: "wait",
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

  const artifact = decisionBundle.artifact;
  const artifactCash =
    artifact?.capital_state.status === "known"
      ? artifact.capital_state.value.available_cash_inr
      : undefined;
  const artifactEntryConfirmed = Boolean(artifact?.entryConfirmed);

  const capitalDecision = buildCapitalDecision({
    intent,
    action: decision.action,
    stock: decision.stock,
    picks: decision.picks,
    allocationPercent: decision.allocationPercent,
    suggested_sell_percent: decision.suggested_sell_percent,
    topAllocationPct: decisionBundle.topAllocationPct,
    availableCash: artifactCash,
    portfolioValue: decisionBundle.portfolioValue,
    entryTiming: { enter: artifactEntryConfirmed },
    confidence: decision.confidence,
  });

  const hero = resolveTodayHero(capitalDecision, {
    suggestedSellPercent: decision.suggested_sell_percent,
  });
  const executionKind = mapExecutionKind(decision.action, hero.executionKind);
  const portfolioHoldings =
    live.status === "OK" && live.holdings.length > 0
      ? formatPortfolioHoldings(
          enrichPortfolioQuantitiesFromNetPositions(
            mapKiteHoldingsToPortfolio(live.holdings),
            live.netPnlPositions,
          ),
        ).holdings
      : [];
  const topSymbol = portfolioHoldings[0]?.tradingsymbol;
  const targetSymbol = decision.stock ?? hero.symbol;
  const targetIsSacredCore = targetSymbol
    ? isSacredCoreSymbol({
        symbol: targetSymbol,
        holdings: portfolioHoldings,
        topSymbol,
      })
    : false;
  const consecutiveLossDays = countConsecutiveLossDays(
    historyBundle.history,
    historyBundle.days,
  );
  const verdictPresentation = buildDailyVerdictPresentation({
    verdictInput: {
      executionKind,
      entryConfirmed: artifactEntryConfirmed,
      consecutiveLossDays,
      portfolioDayPnl: dayPnl,
      portfolioValue: decisionBundle.portfolioValue,
      riskBlocked: decision.validation?.risk_ok === false,
      targetIsSacredCore,
      targetSymbol: targetSymbol ?? undefined,
      tapeHardWait: tape.hardWait,
    },
    heroHeadline: hero.headline,
    heroSubline: hero.subline,
  });
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
  if (targetIsSacredCore && executionKind === "BUY") {
    warnings.push("Today's symbol is in your sacred core — tactical buys only.");
  }
  if (stale) {
    warnings.push("Live broker data may be stale.");
  }
  if (tape.hardWait) {
    warnings.push(tape.briefLine);
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
      verdict_display: verdictPresentation.displayWord,
      daily_verdict: verdictPresentation.verdict,
      verdict_key: executionKind,
      reason: decision.reason ?? decision.message ?? capitalDecision.primaryActionDetail,
      confidence_level: Math.round(decision.confidence ?? 50),
      confidence_band: confidenceBand(decision.confidence ?? 50),
      last_updated: builtAt,
      valid_until: builtAt,
      cta_label: verdictPresentation.ctaLabel,
      cta_action: verdictPresentation.verdict,
      decision_id: `brief-${tradingDateKey()}-${decision.stock ?? "none"}`,
      decision_source: "decision_engine",
      headline: verdictPresentation.headline,
      subline: verdictPresentation.subline,
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
      cash_available_inr: artifactCash ?? null,
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
