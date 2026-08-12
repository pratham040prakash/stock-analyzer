import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";
import {
  computeTimeProgressPct,
  formatPatienceUntil,
  formatTimeRemaining,
  formatTimeTargetLabel,
  resolveJourneyTimeTarget,
} from "@/lib/journey/journeyTimeTarget";
import type {
  JourneyHorizon,
  JourneyMilestone,
  JourneyPathStep,
  JourneyProgressViewModel,
  StoredInvestmentJourney,
} from "@/types/investmentJourney";

export type BuildJourneyProgressInput = {
  journey: StoredInvestmentJourney;
  currentPriceInr?: number | null;
  quantity?: number;
  waitingForEntry?: boolean;
  entryConfirmed?: boolean;
  now?: Date;
};

function daysBetween(startIso: string, end: Date): number {
  const start = new Date(`${startIso}T00:00:00`);
  if (Number.isNaN(start.getTime())) {
    return 0;
  }

  return Math.max(
    0,
    Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)),
  );
}

function horizonLabel(horizon: JourneyHorizon): string {
  return horizon === "swing"
    ? JOURNEY_COPY.horizonSwing
    : JOURNEY_COPY.horizonLongTerm;
}

function computeProgressPct(
  entry: number | null,
  target: number,
  current: number | null,
): number {
  if (current === null || !Number.isFinite(current)) {
    return 0;
  }

  if (entry !== null && Number.isFinite(entry) && target !== entry) {
    const raw = ((current - entry) / (target - entry)) * 100;
    return Math.max(0, Math.min(100, Math.round(raw)));
  }

  if (target <= 0) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round((current / target) * 100)));
}

function resolveMilestone(input: {
  progressPct: number;
  waitingForEntry: boolean;
  inPosition: boolean;
  targetReached: boolean;
  thesisBroken: boolean;
}): JourneyMilestone {
  if (input.thesisBroken) {
    return "review";
  }

  if (input.targetReached) {
    return "target_reached";
  }

  if (input.waitingForEntry && !input.inPosition) {
    return "waiting_entry";
  }

  if (!input.inPosition) {
    return "planning";
  }

  if (input.progressPct >= 90) {
    return "near_target";
  }

  if (input.progressPct >= 20) {
    return "on_path";
  }

  return "in_position";
}

function milestoneLabel(milestone: JourneyMilestone): string {
  switch (milestone) {
    case "planning":
      return "Planning";
    case "waiting_entry":
      return "Waiting for entry";
    case "in_position":
      return "In position";
    case "on_path":
      return "On path";
    case "near_target":
      return "Near target";
    case "target_reached":
      return "Target reached";
    case "review":
      return "Review";
    default:
      return "On path";
  }
}

function buildPathSteps(input: {
  milestone: JourneyMilestone;
  waitingForEntry: boolean;
  inPosition: boolean;
  horizon: JourneyHorizon;
}): JourneyPathStep[] {
  const steps: Array<Omit<JourneyPathStep, "status">> = [
    {
      id: "plan",
      label: JOURNEY_COPY.path.plan,
      detail: "You chose a target and horizon.",
    },
    {
      id: "wait",
      label: JOURNEY_COPY.path.wait,
      detail: "Today confirms before you deploy capital.",
    },
    {
      id: "enter",
      label: JOURNEY_COPY.path.enter,
      detail: "Buy or add only inside your entry zone.",
    },
    {
      id: "hold",
      label: JOURNEY_COPY.path.hold,
      detail:
        input.horizon === "swing"
          ? "Hold through the swing window — no impulse trades."
          : "Hold core thesis; add only on plan.",
    },
    {
      id: "checkpoint",
      label: JOURNEY_COPY.path.checkpoint,
      detail: "Check progress vs target — adjust only with reason.",
    },
    {
      id: "target",
      label: JOURNEY_COPY.path.target,
      detail: "Near target: trim, hold, or set a new path.",
    },
  ];

  let currentIndex = 0;
  if (input.milestone === "target_reached") {
    currentIndex = steps.length;
  } else if (input.milestone === "near_target") {
    currentIndex = 5;
  } else if (input.milestone === "on_path") {
    currentIndex = 4;
  } else if (input.inPosition) {
    currentIndex = 3;
  } else if (input.waitingForEntry) {
    currentIndex = 1;
  }

  return steps.map((step, index) => ({
    ...step,
    status:
      index < currentIndex
        ? "done"
        : index === currentIndex
          ? "current"
          : "upcoming",
  }));
}

function buildGuidance(milestone: JourneyMilestone, progressPct: number): string {
  const base = JOURNEY_COPY.guidance[milestone] ?? JOURNEY_COPY.guidance.on_path;

  if (milestone === "on_path" || milestone === "in_position") {
    return `${base} (${progressPct}% toward target price.)`;
  }

  return base;
}

