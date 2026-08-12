import type { JourneyHorizon, JourneyTimeUnit } from "@/types/investmentJourney";

export type JourneyTimePreset = {
  id: string;
  label: string;
  amount: number;
  unit: JourneyTimeUnit;
};

export type JourneyTimeSuggestion = {
  amount: number;
  unit: JourneyTimeUnit;
  totalDays: number;
  waitLabel: string;
  rationale: string;
  medianHistoricalDays: number | null;
  movePctNeeded: number;
};

export const JOURNEY_TIME_PRESETS: JourneyTimePreset[] = [
  { id: "2w", label: "2 weeks", amount: 2, unit: "weeks" },
  { id: "4w", label: "4 weeks", amount: 4, unit: "weeks" },
  { id: "8w", label: "8 weeks", amount: 8, unit: "weeks" },
  { id: "3m", label: "3 months", amount: 90, unit: "days" },
  { id: "6m", label: "6 months", amount: 26, unit: "weeks" },
  { id: "1y", label: "1 year", amount: 1, unit: "years" },
];

export function durationToDays(amount: number, unit: JourneyTimeUnit): number {
  const value = Math.max(1, Math.round(amount));
  if (unit === "days") {
    return value;
  }
  if (unit === "weeks") {
    return value * 7;
  }
  return value * 365;
}

export function computeTargetByDate(
  startedAt: string,
  amount: number,
  unit: JourneyTimeUnit,
): string {
  const start = new Date(`${startedAt}T00:00:00`);
  if (Number.isNaN(start.getTime())) {
    return new Date().toISOString().slice(0, 10);
  }

  const days = durationToDays(amount, unit);
  const end = new Date(start);
  end.setDate(end.getDate() + days);
  return end.toISOString().slice(0, 10);
}

export function formatTimeTargetLabel(amount: number, unit: JourneyTimeUnit): string {
  const value = Math.max(1, Math.round(amount));
  if (unit === "days") {
    return value === 1 ? "1 day" : `${value} days`;
  }
  if (unit === "weeks") {
    return value === 1 ? "1 week" : `${value} weeks`;
  }
  return value === 1 ? "1 year" : `${value} years`;
}

export function formatTimeRemaining(daysRemaining: number | null): string | null {
  if (daysRemaining === null) {
    return null;
  }

  if (daysRemaining <= 0) {
    return "Time target due";
  }

  if (daysRemaining === 1) {
    return "1 day left";
  }

  if (daysRemaining < 14) {
    return `${daysRemaining} days left`;
  }

  const weeks = Math.round(daysRemaining / 7);
  if (weeks < 8) {
    return `${weeks} wk left`;
  }

  const months = Math.round(daysRemaining / 30);
  return months <= 1 ? "1 mo left" : `${months} mo left`;
}

export function computeTimeProgressPct(
  daysElapsed: number,
  totalDays: number,
): number {
  if (totalDays <= 0) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round((daysElapsed / totalDays) * 100)));
}

export function suggestTimeTarget(horizon: JourneyHorizon): {
  amount: number;
  unit: JourneyTimeUnit;
} {
  if (horizon === "swing") {
    return { amount: 4, unit: "weeks" };
  }

  return { amount: 1, unit: "years" };
}

function median(values: number[]): number | null {
  if (values.length === 0) {
    return null;
  }

  const sorted = [...values].sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)];
}

function normalizeDaysToUnit(
  days: number,
  horizon: JourneyHorizon,
): { amount: number; unit: JourneyTimeUnit; totalDays: number } {
  const clamped =
    horizon === "swing"
      ? Math.max(10, Math.min(60, Math.round(days)))
      : Math.max(60, Math.min(730, Math.round(days)));

  if (horizon === "long_term" && clamped >= 300) {
    const years = Math.max(1, Math.round(clamped / 365));
    return { amount: years, unit: "years", totalDays: durationToDays(years, "years") };
  }

  if (clamped >= 14) {
    const weeks = Math.max(1, Math.round(clamped / 7));
    return { amount: weeks, unit: "weeks", totalDays: durationToDays(weeks, "weeks") };
  }

  return {
    amount: Math.max(7, clamped),
    unit: "days",
    totalDays: Math.max(7, clamped),
  };
}

function findHistoricalClimbDays(
  prices: number[],
  gainPctNeeded: number,
): number[] {
  if (gainPctNeeded <= 0) {
    return [];
  }

  const threshold = gainPctNeeded * 0.85;
  const durations: number[] = [];

  for (let start = 0; start < prices.length - 5; start += 1) {
    const base = prices[start];
    if (base <= 0) {
      continue;
    }

    for (let end = start + 1; end < prices.length; end += 1) {
      const gainPct = ((prices[end] - base) / base) * 100;
      if (gainPct >= threshold) {
        durations.push(end - start);
        break;
      }
    }
  }

  return durations;
}

function averageDailyAbsMovePct(prices: number[]): number {
  const moves: number[] = [];

  for (let index = 1; index < prices.length; index += 1) {
    const previous = prices[index - 1];
    const current = prices[index];
    if (previous <= 0) {
      continue;
    }

    moves.push(Math.abs(((current - previous) / previous) * 100));
  }

  if (moves.length === 0) {
    return 0;
  }

  return moves.reduce((sum, value) => sum + value, 0) / moves.length;
}

