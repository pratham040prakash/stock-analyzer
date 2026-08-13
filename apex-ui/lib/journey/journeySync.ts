import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import {
  completeJourney as completeLocalJourney,
  getActiveJourneyForSymbol,
  listActiveJourneys,
  pauseJourney as pauseLocalJourney,
  saveJourney,
} from "@/lib/journey/journeyStore";
import type {
  JourneyStatus,
  StoredInvestmentJourney,
} from "@/types/investmentJourney";

type ActiveJourneyResponse = {
  journey: StoredInvestmentJourney | null;
};

type ActiveJourneysListResponse = {
  journeys: StoredInvestmentJourney[];
};

type JourneyMutationResponse = {
  journey: StoredInvestmentJourney;
};

export async function syncJourneyForSymbol(
  symbol: string,
): Promise<StoredInvestmentJourney | null> {
  const normalized = symbol.trim().toUpperCase();
  if (!normalized) {
    return null;
  }

  const local = getActiveJourneyForSymbol(normalized);

  try {
    const response = await apiFetch(
      `/api/journey/active?symbol=${encodeURIComponent(normalized)}`,
      { cache: "no-store" },
    );
    const data = await parseApiJson<ActiveJourneyResponse>(
      response,
      "Journey sync",
    );

    if (response.ok && data?.journey) {
      saveJourney(data.journey);
      return data.journey;
    }

    if (local) {
      return persistJourneyToServer(local);
    }

    return null;
  } catch {
    return local;
  }
}

export async function syncAllActiveJourneys(): Promise<StoredInvestmentJourney[]> {
  const localBefore = listActiveJourneys();

  try {
    const response = await apiFetch("/api/journey/active", { cache: "no-store" });
    const data = await parseApiJson<ActiveJourneysListResponse>(
      response,
      "Journey list sync",
    );

    if (response.ok && Array.isArray(data?.journeys)) {
      for (const journey of data.journeys) {
        saveJourney(journey);
      }

      const serverSymbols = new Set(
        data.journeys.map((journey) => journey.symbol.trim().toUpperCase()),
      );

      for (const local of localBefore) {
        if (!serverSymbols.has(local.symbol.trim().toUpperCase())) {
          await persistJourneyToServer(local);
        }
      }

      return listActiveJourneys();
    }
  } catch {
    // Fall through to local-only paths.
  }

  for (const local of localBefore) {
    await persistJourneyToServer(local);
  }

  return listActiveJourneys();
}

export async function persistJourneyToServer(
  journey: StoredInvestmentJourney,
): Promise<StoredInvestmentJourney | null> {
  try {
    const response = await apiFetch("/api/journey", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(journey),
    });
    const data = await parseApiJson<JourneyMutationResponse>(
      response,
      "Journey save",
    );

    if (!response.ok || !data?.journey) {
      return journey;
    }

    saveJourney(data.journey);
    return data.journey;
  } catch {
    return journey;
  }
}

export async function updateJourneyStatusOnServer(
  journeyId: string,
  status: Exclude<JourneyStatus, "active">,
): Promise<StoredInvestmentJourney | null> {
  if (status === "completed") {
    completeLocalJourney(journeyId);
  } else {
    pauseLocalJourney(journeyId);
  }

  try {
    const response = await apiFetch("/api/journey", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: journeyId, status }),
    });
    const data = await parseApiJson<JourneyMutationResponse>(
      response,
      "Journey status",
    );

    if (response.ok && data?.journey) {
      saveJourney(data.journey);
      return data.journey;
    }
  } catch {
    // Local store already updated — offline-safe.
  }

  return null;
}

export function runJourneySyncSelfCheck(): void {
  if (typeof syncJourneyForSymbol !== "function") {
    throw new Error("Journey sync self-check failed: symbol sync");
  }

  if (typeof syncAllActiveJourneys !== "function") {
    throw new Error("Journey sync self-check failed: list sync");
  }
}
