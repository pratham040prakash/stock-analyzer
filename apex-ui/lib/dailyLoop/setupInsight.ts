import type { StockPick } from "@/types/decision";

export type SetupInsightTag = "Watch closely" | "Early" | "Wait";

export type SetupInsightInput = {
  stockName: string;
  trendScore: number;
  momentumScore: number;
  alignmentScore: number;
};

export type SetupInsight = {
  title: string;
  line1: string;
  line2: string;
  tag: SetupInsightTag;
};

function trendPhrase(score: number): string {
  if (score > 75) {
    return "Strong trend";
  }

  if (score >= 60) {
    return "Developing trend";
  }

  return "Weak trend";
}

function momentumPhrase(score: number): string {
  if (score > 75) {
    return "with strong momentum";
  }

  if (score >= 60) {
    return "with building momentum";
  }

  return "with fading momentum";
}

function alignmentPhrase(score: number): string {
  if (score > 80) {
    return "Well aligned setup";
  }

  if (score >= 65) {
    return "Reasonable setup";
  }

  return "Not fully aligned";
}

function resolveTag(alignmentScore: number): SetupInsightTag {
  if (alignmentScore > 80) {
    return "Watch closely";
  }

  if (alignmentScore >= 65) {
    return "Early";
  }

  return "Wait";
}

/** Converts internal signal scores into calm, human-readable setup insight. */
export function generateSetupInsight(setup: SetupInsightInput): SetupInsight {
  return {
    title: setup.stockName,
    line1: `${trendPhrase(setup.trendScore)} ${momentumPhrase(setup.momentumScore)}`,
    line2: alignmentPhrase(setup.alignmentScore),
    tag: resolveTag(setup.alignmentScore),
  };
}

export function generateSetupInsightFromPick(pick: StockPick): SetupInsight {
  return generateSetupInsight({
    stockName: pick.stock,
    trendScore: pick.signals.trend,
    momentumScore: pick.signals.momentum,
    alignmentScore: Math.round(pick.score),
  });
}

export function formatSetupWatchInsight(insight: SetupInsight): string {
  return `${insight.title} — ${insight.line1}. ${insight.line2}.`;
}
