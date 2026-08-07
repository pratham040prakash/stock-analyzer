export type DecisionHistoryEntry = {
  date: string;
  action: import("@/types/decision").DecisionActionType;
  stock?: string;
  confidence: number;
};

export type DecisionHistoryResponse = {
  history: DecisionHistoryEntry[];
};
