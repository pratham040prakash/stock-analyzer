export type JourneyHorizon = "long_term" | "swing";

export type JourneyStatus = "active" | "completed" | "paused";

export type StoredInvestmentJourney = {
  id: string;
  symbol: string;
  horizon: JourneyHorizon;
  targetPriceInr: number;
  entryPriceInr?: number;
  investedAmountInr?: number;
  startedAt: string;
  targetBy?: string;
  status: JourneyStatus;
  notes?: string;
};

export type JourneyPathStepStatus = "done" | "current" | "upcoming";

export type JourneyPathStep = {
  id: string;
  label: string;
  detail: string;
  status: JourneyPathStepStatus;
};

export type JourneyMilestone =
  | "planning"
  | "waiting_entry"
  | "in_position"
  | "on_path"
  | "near_target"
  | "target_reached"
  | "review";

export type JourneyProgressViewModel = {
  journey: StoredInvestmentJourney;
  symbol: string;
  horizon: JourneyHorizon;
  horizonLabel: string;
  targetPriceInr: number;
  entryPriceInr: number | null;
  currentPriceInr: number | null;
  progressPct: number;
  priceRemainingInr: number | null;
  investedAmountInr: number | null;
  currentValueInr: number | null;
  gainPct: number | null;
  daysElapsed: number;
  daysRemaining: number | null;
  milestone: JourneyMilestone;
  milestoneLabel: string;
  guidance: string;
  pathSteps: JourneyPathStep[];
  disclaimer: string;
  targetReached: boolean;
};

export type StartJourneyInput = {
  symbol: string;
  horizon: JourneyHorizon;
  targetPriceInr: number;
  entryPriceInr?: number;
  investedAmountInr?: number;
  swingWeeks?: number;
  notes?: string;
};
