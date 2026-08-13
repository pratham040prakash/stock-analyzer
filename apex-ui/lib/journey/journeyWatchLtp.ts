import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import {
  buildJourneyPriceMap,
  lookupJourneyLiveQuote,
  mergeWatchPathQuotes,
  type JourneyLiveQuote,
} from "@/lib/journey/journeyPriceMap";
import type { StoredInvestmentJourney } from "@/types/investmentJourney";
import type { StockPick } from "@/types/decision";
import type { PortfolioHoldingRow } from "@/types/portfolioApi";
import type { ExploreLiveTrigger } from "@/services/explore/liveTriggers";

type TriggersResponse = {
  status?: string;
  triggers?: ExploreLiveTrigger[];
};

const MAX_WATCH_QUOTES = 5;

function buildWatchPicks(journeys: StoredInvestmentJourney[]): StockPick[] {
  return journeys.slice(0, MAX_WATCH_QUOTES).map((journey) => ({
    stock: journey.symbol,
    score: 70,
    signals: { trend: 0, momentum: 0, volume: 0 },
    price: journey.entryPriceInr,
    activationLevel: journey.entryPriceInr,
  }));
}

export async function hydrateJourneyPriceMap(
  journeys: StoredInvestmentJourney[],
  holdings: PortfolioHoldingRow[],
): Promise<Map<string, JourneyLiveQuote>> {
  const priceMap = buildJourneyPriceMap(holdings);

  const watchJourneys = journeys.filter(
    (journey) => !lookupJourneyLiveQuote(priceMap, journey.symbol),
  );

  if (watchJourneys.length === 0) {
    return priceMap;
  }

  try {
    const response = await apiFetch("/api/explore/triggers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ picks: buildWatchPicks(watchJourneys) }),
    });
    const data = await parseApiJson<TriggersResponse>(response, "Journey watch LTP");

    if (!response.ok || !data?.triggers?.length) {
      return priceMap;
    }

    return mergeWatchPathQuotes(
      priceMap,
      data.triggers.map((trigger) => ({
        symbol: trigger.symbol,
        livePrice: trigger.livePrice,
      })),
    );
  } catch {
    return priceMap;
  }
}

export async function fetchJourneySymbolLivePrice(
  symbol: string,
  entryPriceInr?: number,
): Promise<number | null> {
  const normalized = symbol.trim().toUpperCase();
  if (!normalized) {
    return null;
  }

  const entry =
    entryPriceInr !== undefined && entryPriceInr > 0
      ? Math.round(entryPriceInr)
      : undefined;
  const target = entry ? Math.round(entry * 1.04) : 1000;

  const map = await hydrateJourneyPriceMap(
    [
      {
        id: `probe_${normalized}`,
        symbol: normalized,
        horizon: "swing",
        targetPriceInr: target,
        entryPriceInr: entry,
        startedAt: new Date().toISOString().slice(0, 10),
        status: "active",
      },
    ],
    [],
  );

  return lookupJourneyLiveQuote(map, normalized)?.currentPriceInr ?? null;
}

export function runJourneyWatchLtpSelfCheck(): void {
  if (MAX_WATCH_QUOTES !== 5) {
    throw new Error("Journey watch LTP self-check failed: cap");
  }

  const picks = buildWatchPicks([
    {
      id: "j1",
      symbol: "TCS",
      horizon: "swing",
      targetPriceInr: 4200,
      entryPriceInr: 4000,
      startedAt: "2026-08-01",
      status: "active",
    },
  ]);

  if (picks.length !== 1 || picks[0]?.stock !== "TCS") {
    throw new Error("Journey watch LTP self-check failed: picks");
  }
}
