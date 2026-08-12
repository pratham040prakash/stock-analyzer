import type {
  JourneyChartBasis,
  StoredInvestmentJourney,
} from "@/types/investmentJourney";

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
    return Array.isArray(parsed) ? parsed : [];
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
  },
): StoredInvestmentJourney {
  const startedAt = input.startedAt ?? new Date().toISOString().slice(0, 10);
  const journey: StoredInvestmentJourney = {
    id: input.id ?? `journey_${Date.now()}`,
    symbol: input.symbol.trim().toUpperCase(),
    horizon: input.horizon,
    targetPriceInr: input.targetPriceInr,
    entryPriceInr: input.entryPriceInr,
    investedAmountInr: input.investedAmountInr,
    startedAt,
    targetBy: input.targetBy,
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
