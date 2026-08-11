export type PlannedVsActualStatus =
  | "aligned"
  | "deviated"
  | "planned_only"
  | "actual_only"
  | "wait_ok";

export type PlannedVsActualRow = {
  date: string;
  symbol: string | null;
  planned_action: string;
  actual_action: string | null;
  status: PlannedVsActualStatus;
  status_label: string;
  pnl: number | null;
};

export type PlannedVsActualSummary = {
  aligned: number;
  deviated: number;
  planned_only: number;
  actual_only: number;
};
