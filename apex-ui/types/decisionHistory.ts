import type { DecisionActionType } from "@/types/decision";

export type DisciplineOutcome =
  | "win"
  | "loss"
  | "open"
  | "followed"
  | "wait"
  | "hold"
  | "none";

export type DisciplineHistorySource = "executed" | "guidance" | "commit";

/** @deprecated Use DisciplineHistoryEntry — kept for backward-compatible imports. */
export type DecisionHistoryEntry = DisciplineHistoryEntry;

export type DisciplineHistoryEntry = {
  date: string;
  action: DecisionActionType;
  stock?: string;
  outcome: DisciplineOutcome;
  outcomeLabel: string;
  pnl?: number | null;
  source: DisciplineHistorySource;
};

export type DisciplineHistorySummary = {
  wins: number;
  losses: number;
  open: number;
  waitDays: number;
  executedDays: number;
  followedDays: number;
};

export type DecisionHistoryResponse = {
  history: DisciplineHistoryEntry[];
  summary: DisciplineHistorySummary;
  days: string[];
};
