import type { DisciplineHistoryEntry } from "@/types/decisionHistory";
import { MAX_DAILY_LOSS_PCT } from "@/services/risk/riskControl";
import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";

export type DailyVerdict = "wait" | "trade" | "pause";

export const PAUSE_LOSS_STREAK_THRESHOLD = 2;

export type DailyVerdictInput = {
  executionKind: TodayExecutionKind;
  entryConfirmed?: boolean;
  consecutiveLossDays?: number;
  portfolioDayPnl?: number | null;
  portfolioValue?: number | null;
  riskBlocked?: boolean;
  brokerStepCompleted?: boolean;
  brokerStepSkipped?: boolean;
};

export type DailyVerdictPresentation = {
  verdict: DailyVerdict;
  displayWord: string;
  headline: string;
  subline: string;
  ctaLabel: string;
  doneForToday: boolean;
  tradingLocked: boolean;
  pauseReason?: string;
};

export function countConsecutiveLossDays(
  history: DisciplineHistoryEntry[],
  dayKeys: string[],
): number {
  let streak = 0;

  for (const date of [...dayKeys].reverse()) {
    const dayEntries = history.filter((entry) => entry.date === date);

    if (dayEntries.length === 0) {
      continue;
    }

    const closedLoss = dayEntries.some((entry) => entry.outcome === "loss");
    const closedWin = dayEntries.some((entry) => entry.outcome === "win");

    if (closedLoss && !closedWin) {
      streak += 1;
      continue;
    }

    if (closedLoss || closedWin) {
      break;
    }
  }

  return streak;
}

export function isDailyLossLimitBreached(
  portfolioDayPnl: number | null | undefined,
  portfolioValue: number | null | undefined,
  maxLossPct = MAX_DAILY_LOSS_PCT,
): boolean {
  if (
    portfolioDayPnl === null ||
    portfolioDayPnl === undefined ||
    !Number.isFinite(portfolioDayPnl) ||
    portfolioDayPnl >= 0
  ) {
    return false;
  }

  if (
    portfolioValue === null ||
    portfolioValue === undefined ||
    !Number.isFinite(portfolioValue) ||
    portfolioValue <= 0
  ) {
    return false;
  }

  return Math.abs(portfolioDayPnl) >= portfolioValue * maxLossPct;
}

export function resolvePauseReason(input: DailyVerdictInput): string | undefined {
  if ((input.consecutiveLossDays ?? 0) >= PAUSE_LOSS_STREAK_THRESHOLD) {
    return "Recent loss days — sit out today and protect capital.";
  }

  if (isDailyLossLimitBreached(input.portfolioDayPnl, input.portfolioValue)) {
    return `Daily loss limit reached (${Math.round(MAX_DAILY_LOSS_PCT * 100)}% of portfolio).`;
  }

  if (input.riskBlocked) {
    return "Risk controls flagged today — no new trades.";
  }

  return undefined;
}

export function resolveDailyVerdict(input: DailyVerdictInput): DailyVerdict {
  if (resolvePauseReason(input)) {
    return "pause";
  }

  if (input.brokerStepCompleted || input.brokerStepSkipped) {
    return "wait";
  }

  if (input.executionKind === "BUY") {
    return input.entryConfirmed ? "trade" : "wait";
  }

  if (input.executionKind === "SELL") {
    return "trade";
  }

  return "wait";
}

export function formatDailyVerdictDisplay(verdict: DailyVerdict): string {
  switch (verdict) {
    case "trade":
      return "Trade";
    case "pause":
      return "Pause";
    default:
      return "Wait";
  }
}

