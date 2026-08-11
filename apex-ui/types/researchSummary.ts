export type ResearchVerdict = "YES" | "NO" | "WAIT";

export type ResearchQuestion = {
  id: string;
  prompt: string;
  answer: string;
  confidence: "high" | "medium" | "low";
};

export type ResearchSummaryViewModel = {
  symbol: string;
  built_at: string;
  source: "alpha_ai" | "market_data" | "partial";
  verdict: ResearchVerdict;
  verdict_label: string;
  headline: string;
  summary: string;
  score: number | null;
  grade: string | null;
  recommendation: string | null;
  risk_level: string | null;
  questions: ResearchQuestion[];
  gaps: string[];
  alpha_available: boolean;
};
