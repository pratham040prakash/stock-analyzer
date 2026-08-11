export type InvestorBehaviorTag =
  | "Disciplined waiter"
  | "Active executor"
  | "Mixed rhythm"
  | "Building habit";

export type InvestorDnaViewModel = {
  behavior_tag: InvestorBehaviorTag;
  summary: string;
  wait_receipts: number;
  act_receipts: number;
  discipline_streak: number;
  insight: string;
  window_days: number;
  trend_30d: {
    wait_receipts: number;
    act_receipts: number;
    dominant_pattern: InvestorBehaviorTag;
  };
};