/** Estimate wait window from candle backtrace — structure-based, not a forecast. */
export function suggestTimeTargetFromCandles(input: {
  prices: number[];
  entryPriceInr: number;
  targetPriceInr: number;
  currentPriceInr?: number | null;
  horizon: JourneyHorizon;
  lookbackDays?: number;
}): JourneyTimeSuggestion {
  const anchor =
    input.currentPriceInr && input.currentPriceInr > 0
      ? input.currentPriceInr
      : input.entryPriceInr;
  const movePctNeeded = Math.max(
    1,
    Math.round(((input.targetPriceInr - anchor) / anchor) * 100),
  );

  const climbDays = findHistoricalClimbDays(input.prices, movePctNeeded);
  const historicalMedian = median(climbDays);
  const avgDailyMove = averageDailyAbsMovePct(input.prices);
  const lookback = input.lookbackDays ?? input.prices.length;

  let rawDays: number;
  let rationale: string;

  if (historicalMedian !== null && climbDays.length >= 2) {
    rawDays = historicalMedian;
    rationale = `FACT · Climbs of ~${movePctNeeded}% in this stock took about ${historicalMedian} sessions in the last ${lookback} days.`;
  } else if (avgDailyMove > 0.05) {
    rawDays = Math.ceil(movePctNeeded / avgDailyMove);
    rationale = `ESTIMATE · Recent daily moves (~${avgDailyMove.toFixed(1)}%/session) imply ~${rawDays} sessions for +${movePctNeeded}% — not guaranteed.`;
  } else {
    const fallback = suggestTimeTarget(input.horizon);
    const totalDays = durationToDays(fallback.amount, fallback.unit);
    return {
      amount: fallback.amount,
      unit: fallback.unit,
      totalDays,
      waitLabel: `Wait ~${formatTimeTargetLabel(fallback.amount, fallback.unit)}`,
      rationale:
        input.horizon === "swing"
          ? "ESTIMATE · Swing path default — limited climb history in the backtrace."
          : "ESTIMATE · Long-term path default — allow structure to develop.",
      medianHistoricalDays: null,
      movePctNeeded,
    };
  }

  const normalized = normalizeDaysToUnit(rawDays, input.horizon);
  const waitLabel = `Wait ~${formatTimeTargetLabel(normalized.amount, normalized.unit)}`;

  return {
    amount: normalized.amount,
    unit: normalized.unit,
    totalDays: normalized.totalDays,
    waitLabel,
    rationale,
    medianHistoricalDays: historicalMedian,
    movePctNeeded,
  };
}

export function resolveJourneyTimeTarget(journey: {
  targetDurationAmount?: number;
  targetDurationUnit?: JourneyTimeUnit;
  targetBy?: string;
  startedAt: string;
}): { amount: number; unit: JourneyTimeUnit; totalDays: number } | null {
  if (journey.targetDurationAmount && journey.targetDurationUnit) {
    return {
      amount: journey.targetDurationAmount,
      unit: journey.targetDurationUnit,
      totalDays: durationToDays(
        journey.targetDurationAmount,
        journey.targetDurationUnit,
      ),
    };
  }

  if (!journey.targetBy) {
    return null;
  }

  const start = new Date(`${journey.startedAt}T00:00:00`);
  const end = new Date(`${journey.targetBy}T00:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return null;
  }

  const totalDays = Math.max(
    1,
    Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)),
  );

  if (totalDays % 365 === 0 && totalDays >= 365) {
    return { amount: Math.round(totalDays / 365), unit: "years", totalDays };
  }

  if (totalDays % 7 === 0) {
    return { amount: Math.round(totalDays / 7), unit: "weeks", totalDays };
  }

  return { amount: totalDays, unit: "days", totalDays };
}

export function runJourneyTimeTargetSelfCheck(): void {
  const targetBy = computeTargetByDate("2026-08-01", 4, "weeks");
  const expected = computeTargetByDate("2026-08-01", 4, "weeks");
  if (targetBy !== expected || !targetBy.startsWith("2026-08-")) {
    throw new Error("Journey time target self-check failed: targetBy");
  }

  const prices = [
    100, 101, 100, 102, 103, 102, 104, 105, 106, 107, 108, 109, 110, 111, 112,
    113, 114, 115, 116, 118,
  ];

  const suggestion = suggestTimeTargetFromCandles({
    prices,
    entryPriceInr: 100,
    targetPriceInr: 118,
    currentPriceInr: 110,
    horizon: "swing",
  });

  if (!suggestion.waitLabel.includes("Wait ~") || suggestion.totalDays < 7) {
    throw new Error("Journey time target self-check failed: candle suggestion");
  }

  if (!suggestion.rationale.startsWith("FACT") && !suggestion.rationale.startsWith("ESTIMATE")) {
    throw new Error("Journey time target self-check failed: rationale prefix");
  }

  const pct = computeTimeProgressPct(14, 28);
  if (pct !== 50) {
    throw new Error("Journey time target self-check failed: progress");
  }
}
