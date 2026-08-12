import {
  buildCapitalDecision,
  type CapitalDecision,
  type CapitalDecisionInput,
} from "@/lib/dailyLoop/capitalDecision";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";

export type TodayFocusPreviewInput = {
  action: string;
  stock?: string;
  picks?: StockPick[];
  allocationPercent?: number;
  suggested_sell_percent?: number;
  topAllocationPct?: number;
  availableCash?: number;
  ledgerCash?: number;
  portfolioValue?: number;
  collateral?: number;
  entryTiming?: EntryTimingState;
};

function summarizeGrowPreview(decision: CapitalDecision): string {
  const sell = decision.actions.find((item) => item.action === "SELL");
  if (sell) {
    return `Trim ${sell.symbol} before any new buy`;
  }

  const buy = decision.actions.find((item) => item.action === "BUY");
  if (buy && decision.deploymentPercentage > 0) {
    return `Deploy ${decision.deploymentPercentage}% into ${buy.symbol} when confirmed`;
  }

  const wait = decision.actions.find((item) => item.action === "WAIT");
  if (wait) {
    return `Wait on ${wait.symbol} — ${wait.reason.missing.toLowerCase()}`;
  }

  if (decision.deploymentPercentage <= 0) {
    return "No trade today — cash stays idle";
  }

  return decision.primaryAction;
}

function summarizeProtectPreview(decision: CapitalDecision): string {
  const sell = decision.actions.find((item) => item.action === "SELL");
  if (sell) {
    return `Reduce ${sell.symbol} before adding risk`;
  }

  const wait = decision.actions.find((item) => item.action === "WAIT");
  if (wait) {
    return `Risk guard — ${wait.symbol}: ${wait.reason.missing.toLowerCase()}`;
  }

  if (decision.deploymentPercentage <= 0) {
    return "Capital protected — no new deployment today";
  }

  return decision.primaryAction;
}

function summarizeExplorePreview(decision: CapitalDecision): string {
  if (decision.exploreSetups.length === 0) {
    return "Scanning — no watchlist items yet";
  }

  const top = decision.exploreSetups[0];
  const closeCount = decision.exploreSetups.filter(
    (item) => item.stage === "Close to readiness",
  ).length;

  if (closeCount > 0) {
    return `${closeCount} almost ready · top: ${top.symbol}`;
  }

  return `${decision.exploreSetups.length} on watch · top: ${top.symbol}`;
}

function toCapitalInput(
  intent: UserIntent,
  input: TodayFocusPreviewInput,
): CapitalDecisionInput {
  return {
    intent,
    action: input.action,
    stock: input.stock,
    picks: input.picks,
    allocationPercent: input.allocationPercent,
    suggested_sell_percent: input.suggested_sell_percent,
    topAllocationPct: input.topAllocationPct,
    availableCash: input.availableCash,
    ledgerCash: input.ledgerCash,
    portfolioValue: input.portfolioValue,
    collateral: input.collateral,
    entryTiming: input.entryTiming,
  };
}

export function buildTodayFocusPreviews(
  input: TodayFocusPreviewInput,
): Record<UserIntent, string> {
  const grow = buildCapitalDecision(toCapitalInput("grow", input));
  const protect = buildCapitalDecision(toCapitalInput("protect", input));
  const explore = buildCapitalDecision(toCapitalInput("explore", input));

  return {
    grow: summarizeGrowPreview(grow),
    protect: summarizeProtectPreview(protect),
    explore: summarizeExplorePreview(explore),
  };
}

export function runTodayFocusPreviewSelfCheck(): void {
  const previews = buildTodayFocusPreviews({
    action: "wait",
    stock: "DIVISLAB",
    picks: [
      {
        stock: "DIVISLAB",
        score: 72,
        signals: {
          trend: 1,
          momentum: 1,
          volume: 1,
        },
      },
    ],
    availableCash: 14_307,
    portfolioValue: 0,
    entryTiming: { enter: false, reason: "Breakout not confirmed" },
  });

  if (!previews.grow.toLowerCase().includes("wait")) {
    throw new Error("Today focus preview self-check failed: grow wait");
  }

  if (!previews.explore.includes("DIVISLAB")) {
    throw new Error("Today focus preview self-check failed: explore symbol");
  }

  if (previews.protect.length < 8) {
    throw new Error("Today focus preview self-check failed: protect preview");
  }
}
