import type { MorningBriefViewModel } from "@/types/morningBrief";
import type { VerdictCanvasProps } from "@/components/dailyLoop/VerdictCanvas";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { DailyVerdict } from "@/lib/dailyLoop/dailyVerdict";

export function projectVerdictCanvasProps(
  brief: MorningBriefViewModel,
  options?: {
    connectionStatus?: ConnectionStatus;
    brokerStepCompleted?: boolean;
    brokerStepSkipped?: boolean;
    pollError?: string | null;
    entryConfirmed?: boolean;
    portfolioDayPnl?: number | null;
    portfolioValue?: number | null;
  },
): VerdictCanvasProps {
  return {
    verdictWord: brief.decision.verdict_display,
    dailyVerdict: brief.decision.daily_verdict,
    headline: brief.decision.headline,
    subline: brief.decision.subline,
    executionKind: brief.decision.verdict_key,
    trustScore: brief.trust.trust_score,
    trustDelta: brief.trust.trust_delta,
    trustMessage: brief.trust.trust_message,
    evidenceTeaser:
      brief.evidence.key_reasons[0] ?? brief.decision.reason ?? undefined,
    confidence: brief.decision.confidence_level,
    portfolioStale: brief.trust.stale,
    pollError: options?.pollError ?? brief.failure_message,
    connectionStatus:
      options?.connectionStatus ??
      (brief.trust.broker_sync_state === "CONNECTED"
        ? "CONNECTED"
        : brief.trust.broker_sync_state === "TOKEN_EXPIRED"
          ? "TOKEN_EXPIRED"
          : "NOT_CONNECTED"),
    brokerStepCompleted: options?.brokerStepCompleted ?? false,
    brokerStepSkipped: options?.brokerStepSkipped ?? false,
    doneForToday:
      brief.decision.daily_verdict === "wait" ||
      brief.decision.daily_verdict === "pause",
    ctaLabel: brief.decision.cta_label,
    tradingLocked: brief.decision.daily_verdict !== "trade",
  };
}

export function runProjectVerdictSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Project verdict self-check failed: ${message}`);
    }
  };

  const brief: MorningBriefViewModel = {
    status: "ok",
    meta: {
      built_at: new Date().toISOString(),
      scenario: "grow",
      market: "Mixed",
      session_phase: "Market open",
    },
    decision: {
      verdict: "wait",
      verdict_display: "Wait",
      daily_verdict: "wait" as DailyVerdict,
      verdict_key: "WAIT",
      reason: "Stay patient.",
      confidence_level: 60,
      confidence_band: "Moderate",
      last_updated: new Date().toISOString(),
      valid_until: new Date().toISOString(),
      cta_label: "Stay patient",
      cta_action: "wait",
      decision_id: "test",
      decision_source: "decision_engine",
      headline: "Wait today",
      subline: "No edge yet.",
    },
    evidence: {
      key_reasons: ["Trend neutral"],
      supporting_signals: [],
      conflicting_signals: [],
      evidence_packet_id: "test",
      evidence_available: true,
      gap_note: "",
    },
    trust: {
      why_this_is_recommended: "Trust steady",
      recommendation_confidence: "Moderate",
      trust_score: 72,
      trust_delta: 0,
      trust_message: "Steady discipline",
      broker_sync_state: "CONNECTED",
      broker_last_sync: new Date().toISOString(),
      portfolio_personalized: true,
      portfolio_scope: "live",
      portfolio_summary: "Synced",
      stale: false,
      stale_label: "",
      gaps: [],
    },
    opportunity: { visible: false, symbol: "", setup: "", lane: "" },
    portfolio: {
      ready: true,
      holdings_count: 2,
      cash_available_inr: 1000,
      tactical_pool_inr: null,
      sacred_core_excluded: true,
      summary: "Portfolio ready",
      day_pnl: 0,
      open_pnl: 0,
    },
    risk: { level: "Low", warnings: [], session_ribbon: [] },
    discipline: {
      process_score: 70,
      streak_count: 2,
      streak_message: "Steady",
      followed_days: 3,
      wait_days: 2,
    },
    market: {
      day_pnl: 0,
      market_trend: "neutral",
      market_label: "Mixed",
      guidance: "Stay steady",
      pnl_line: "Flat today",
    },
    failure_message: null,
  };

  const props = projectVerdictCanvasProps(brief);
  assert(props.verdictWord === "Wait", "Verdict word must map from brief");
  assert(props.dailyVerdict === "wait", "Daily verdict must map from brief");
  assert(props.headline === "Wait today", "Headline must pass through");
}
