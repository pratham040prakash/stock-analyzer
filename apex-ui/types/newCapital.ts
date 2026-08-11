export type NewCapitalRecommendation = {
  deployable_inr: number;
  headline: string;
  guidance: string;
  suggested_symbols: string[];
  sacred_core_note: string | null;
};

export type NewCapitalViewModel = {
  built_at: string;
  available: NewCapitalRecommendation | null;
  message: string;
};
