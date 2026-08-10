import type { CapitalAction, CapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import { buildCapitalDecision } from "@/lib/dailyLoop/capitalDecision";

export type TodayExecutionKind = "WAIT" | "SELL" | "BUY" | "OBSERVE";

export type TodayHero = {
  headline: string;
  subline: string;
  executionKind: TodayExecutionKind;
  symbol?: string;
  /** Percent of holding quantity to sell (1–100). */
  sellPercent?: number;
  deployAmount?: number;
  targetWeightAfter?: number;
  currentWeight?: number;
};

export function sellPercentToReachTargetWeight(
  currentWeight: number,
  targetWeight: number,
): number {
  if (
    !Number.isFinite(currentWeight) ||
    !Number.isFinite(targetWeight) ||
    currentWeight <= 0 ||
    currentWeight <= targetWeight
  ) {
    return 0;
  }

  return Math.min(
    100,
    Math.max(1, Math.round(((currentWeight - targetWeight) / currentWeight) * 100)),
  );
}

function resolvePrimaryAction(decision: CapitalDecision): CapitalAction | undefined {
  return (
    decision.actions.find((action) => action.isPrimary) ??
    decision.actions.find((action) => action.action === "SELL") ??
    decision.actions.find((action) => action.action === "BUY") ??
    decision.actions[0]
  );
}

export function resolveTodayHero(
  decision: CapitalDecision,
  options?: {
    suggestedSellPercent?: number;
  },
): TodayHero {
  if (decision.mode === "explore") {
    return {
      headline: decision.heroHeadline,
      subline: decision.heroSubline,
      executionKind: "OBSERVE",
    };
  }

  const primary = resolvePrimaryAction(decision);

  if (primary?.action === "SELL") {
    const currentWeight = primary.portfolioWeight ?? 0;
    const targetWeight = primary.deployPercentage;
    const computed = sellPercentToReachTargetWeight(currentWeight, targetWeight);
    const suggested = options?.suggestedSellPercent;
    const sellPercent =
      typeof suggested === "number" &&
      suggested > 0 &&
      suggested <= 100
        ? Math.round(suggested)
        : computed;
    const resolvedSellPercent =
      sellPercent > 0 ? sellPercent : Math.round(primary.deployPercentage);
    const postTrimWeight =
      currentWeight > 0 && resolvedSellPercent > 0
        ? Math.max(
            0,
            Math.round(currentWeight * (1 - resolvedSellPercent / 100)),
          )
        : undefined;

    return {
      headline: `Trim ${primary.symbol} by ${resolvedSellPercent}% today`,
      subline:
        decision.primaryActionDetail ??
        "Reduce exposure before new deployment.",
      executionKind: "SELL",
      symbol: primary.symbol,
      sellPercent: resolvedSellPercent,
      targetWeightAfter: postTrimWeight,
      currentWeight,
    };
  }

  if (primary?.action === "BUY" && (primary.deployAmount ?? decision.deployAmount) > 0) {
    return {
      headline: decision.primaryAction,
      subline: decision.primaryActionDetail,
      executionKind: "BUY",
      symbol: primary.symbol,
      deployAmount: primary.deployAmount ?? decision.deployAmount,
    };
  }

  return {
    headline: decision.heroHeadline,
    subline: decision.heroSubline,
    executionKind: "WAIT",
    symbol: primary?.symbol,
  };
}

export function formatPostTrimWeightNote(
  actualWeight?: number,
  projectedWeight?: number,
): string {
  if (actualWeight !== undefined && Number.isFinite(actualWeight)) {
    return `Position now ~${Math.round(actualWeight)}% of portfolio.`;
  }

  if (projectedWeight !== undefined) {
    return `Target weight ~${projectedWeight}% after today's trim.`;
  }

  return "Broker step complete for today.";
}

/** After a logged broker fill, swap action CTAs for completion copy on Today. */
export function resolveTodayHeroDisplay(
  hero: TodayHero,
  brokerStepCompleted: boolean,
  options?: { actualPortfolioWeight?: number },
): TodayHero {
  if (!brokerStepCompleted) {
    return hero;
  }

  if (hero.executionKind === "SELL" && hero.symbol) {
    const weightNote = formatPostTrimWeightNote(
      options?.actualPortfolioWeight,
      hero.targetWeightAfter,
    );

    return {
      ...hero,
      headline: `${hero.symbol} trim logged on Zerodha`,
      subline: weightNote,
    };
  }

  if (hero.executionKind === "BUY" && hero.symbol) {
    return {
      ...hero,
      headline: `${hero.symbol} entry logged on Zerodha`,
      subline: "Verify entry and stop orders in Kite.",
    };
  }

  return hero;
}

export function runTodaySurfaceSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Today surface self-check failed: ${message}`);
    }
  };

  assert(
    sellPercentToReachTargetWeight(100, 25) === 75,
    "Sell percent must reach target weight from full concentration",
  );
  assert(
    sellPercentToReachTargetWeight(32, 25) === 22,
    "Sell percent must trim overweight positions",
  );
  assert(
    sellPercentToReachTargetWeight(20, 25) === 0,
    "No sell when already at or below target weight",
  );

  const trimDecision = buildCapitalDecision({
    intent: "grow",
    action: "wait",
    stock: "JIOFIN",
    availableCash: 9_631,
    portfolioValue: 257,
    topAllocationPct: 100,
    suggested_sell_percent: 25,
    entryTiming: { enter: false },
  });

  const trimHero = resolveTodayHero(trimDecision, { suggestedSellPercent: 25 });

  assert(
    trimHero.executionKind === "SELL",
    "Today hero must execute as SELL when concentration trim is primary",
  );
  assert(
    trimHero.headline.includes("Trim JIOFIN"),
    "Today hero headline must name the trim action",
  );
  assert(
    trimHero.targetWeightAfter === 75,
    "Post-trim weight must reflect shares sold, not trim percent",
  );
  assert(
    !trimHero.headline.includes("Remain fully in cash"),
    "Today hero must not show cash-only copy during required trim",
  );

  const completedTrim = resolveTodayHeroDisplay(trimHero, true);
  assert(
    completedTrim.headline.includes("logged on Zerodha"),
    "Completed trim hero must reflect broker logging",
  );
  assert(
    !completedTrim.headline.includes("Trim JIOFIN by"),
    "Completed trim hero must not repeat the action CTA",
  );

  const actualWeightNote = formatPostTrimWeightNote(72, 75);
  assert(
    actualWeightNote.includes("72%") && actualWeightNote.includes("now"),
    "Actual portfolio weight must override projected trim copy",
  );
}
