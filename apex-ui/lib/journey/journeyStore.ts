import type {
  JourneyChartBasis,
  JourneyTimeUnit,
  StoredInvestmentJourney,
} from "@/types/investmentJourney";
import { computeTargetByDate } from "@/lib/journey/journeyTimeTarget";
import { normalizeJourneyPrices, repairStoredJourney } from "@/lib/journey/journeyPlanSanitize";

const STORAGE_KEY = "apex_investment_journeys_v1";

function readAll(): StoredInvestmentJourney[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw) as StoredInvestmentJourney[];
    if (!Array.isArray(parsed)) {
      return [];
    }

    const repaired = parsed.map((journey) => repairStoredJourney(journey));
    const changed = repaired.some(
      (journey, index) => JSON.stringify(journey) !== JSON.stringify(parsed[index]),
    );
    if (changed) {
      writeAll(repaired);
    }

    return repaired;
  } catch {
    return [];
  }
}

function writeAll(journeys: StoredInvestmentJourney[]): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(journeys));
}

export function listActiveJourneys(): StoredInvestmentJourney[] {
  return readAll().filter((journey) => journey.status === "active");
}

export function getActiveJourneyForSymbol(
  symbol: string,
): StoredInvestmentJourney | null {
  const normalized = symbol.trim().toUpperCase();
  return (
    readAll().find(
      (journey) =>
        journey.status === "active" &&
        journey.symbol.trim().toUpperCase() === normalized,
    ) ?? null
  );
}

export function saveJourney(journey: StoredInvestmentJourney): void {
  const journeys = readAll().filter((row) => row.id !== journey.id);
  journeys.unshift(journey);
  writeAll(journeys.slice(0, 12));
}

export function createJourney(
  input: Omit<StoredInvestmentJourney, "id" | "status" | "startedAt"> & {
    id?: string;
    startedAt?: string;
    suggestedByApex?: boolean;
    chartBasis?: JourneyChartBasis;
    targetDurationAmount?: number;
    targetDurationUnit?: JourneyTimeUnit;
  },
): StoredInvestmentJourney {
  const startedAt = input.startedAt ?? new Date().toISOString().slice(0, 10);
  const normalized = normalizeJourneyPrices({
    entryPriceInr: input.entryPriceInr ?? input.targetPriceInr * 0.94,
    targetPriceInr: input.targetPriceInr,
  });
  const targetBy =
    input.targetDurationAmount && input.targetDurationUnit
      ? computeTargetByDate(
          startedAt,
          input.targetDurationAmount,
          input.targetDurationUnit,
        )
      : input.targetBy;

  const journey: StoredInvestmentJourney = {
    id: input.id ?? `journey_${Date.now()}`,
    symbol: input.symbol.trim().toUpperCase(),
    horizon: input.horizon,
    targetPriceInr: normalized.targetPriceInr,
    entryPriceInr: normalized.entryPriceInr,
    investedAmountInr: input.investedAmountInr,
    startedAt,
    targetBy,
    targetDurationAmount: input.targetDurationAmount,
    targetDurationUnit: input.targetDurationUnit,
    status: "active",
    notes: input.notes,
    suggestedByApex: input.suggestedByApex,
    chartBasis: input.chartBasis,
  };

  saveJourney(journey);
  return journey;
}

export function completeJourney(id: string): void {
  const journeys = readAll();
  const index = journeys.findIndex((row) => row.id === id);
  if (index === -1) {
    return;
  }

  journeys[index] = { ...journeys[index], status: "completed" };
  writeAll(journeys);
}

export function pauseJourney(id: string): void {
  const journeys = readAll();
  const index = journeys.findIndex((row) => row.id === id);
  if (index === -1) {
    return;
  }

  journeys[index] = { ...journeys[index], status: "paused" };
  writeAll(journeys);
}

export function runJourneyStoreSelfCheck(): void {
  const sample: StoredInvestmentJourney = {
    id: "journey_test",
    symbol: "DIVISLAB",
    horizon: "swing",
    targetPriceInr: 8585,
    entryPriceInr: 8200,
    startedAt: "2026-08-01",
    targetBy: "2026-08-22",
    status: "active",
  };

  if (sample.symbol !== "DIVISLAB" || sample.status !== "active") {
    throw new Error("Journey store self-check failed");
  }
}
