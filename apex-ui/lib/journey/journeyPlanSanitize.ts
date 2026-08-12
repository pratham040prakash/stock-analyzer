import type { ChartBackedJourneyPlan } from "@/lib/journey/buildChartBackedJourneyPlan";
import type { StoredInvestmentJourney } from "@/types/investmentJourney";
import { computeTargetByDate } from "@/lib/journey/journeyTimeTarget";

export function normalizeJourneyPrices(input: {
  entryPriceInr: number;
  targetPriceInr: number;
  currentPriceInr?: number | null;
}): { entryPriceInr: number; targetPriceInr: number } {
  let entry = Math.round(input.entryPriceInr);
  let target = Math.round(input.targetPriceInr);

  if (!Number.isFinite(entry) || entry <= 0) {
    entry = Math.max(1, Math.round(input.currentPriceInr ?? target));
  }

  if (!Number.isFinite(target) || target <= entry) {
    target = Math.round(entry * 1.06);
  }

  const current = input.currentPriceInr;
  if (current !== null && current !== undefined && Number.isFinite(current) && target <= current) {
    target = Math.round(Math.max(entry * 1.06, current * 1.08));
  }

  return { entryPriceInr: entry, targetPriceInr: target };
}

export function isValidJourneyPlan(plan: {
  entryPriceInr: number;
  targetPriceInr: number;
}): boolean {
  return (
    Number.isFinite(plan.entryPriceInr) &&
    Number.isFinite(plan.targetPriceInr) &&
    plan.entryPriceInr > 0 &&
    plan.targetPriceInr > plan.entryPriceInr
  );
}

export function sanitizeChartBackedJourneyPlan(
  plan: ChartBackedJourneyPlan,
  currentPriceInr?: number | null,
): ChartBackedJourneyPlan {
  const normalized = normalizeJourneyPrices({
    entryPriceInr: plan.entryPriceInr,
    targetPriceInr: plan.targetPriceInr,
    currentPriceInr,
  });

  return {
    ...plan,
    entryPriceInr: normalized.entryPriceInr,
    targetPriceInr: normalized.targetPriceInr,
  };
}

export function repairStoredJourney(journey: StoredInvestmentJourney): StoredInvestmentJourney {
  const today = new Date().toISOString().slice(0, 10);
  const normalized = normalizeJourneyPrices({
    entryPriceInr: journey.entryPriceInr ?? journey.targetPriceInr * 0.94,
    targetPriceInr: journey.targetPriceInr,
  });

  let startedAt = journey.startedAt;
  let targetBy = journey.targetBy;

  const durationAmount = journey.targetDurationAmount;
  const durationUnit = journey.targetDurationUnit;

  if (durationAmount && durationUnit) {
    if (!startedAt || startedAt < "2020-01-01" || (targetBy && targetBy < today)) {
      startedAt = today;
    }

    targetBy = computeTargetByDate(startedAt, durationAmount, durationUnit);
  }

  return {
    ...journey,
    entryPriceInr: normalized.entryPriceInr,
    targetPriceInr: normalized.targetPriceInr,
    startedAt,
    targetBy,
  };
}

export function runJourneyPlanSanitizeSelfCheck(): void {
  const fixed = normalizeJourneyPrices({
    entryPriceInr: 3275,
    targetPriceInr: 3268,
    currentPriceInr: 3200,
  });

  if (fixed.targetPriceInr <= fixed.entryPriceInr) {
    throw new Error("Journey plan sanitize self-check failed: target/entry");
  }

  const repaired = repairStoredJourney({
    id: "test",
    symbol: "TEST",
    horizon: "swing",
    targetPriceInr: 3268,
    entryPriceInr: 3275,
    startedAt: "2023-08-11",
    targetBy: "2023-10-13",
    targetDurationAmount: 9,
    targetDurationUnit: "weeks",
    status: "active",
  });

  if (repaired.startedAt < "2026-01-01" || !repaired.targetBy || repaired.targetBy < repaired.startedAt) {
    throw new Error("Journey plan sanitize self-check failed: repair dates");
  }
}
