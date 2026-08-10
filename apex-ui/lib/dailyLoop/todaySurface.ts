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
}
