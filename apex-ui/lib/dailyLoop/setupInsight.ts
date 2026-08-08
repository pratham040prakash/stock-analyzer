import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import {
  formatJudgment,
  resolveIntentEnding,
  type IntentEnding,
} from "@/lib/dailyLoop/apexVoice";

export type SetupInsight = {
  title: string;
  line1: string;
  line2: string;
  ending: IntentEnding;
};

export type SetupInsightInput = {
  stockName: string;
  trendScore: number;
  momentumScore: number;
  alignmentScore: number;
  intent?: UserIntent;
};

function trendObservation(score: number): string {
  if (score > 75) {
    return "Trend is strong.";
  }

  if (score >= 60) {
    return "Trend is developing.";
  }

  return "Trend is soft.";
}

function momentumObservation(score: number): string {
  if (score > 75) {
    return "Momentum is holding.";
  }

  if (score >= 60) {
    return "Momentum is building.";
  }

  return "Momentum is fading.";
}

function structureJudgment(score: number): string {
  if (score > 80) {
    return "Structure is aligned";
  }

  if (score >= 65) {
    return "Structure is forming";
  }

  return "Structure is mixed";
}

/** Converts internal signal scores into APEX observation + judgment voice. */
export function generateSetupInsight(setup: SetupInsightInput): SetupInsight {
  const ending = resolveIntentEnding(setup.alignmentScore, setup.intent);

  return {
    title: setup.stockName,
    line1: `${trendObservation(setup.trendScore)} ${momentumObservation(setup.momentumScore)}`,
    line2: formatJudgment(structureJudgment(setup.alignmentScore), ending),
    ending,
  };
}

export function generateSetupInsightFromPick(
  pick: StockPick,
  intent?: UserIntent,
): SetupInsight {
  return generateSetupInsight({
    stockName: pick.stock,
    trendScore: pick.signals.trend,
    momentumScore: pick.signals.momentum,
    alignmentScore: Math.round(pick.score),
    intent,
  });
}

export function formatSetupWatchInsight(insight: SetupInsight): string {
  return `${insight.line1} ${insight.line2}`;
}
