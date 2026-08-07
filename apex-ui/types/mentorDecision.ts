export type MentorAction = "reduce" | "add" | "hold" | "observe";

export type MentorUrgency = "low" | "medium" | "high";

export type MentorConfidence = "low" | "medium" | "high";

export type MentorFocusArea =
  | "portfolio"
  | "stock"
  | "behavior"
  | "risk"
  | "opportunity";

export type StockSuggestion = "add" | "reduce" | "hold";

export type AffectedStock = {
  symbol: string;
  suggestion: StockSuggestion;
  reason: string;
  weight?: number;
};

export type FinancialContext = {
  investableSurplus: number;
  utilizationLevel: "under" | "optimal" | "over";
  message: string;
};

export type SessionHistory = {
  lastReviewedStock?: string;
  pastDecisions: { symbol: string; action: string }[];
  visitCount: number;
};

export type MentorDecision = {
  summary: string;
  action: MentorAction;
  urgency: MentorUrgency;
  confidence: MentorConfidence;
  focusArea: MentorFocusArea;
  primaryInsight: string;
  reasoning: string[];
  affectedStocks?: AffectedStock[];
  financialContext?: FinancialContext;
  behavioralInsight?: string;
  nextStep: string;
  sessionClosing: string;
  continueWithSymbol?: string;
};
