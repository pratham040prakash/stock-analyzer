export type DailyDecisionType = "BUY_MORE" | "HOLD" | "REDUCE" | "WAIT";

export type DailyDecisionOutput = {
  decision: DailyDecisionType;
  confidence: number;
  reason: string;
  actions: string[];
};

export type PortfolioSnapshotInput = {
  holdings: import("@/types/portfolio").Portfolio["holdings"];
  total_value: number;
  pnl?: number;
};

export type DecisionEngineInput = {
  portfolioSnapshot: PortfolioSnapshotInput;
  financialProfile: import("@/lib/financialProfile").FinancialProfile | null;
  lastMentorOutput?: import("@/types/mentorDecision").MentorDecision | null;
};
