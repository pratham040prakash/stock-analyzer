export type QuarterlyThesisProgress = {
  symbol: string;
  status: "documented" | "missing";
  note: string;
};

export type QuarterlyReviewViewModel = {
  built_at: string;
  quarter_label: string;
  headline: string;
  summary: string;
  discipline_score: number;
  aligned_days: number;
  deviated_days: number;
  concentration_warning: string | null;
  sacred_core_ok: boolean;
  action_items: string[];
  thesis_progress: QuarterlyThesisProgress[];
  goal_framing: string;
};
