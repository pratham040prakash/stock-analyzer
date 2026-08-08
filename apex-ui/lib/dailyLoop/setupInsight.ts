import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import {
  formatJudgment,
  type IntentEnding,
} from "@/lib/dailyLoop/apexVoice";

export type SetupInsightFormat = "split" | "single";

export type SetupInsight = {
  title: string;
  line1: string;
  line2: string;
  ending: IntentEnding;
  format: SetupInsightFormat;
};

export type SetupInsightInput = {
  stockName: string;
  trendScore: number;
  momentumScore: number;
  alignmentScore: number;
  intent?: UserIntent;
};

const TREND_STRONG = [
  "Trend is strong",
  "Clear directional strength",
  "Trend is holding firm",
] as const;

const TREND_DEVELOPING = [
  "Trend is developing",
  "Direction is emerging",
  "Trend is finding its footing",
] as const;

const TREND_SOFT = [
  "Trend is soft",
  "Direction lacks conviction",
  "Trend is unsettled",
] as const;

const MOMENTUM_HOLDING = [
  "Momentum is holding",
  "Strength is sustained",
  "Momentum remains steady",
] as const;

const MOMENTUM_BUILDING = [
  "Momentum is improving",
  "Momentum is picking up",
  "Early momentum building",
] as const;

const MOMENTUM_FADING = [
  "Momentum is fading",
  "Follow-through is weakening",
  "Momentum is slipping",
] as const;

const ALIGNMENT_HIGH = [
  "Structure is aligned",
  "Conditions are lining up",
  "Setup is coming together",
] as const;

const ALIGNMENT_FORMING = [
  "Structure is forming",
  "Pieces are assembling",
  "Setup is taking shape",
] as const;

const ALIGNMENT_MIXED = [
  "Structure is mixed",
  "Conditions are incomplete",
  "Setup lacks cohesion",
] as const;

function stableIndex(seed: string, salt: string, size: number): number {
  if (size <= 0) {
    return 0;
  }

  let hash = 0;
  const key = `${seed}|${salt}`;

  for (let index = 0; index < key.length; index += 1) {
    hash = (hash * 31 + key.charCodeAt(index)) >>> 0;
  }

  return hash % size;
}

function pickPhrase(
  seed: string,
  salt: string,
  pool: readonly string[],
): string {
  return pool[stableIndex(seed, salt, pool.length)] ?? pool[0];
}

function capitalize(text: string): string {
  if (!text) {
    return text;
  }

  return text.charAt(0).toUpperCase() + text.slice(1);
}

function lowercaseLead(text: string): string {
  if (!text) {
    return text;
  }

  return text.charAt(0).toLowerCase() + text.slice(1);
}

function trendPool(score: number): readonly string[] {
  if (score > 75) {
    return TREND_STRONG;
  }

  if (score >= 60) {
    return TREND_DEVELOPING;
  }

  return TREND_SOFT;
}

function momentumPool(score: number): readonly string[] {
  if (score > 75) {
    return MOMENTUM_HOLDING;
  }

  if (score >= 60) {
    return MOMENTUM_BUILDING;
  }

  return MOMENTUM_FADING;
}

function alignmentPool(score: number): readonly string[] {
  if (score > 80) {
    return ALIGNMENT_HIGH;
  }

  if (score >= 65) {
    return ALIGNMENT_FORMING;
  }

  return ALIGNMENT_MIXED;
}

function resolveSetupEnding(
  alignmentScore: number,
  intent?: UserIntent,
): IntentEnding {
  if (alignmentScore > 80) {
    return "worth tracking";
  }

  if (alignmentScore >= 65) {
    return "not ready yet";
  }

  if (intent === "protect") {
    return "avoid for now";
  }

  return "wait for clarity";
}

/** Converts internal signal scores into varied APEX setup voice. */
export function generateSetupInsight(setup: SetupInsightInput): SetupInsight {
  const seed = setup.stockName.trim().toUpperCase();
  const ending = resolveSetupEnding(setup.alignmentScore, setup.intent);
  const trend = pickPhrase(seed, "trend", trendPool(setup.trendScore));
  const momentum = pickPhrase(seed, "momentum", momentumPool(setup.momentumScore));
  const alignment = pickPhrase(
    seed,
    "alignment",
    alignmentPool(setup.alignmentScore),
  );
  const useSingleFormat = stableIndex(seed, "format", 2) === 0;

  if (useSingleFormat) {
    return {
      title: setup.stockName,
      line1: `${trend}, ${lowercaseLead(momentum)} — ${ending}.`,
      line2: "",
      ending,
      format: "single",
    };
  }

  return {
    title: setup.stockName,
    line1: `${capitalize(trend)}. ${capitalize(momentum)}.`,
    line2: formatJudgment(alignment, ending),
    ending,
    format: "split",
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
  if (insight.format === "single" || !insight.line2) {
    return insight.line1;
  }

  return `${insight.line1} ${insight.line2}`;
}
