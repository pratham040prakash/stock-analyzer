import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";

export type JourneyWaitPathInsight = {
  tone: "amber";
  message: string;
};

function resolveWaitPathEnd(input: {
  entryPriceInr: number;
  targetPriceInr: number;
  buyAboveInr?: number | null;
}): number | null {
  const entry = input.entryPriceInr;
  const buyAbove = input.buyAboveInr;
  if (
    buyAbove !== null &&
    buyAbove !== undefined &&
    Number.isFinite(buyAbove) &&
    buyAbove > entry
  ) {
    return buyAbove;
  }

  const target = input.targetPriceInr;
  if (!Number.isFinite(target) || target <= entry) {
    return null;
  }

  return target;
}

export function resolveJourneyWaitPathInsight(input: {
  waitingForEntry: boolean;
  entryPriceInr: number;
  targetPriceInr: number;
  buyAboveInr?: number | null;
  currentPriceInr?: number | null;
}): JourneyWaitPathInsight | null {
  if (!input.waitingForEntry) {
    return null;
  }

  const current = input.currentPriceInr;
  if (current === null || current === undefined || !Number.isFinite(current)) {
    return null;
  }

  const entry = input.entryPriceInr;
  const pathEnd = resolveWaitPathEnd(input);
  if (pathEnd === null) {
    return null;
  }

  const usesBuyTrigger =
    input.buyAboveInr !== null &&
    input.buyAboveInr !== undefined &&
    Number.isFinite(input.buyAboveInr) &&
    input.buyAboveInr > entry;

  if (current >= pathEnd) {
    return {
      tone: "amber",
      message: usesBuyTrigger
        ? JOURNEY_COPY.waitAtBuyCallout
        : JOURNEY_COPY.waitAtTargetCallout,
    };
  }

  const pathPct = ((current - entry) / (pathEnd - entry)) * 100;
  if (pathPct >= 90) {
    return {
      tone: "amber",
      message: usesBuyTrigger
        ? JOURNEY_COPY.waitNearBuyCallout
        : JOURNEY_COPY.waitNearTargetCallout,
    };
  }

  return null;
}

export function runJourneyWaitPathInsightSelfCheck(): void {
  const atBuy = resolveJourneyWaitPathInsight({
    waitingForEntry: true,
    entryPriceInr: 1902,
    targetPriceInr: 1966,
    buyAboveInr: 1978,
    currentPriceInr: 1978,
  });

  if (!atBuy?.message.includes("buy trigger")) {
    throw new Error("Journey wait path insight self-check failed: at buy");
  }

  const inTrade = resolveJourneyWaitPathInsight({
    waitingForEntry: false,
    entryPriceInr: 1902,
    targetPriceInr: 1966,
    buyAboveInr: 1978,
    currentPriceInr: 1978,
  });

  if (inTrade !== null) {
    throw new Error("Journey wait path insight self-check failed: in trade");
  }

  const nearBuy = resolveJourneyWaitPathInsight({
    waitingForEntry: true,
    entryPriceInr: 1902,
    targetPriceInr: 1966,
    buyAboveInr: 1978,
    currentPriceInr: 1971,
  });

  if (!nearBuy?.message.includes("buy trigger")) {
    throw new Error("Journey wait path insight self-check failed: near buy");
  }
}
