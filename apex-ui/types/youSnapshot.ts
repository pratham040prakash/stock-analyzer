import type { InvestorDnaViewModel } from "@/types/investorDna";

export type TraderStateWord = "Growing" | "Steady" | "Rebuilding" | "Focused";

export type TrustStateWord = "Honest" | "Learning" | "Earned";

export type CdqsInterpretation =
  | "trustworthy"
  | "calibrating"
  | "trust_failure"
  | "insufficient_data";

export type YouSnapshotViewModel = {
  built_at: string;
  trader_state: TraderStateWord;
  trader_narrative: string;
  coaching_insight: string;
  forward_line: string;
  process_score: number;
  streak_count: number;
  trust_score: number;
  trust_state: TrustStateWord;
  trust_narrative: string;
  cdqs_score_percent: number | null;
  cdqs_interpretation: CdqsInterpretation;
  cdqs_headline: string;
  cdqs_detail: string;
  cdqs_sample_size: number;
  outcome_loop_visible: boolean;
  outcome_loop_stock: string | null;
  outcome_loop_closed_at: string | null;
  outcome_loop_result: string | null;
  outcome_loop_discipline: number | null;
  outcome_loop_execution: number | null;
  outcome_loop_trust_delta: number | null;
  outcome_loop_summary: string | null;
  override_count_14d: number;
  override_follow_rate_14d: number | null;
  override_headline: string;
  override_detail: string;
  last_week_summary: string;
  this_week_summary: string;
  visible_miss: string | null;
  investor_dna: InvestorDnaViewModel;
};
