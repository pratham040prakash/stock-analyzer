import type { JourneyHorizon, JourneyTimeUnit } from "@/types/investmentJourney";

export type JourneyTimePreset = {
  id: string;
  label: string;
  amount: number;
  unit: JourneyTimeUnit;
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

  const label = formatTimeTargetLabel(4, "weeks");
  if (label !== "4 weeks") {
    throw new Error("Journey time target self-check failed: label");
  }

  const pct = computeTimeProgressPct(14, 28);
  if (pct !== 50) {
    throw new Error("Journey time target self-check failed: progress");
  }
}
