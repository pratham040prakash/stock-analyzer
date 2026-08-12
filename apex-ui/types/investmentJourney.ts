export type JourneyHorizon = "long_term" | "swing";

export type JourneyTimeUnit = "days" | "weeks" | "years";

export type JourneyStatus = "active" | "completed" | "paused";

export type JourneyChartBasis = {
  lookbackDays: number;
  supportLevelInr?: number;
  resistanceLevelInr?: number;
  backtraceSummary: string;
  structureScore?: number;
  suggestedAt: string;
  suggestedWaitDays?: number;
  timeSuggestionRationale?: string;
  timeWaitLabel?: string;
};

export type StoredInvestmentJourney = {
  id: string;
  symbol: string;
  horizon: JourneyHorizon;
  targetPriceInr: number;
  entryPriceInr?: number;
  investedAmountInr?: number;
  startedAt: string;
  targetBy?: string;
  targetDurationAmount?: number;
  targetDurationUnit?: JourneyTimeUnit;
  status: JourneyStatus;
  notes?: string;
  /** Set when path came from APEX chart backtrace, not manual entry. */
  suggestedByApex?: boolean;
  chartBasis?: JourneyChartBasis;
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
  timeTargetLabel: string | null;
  timeProgressPct: number | null;
  timeRemainingLabel: string | null;
  timeOverdue: boolean;
  milestone: JourneyMilestone;
  milestoneLabel: string;
  guidance: string;
  pathSteps: JourneyPathStep[];
  disclaimer: string;
  targetReached: boolean;
  thesisBroken: boolean;
  backtraceSummary?: string;
  timeWaitLabel?: string | null;
  timeSuggestionRationale?: string | null;
};

export type StartJourneyInput = {
  symbol: string;
  horizon: JourneyHorizon;
  targetPriceInr: number;
  entryPriceInr?: number;
  investedAmountInr?: number;
  swingWeeks?: number;
  targetDurationAmount?: number;
  targetDurationUnit?: JourneyTimeUnit;
  notes?: string;
  suggestedByApex?: boolean;
  chartBasis?: JourneyChartBasis;
};