export function buildDailyVerdictPresentation(input: {
  verdictInput: DailyVerdictInput;
  heroHeadline: string;
  heroSubline: string;
}): DailyVerdictPresentation {
  const pauseReason = resolvePauseReason(input.verdictInput);
  const verdict = resolveDailyVerdict(input.verdictInput);
  const displayWord = formatDailyVerdictDisplay(verdict);

  if (verdict === "pause") {
    return {
      verdict,
      displayWord,
      headline: "Pause trading today",
      subline:
        pauseReason ??
        "Protect capital before adding risk. Your long-term holdings stay unchanged.",
      ctaLabel: "You're done for today",
      doneForToday: true,
      tradingLocked: true,
      pauseReason,
    };
  }

  if (verdict === "wait") {
    const setupNotReady =
      input.verdictInput.executionKind === "BUY" && !input.verdictInput.entryConfirmed;

    return {
      verdict,
      displayWord,
      headline: setupNotReady
        ? "Wait for entry confirmation"
        : input.heroHeadline || "Wait today",
      subline: setupNotReady
        ? "Breakout is not confirmed yet — price, volume, and momentum must align before risking capital."
        : input.heroSubline ||
          "Nothing worth risking capital on today. Staying in cash is an active decision.",
      ctaLabel: "You're done for today",
      doneForToday: true,
      tradingLocked: true,
    };
  }

  return {
    verdict,
    displayWord,
    headline: input.heroHeadline,
    subline: input.heroSubline,
    ctaLabel:
      input.verdictInput.executionKind === "SELL"
        ? "Review trim plan"
        : "Review entry plan",
    doneForToday: false,
    tradingLocked: false,
  };
}

/** @deprecated Use formatDailyVerdictDisplay after resolveDailyVerdict. */
export function legacyVerdictWordFromExecutionKind(
  executionKind: TodayExecutionKind,
): string {
  switch (executionKind) {
    case "BUY":
      return "ACT";
    case "SELL":
      return "TRIM";
    case "OBSERVE":
      return "EXPLORE";
    default:
      return "WAIT";
  }
}

export function runDailyVerdictSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Daily verdict self-check failed: ${message}`);
    }
  };

  assert(
    resolveDailyVerdict({
      executionKind: "BUY",
      entryConfirmed: false,
    }) === "wait",
    "Unconfirmed buy must wait",
  );

  assert(
    resolveDailyVerdict({
      executionKind: "BUY",
      entryConfirmed: true,
    }) === "trade",
    "Confirmed buy may trade",
  );

  assert(
    resolveDailyVerdict({
      executionKind: "SELL",
    }) === "trade",
    "Required trim maps to trade",
  );

  assert(
    resolveDailyVerdict({
      executionKind: "BUY",
      entryConfirmed: true,
      consecutiveLossDays: 2,
    }) === "pause",
    "Loss streak must pause",
  );

  assert(
    resolveDailyVerdict({
      executionKind: "BUY",
      entryConfirmed: true,
      portfolioDayPnl: -500,
      portfolioValue: 10_000,
    }) === "pause",
    "Daily loss dam must pause",
  );

  const waitPresentation = buildDailyVerdictPresentation({
    verdictInput: {
      executionKind: "WAIT",
    },
    heroHeadline: "Stay patient",
    heroSubline: "No deployment today.",
  });
  assert(waitPresentation.displayWord === "Wait", "Wait presentation word");
  assert(waitPresentation.tradingLocked, "Wait must lock trading");

  const pausePresentation = buildDailyVerdictPresentation({
    verdictInput: {
      executionKind: "BUY",
      entryConfirmed: true,
      consecutiveLossDays: 3,
    },
    heroHeadline: "Ignored",
    heroSubline: "Ignored",
  });
  assert(pausePresentation.verdict === "pause", "Pause presentation verdict");
  assert(pausePresentation.doneForToday, "Pause must be done for today");

  assert(
    countConsecutiveLossDays(
      [
        {
          date: "2026-08-08",
          action: "buy",
          outcome: "loss",
          outcomeLabel: "Closed loss",
          source: "executed",
        },
        {
          date: "2026-08-09",
          action: "buy",
          outcome: "loss",
          outcomeLabel: "Closed loss",
          source: "executed",
        },
      ],
      ["2026-08-07", "2026-08-08", "2026-08-09"],
    ) === 2,
    "Consecutive loss days must count from recent history",
  );
}