export function buildJourneyProgress(
  input: BuildJourneyProgressInput,
): JourneyProgressViewModel {
  const now = input.now ?? new Date();
  const entry = input.journey.entryPriceInr ?? null;
  const current = input.currentPriceInr ?? null;
  const target = input.journey.targetPriceInr;
  const supportLevel =
    input.journey.chartBasis?.supportLevelInr ?? entry ?? null;
  const thesisBroken =
    supportLevel !== null &&
    current !== null &&
    Number.isFinite(current) &&
    current < supportLevel * 0.98;
  const progressPct = computeProgressPct(entry, target, current);
  const inPosition = (input.quantity ?? 0) > 0 || input.entryConfirmed === true;
  const waitingForEntry = input.waitingForEntry ?? !inPosition;
  const targetReached =
    !thesisBroken &&
    current !== null &&
    Number.isFinite(current) &&
    current >= target &&
    target > 0;

  const milestone = resolveMilestone({
    progressPct,
    waitingForEntry,
    inPosition,
    targetReached,
    thesisBroken,
  });

  const daysElapsed = daysBetween(input.journey.startedAt, now);

  let daysRemaining: number | null = null;
  if (input.journey.targetBy) {
    const targetDate = new Date(`${input.journey.targetBy}T00:00:00`);
    if (!Number.isNaN(targetDate.getTime())) {
      daysRemaining = Math.max(
        0,
        Math.ceil((targetDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)),
      );
    }
  }

  const timeTarget = resolveJourneyTimeTarget(input.journey);
  const timeTargetLabel = timeTarget
    ? formatTimeTargetLabel(timeTarget.amount, timeTarget.unit)
    : null;
  const timeProgressPct =
    timeTarget !== null
      ? computeTimeProgressPct(daysElapsed, timeTarget.totalDays)
      : null;
  const timeRemainingLabel = formatTimeRemaining(daysRemaining);
  const timeOverdue =
    timeTarget !== null &&
    daysRemaining !== null &&
    daysRemaining <= 0 &&
    !targetReached;

  const invested = input.journey.investedAmountInr ?? null;
  let currentValue: number | null = null;
  let gainPct: number | null = null;

  if (
    invested !== null &&
    entry !== null &&
    current !== null &&
    entry > 0 &&
    Number.isFinite(invested)
  ) {
    currentValue = Math.round(invested * (current / entry));
    gainPct = Math.round(((currentValue - invested) / invested) * 1000) / 10;
  } else if (
    input.quantity &&
    input.quantity > 0 &&
    current !== null &&
    Number.isFinite(current)
  ) {
    currentValue = Math.round(input.quantity * current);
  }

  const priceRemaining =
    current !== null && target > current ? Math.round(target - current) : null;

  return {
    journey: input.journey,
    symbol: input.journey.symbol,
    horizon: input.journey.horizon,
    horizonLabel: horizonLabel(input.journey.horizon),
    targetPriceInr: target,
    entryPriceInr: entry,
    currentPriceInr: current,
    progressPct,
    priceRemainingInr: priceRemaining,
    investedAmountInr: invested,
    currentValueInr: currentValue,
    gainPct,
    daysElapsed,
    daysRemaining,
    timeTargetLabel,
    timeProgressPct,
    timeRemainingLabel,
    timeOverdue,
    milestone,
    milestoneLabel: milestoneLabel(milestone),
    guidance: buildGuidance(milestone, progressPct),
    pathSteps: buildPathSteps({
      milestone,
      waitingForEntry,
      inPosition,
      horizon: input.journey.horizon,
    }),
    disclaimer: JOURNEY_COPY.disclaimer,
    targetReached,
    thesisBroken,
    backtraceSummary: input.journey.chartBasis?.backtraceSummary,
    timeWaitLabel: input.journey.chartBasis?.timeWaitLabel ?? null,
    timeSuggestionRationale: input.journey.chartBasis?.timeSuggestionRationale ?? null,
    patienceUntilLabel:
      input.journey.targetBy !== undefined
        ? formatPatienceUntil(input.journey.targetBy, daysRemaining)
        : null,
  };
}

export function runBuildJourneyProgressSelfCheck(): void {
  const journey: StoredInvestmentJourney = {
    id: "test",
    symbol: "DIVISLAB",
    horizon: "swing",
    targetPriceInr: 8585,
    entryPriceInr: 8200,
    investedAmountInr: 100000,
    startedAt: "2026-08-01",
    targetBy: "2026-08-29",
    targetDurationAmount: 4,
    targetDurationUnit: "weeks",
    status: "active",
  };

  const mid = buildJourneyProgress({
    journey,
    currentPriceInr: 8400,
    quantity: 10,
    waitingForEntry: false,
    entryConfirmed: true,
    now: new Date("2026-08-12T10:00:00"),
  });

  if (mid.progressPct <= 0 || mid.progressPct >= 100) {
    throw new Error("Journey progress self-check failed: mid progress");
  }

  if (mid.pathSteps.filter((step) => step.status === "current").length !== 1) {
    throw new Error("Journey progress self-check failed: path current step");
  }

  if (mid.timeTargetLabel !== "4 weeks") {
    throw new Error("Journey progress self-check failed: time target label");
  }

  const reached = buildJourneyProgress({
    journey,
    currentPriceInr: 8600,
    quantity: 10,
    waitingForEntry: false,
    now: new Date("2026-08-12T10:00:00"),
  });

  if (!reached.targetReached || reached.milestone !== "target_reached") {
    throw new Error("Journey progress self-check failed: target reached");
  }
}
