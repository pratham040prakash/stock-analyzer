import type { DailyDecisionOutput } from "@/types/decision";
import type { DailyInsight } from "@/types/dailyInsight";
import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";
import type { TrustOutcomeSnapshot } from "@/services/decision/trustOutcome";

export type EvidenceLabel = "FACT" | "ASSUMPTION" | "ESTIMATE" | "OPINION";

export type EvidenceLine = {
  label: string;
  value: string;
  type: EvidenceLabel;
  source: string;
  confidence: string;
};

export type MorningBriefMeta = {
  built_at: string;
  scenario: string;
  market: string;
  session_phase: string;
};

export type MorningBriefDecision = {
  verdict: string | null;
  verdict_display: string;
  verdict_key: TodayExecutionKind;
  reason: string;
  confidence_level: number;
  confidence_band: string;
  last_updated: string;
  valid_until: string;
  cta_label: string;
  cta_action: string;
  decision_id: string;
  decision_source: string;
  headline: string;
  subline: string;
};

export type MorningBriefEvidence = {
  key_reasons: string[];
  supporting_signals: EvidenceLine[];
  conflicting_signals: EvidenceLine[];
  evidence_packet_id: string;
  evidence_available: boolean;
  gap_note: string;
};

export type MorningBriefTrust = {
  why_this_is_recommended: string;
  recommendation_confidence: string;
  trust_score: number;
  trust_delta: number;
  trust_message: string;
  broker_sync_state: "CONNECTED" | "TOKEN_EXPIRED" | "NOT_CONNECTED" | "STALE";
  broker_last_sync: string | null;
  portfolio_personalized: boolean;
  portfolio_scope: string;
  portfolio_summary: string;
  stale: boolean;
  stale_label: string;
  gaps: string[];
};

export type MorningBriefOpportunity = {
  visible: boolean;
  symbol: string;
  setup: string;
  lane: string;
};

export type MorningBriefPortfolio = {
  ready: boolean;
  holdings_count: number;
  cash_available_inr: number | null;
  tactical_pool_inr: number | null;
  sacred_core_excluded: boolean;
  summary: string;
  day_pnl: number | null;
  open_pnl: number | null;
};

export type MorningBriefRisk = {
  level: "High" | "Medium" | "Low";
  warnings: string[];
  session_ribbon: string[];
};

export type MorningBriefDiscipline = {
  process_score: number;
  streak_count: number;
  streak_message: string;
  followed_days: number;
  wait_days: number;
};

export type MorningBriefViewModel = {
  status: "ok" | "partial" | "error";
  meta: MorningBriefMeta;
  decision: MorningBriefDecision;
  evidence: MorningBriefEvidence;
  trust: MorningBriefTrust;
  opportunity: MorningBriefOpportunity;
  portfolio: MorningBriefPortfolio;
  risk: MorningBriefRisk;
  discipline: MorningBriefDiscipline;
  market: DailyInsight;
  failure_message: string | null;
  raw_decision?: DailyDecisionOutput | null;
  trust_snapshot?: TrustOutcomeSnapshot;
};

export type MorningBriefResponse = {
  status: "ok" | "partial" | "error";
  brief: MorningBriefViewModel | null;
  message?: string;
};
