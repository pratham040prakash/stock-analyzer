import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";

export type JourneyWaitPathInsight = {
  tone: "amber";
  message: string;
};

export function resolveJourneyWaitPathInsight(input: {
  waitingForEntry: boolean;
  entryPriceInr: number;
  targetPriceInr: number;
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
  const target = input.targetPriceInr;
  if (!Number.isFinite(entry) || !Number.isFinite(target) || target <= entry) {
    return null;
  }

  if (current >= target) {
    return {
      tone: "amber",
      message: JOURNEY_COPY.waitAtTargetCallout,
    };
  }

  const pathPct = ((current - entry) / (target - entry)) * 100;
  if (pathPct >= 90) {
    return {
      tone: "amber",
      message: JOURNEY_COPY.waitNearTargetCallout,
    };
  }

  return null;
}

export function runJourneyWaitPathInsightSelfCheck(): void {
  const atTarget = resolveJourneyWaitPathInsight({
    waitingForEntry: true,
    entryPriceInr: 1902,
    targetPriceInr: 1960,
    currentPriceInr: 1960,
  });

  if (!atTarget?.message.includes("not entered")) {
    throw new Error("Journey wait path insight self-check failed: at target");
  }

  const inTrade = resolveJourneyWaitPathInsight({
    waitingForEntry: false,
    entryPriceInr: 1902,
    targetPriceInr: 1960,
    currentPriceInr: 1960,
  });

  if (inTrade !== null) {
    throw new Error("Journey wait path insight self-check failed: in trade");
  }

  const nearTarget = resolveJourneyWaitPathInsight({
    waitingForEntry: true,
    entryPriceInr: 1902,
    targetPriceInr: 2000,
    currentPriceInr: 1991,
  });

  if (!nearTarget?.message.includes("near")) {
    throw new Error("Journey wait path insight self-check failed: near target");
  }
}
