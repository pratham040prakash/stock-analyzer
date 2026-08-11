import type { InvestorDnaViewModel } from "@/types/investorDna";

export type TraderStateWord = "Growing" | "Steady" | "Rebuilding" | "Focused";

export type TrustStateWord = "Honest" | "Learning" | "Earned";

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
  last_week_summary: string;
  this_week_summary: string;
  visible_miss: string | null;
  investor_dna: InvestorDnaViewModel;
};
