import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  formatJudgment,
  sanitizeVoiceText,
  voiceRegimeJudgment,
  voiceRegimeObservation,
  voiceRiskJudgment,
  voiceRiskObservation,
  voiceSignalJudgment,
  voiceSignalObservation,
  voiceStructureJudgment,
  voiceStructureObservation,
} from "@/lib/dailyLoop/apexVoice";
import {
  resolveExecutionPlanMarketRegime,
  type ExecutionPlanConviction,
  type ExecutionPlanMarketRegime,
} from "@/services/execution/executionPlanEngine";
import type { StockPick } from "@/types/decision";
import {
  isSellAction,
  type DecisionActionType,
} from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import {
  formatSetupWatchInsight,
  generateSetupInsightFromPick,
  type SetupInsight,
} from "@/lib/dailyLoop/setupInsight";

export const IDEAL_MAX_SINGLE_HOLDING_PCT = 25;

export type ConfidenceLevel = "Strong" | "Moderate" | "Weak";

export type ProtectAllocationInsight = {
  topSymbol?: string;
  currentPct: number;
  idealPct: number;
  sellPercent?: number;
  sellExplanation: string;
};

export type DecisionDepth = {
  whyBullets: string[];
  watchNext: string[];
  systemContext: {
    confidenceLevel: ConfidenceLevel;
    marketRegime: ExecutionPlanMarketRegime;
    conviction?: ExecutionPlanConviction;
  };
  protectAllocation?: ProtectAllocationInsight;
  exploreSetups: string[];
  exploreSetupItems: SetupInsight[];
};

export type DecisionDepthInput = {
  action: string;
  stock?: string;
  confidence?: number;
  structureScore?: number;
  reason?: string;
  message?: string;
  confidence_factors?: string[];
  validation?: {
    signal_strength?: number;
    signal_agreement?: boolean;
    market_alignment?: boolean;
    risk_ok?: boolean;
  };
  confidenceMetrics?: {
    probability?: number;
    expectedReturn?: number;
    edgeScore?: number;
  };
  picks?: StockPick[];
  allocation?: number;
  suggested_sell_percent?: number;
  allocationPercent?: number;
  allocationReason?: string;
  intent: UserIntent;
  entryTiming?: EntryTimingState;
  planConviction?: ExecutionPlanConviction;
  planMarketRegime?: ExecutionPlanMarketRegime;
  topSymbol?: string;
  topAllocationPct?: number;
};

function normalizePercent(value: number | undefined): number | undefined {
  if (value === undefined || !Number.isFinite(value)) {
    return undefined;
  }

  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

export function resolveConfidenceLevel(
  confidence?: number,
  probability?: number,
): ConfidenceLevel {
  const score =
    probability !== undefined
      ? normalizePercent(probability) ?? 50
      : Math.round(confidence ?? 50);

  if (score >= 75) {
    return "Strong";
  }

  if (score >= 55) {
    return "Moderate";
  }

  return "Weak";
}

function regimeNote(regime: ExecutionPlanMarketRegime): string {
  return voiceRegimeObservation(regime);
}

function formatSetupObservation(pick: StockPick, intent?: UserIntent): string {
  return formatSetupWatchInsight(generateSetupInsightFromPick(pick, intent));
}

export type { SetupInsight as ExploreSetupItem } from "@/lib/dailyLoop/setupInsight";

function isNoTradeAction(action: string): boolean {
  return (
    action === "wait" ||
    action === "hold" ||
    action === "explore"
  );
}

function buildWhyBullets(
  input: DecisionDepthInput,
  marketRegime: ExecutionPlanMarketRegime,
): string[] {
  const bullets: string[] = [];

  const structureObservation = voiceStructureObservation(input.structureScore);
  const structureJudgment = voiceStructureJudgment(
    input.structureScore,
    input.intent,
  );

  if (structureObservation && structureJudgment) {
    bullets.push(`${structureObservation} ${structureJudgment}`);
  }

  const signalObservation = voiceSignalObservation(
    input.validation?.signal_agreement,
  );
  const signalJudgment = voiceSignalJudgment(
    input.validation?.signal_agreement,
    input.intent,
  );

  if (signalObservation && signalJudgment && bullets.length < 3) {
    bullets.push(`${signalObservation} ${signalJudgment}`);
  }

  bullets.push(
    `${voiceRegimeObservation(marketRegime)} ${voiceRegimeJudgment(marketRegime, input.intent)}`,
  );

  const riskObservation = voiceRiskObservation(input.validation?.risk_ok);
  if (riskObservation && bullets.length < 3) {
    bullets.push(`${riskObservation} ${voiceRiskJudgment(input.intent)}`);
  }

  if (input.intent === "explore" && input.picks?.[0] && bullets.length < 3) {
    const lead = generateSetupInsightFromPick(input.picks[0], input.intent);
    bullets.unshift(`${lead.title} leads the field. ${formatSetupWatchInsight(lead)}`);
  }

  if (bullets.length < 2 && input.reason) {
    bullets.push(sanitizeVoiceText(input.reason));
  }

  return bullets.slice(0, 3);
}

function buildWatchNext(input: DecisionDepthInput): string[] {
  const action = input.action as DecisionActionType;
  const picks = input.picks ?? [];

  if (isSellAction(action) || action === "reduce" || action === "sell") {
    const symbol = input.stock ?? "this name";
    return [
      formatJudgment(`Re-entry in ${symbol} waits for a lighter book`, "patience matters"),
      "Trend and momentum must realign after the trim.",
      voiceRegimeJudgment("Unfavorable", input.intent),
    ].slice(0, 3);
  }

  if (isNoTradeAction(action)) {
    if (picks.length === 0) {
      return [
        formatJudgment("Nothing is clean today", "patience matters"),
        voiceRegimeJudgment(
          resolveExecutionPlanMarketRegime(input, input.entryTiming),
          input.intent,
        ),
      ];
    }

    return picks
      .slice(0, 3)
      .map((pick) => formatSetupObservation(pick, input.intent));
  }

  if (action === "buy") {
    const items: string[] = [];

    if (input.entryTiming?.enter) {
      items.push(formatJudgment("Stage the entry", "worth tracking"));
    } else {
      items.push(
        input.stock
          ? formatJudgment(`${input.stock} still needs confirmation`, "not ready yet")
          : formatJudgment("Price still needs confirmation", "not ready yet"),
      );
    }

    const alternates = picks
      .filter((pick) => pick.stock !== input.stock)
      .slice(0, 2)
      .map((pick) => formatSetupObservation(pick, input.intent));

    return [...items, ...alternates].slice(0, 3);
  }

  return picks
    .slice(0, 3)
    .map((pick) => formatSetupObservation(pick, input.intent));
}

function buildProtectAllocation(
  input: DecisionDepthInput,
): ProtectAllocationInsight | undefined {
  if (input.intent !== "protect") {
    return undefined;
  }

  const currentPct = Math.round(
    input.allocation ?? input.topAllocationPct ?? 0,
  );

  if (currentPct <= 0) {
    return undefined;
  }

  const topSymbol = input.stock ?? input.topSymbol;
  const sellPercent = input.suggested_sell_percent;
  const idealPct = IDEAL_MAX_SINGLE_HOLDING_PCT;

  let sellExplanation = formatJudgment(
    "Concentration needs air",
    "worth tracking",
  );

  if (sellPercent !== undefined && topSymbol) {
    sellExplanation =
      sellPercent === 25
        ? formatJudgment(
            `${topSymbol} is too heavy in the book — trim first`,
            "worth tracking",
          )
        : formatJudgment(
            `A ${sellPercent}% trim in ${topSymbol} rebalances the book`,
            "worth tracking",
          );
  } else if (currentPct > idealPct && topSymbol) {
    sellExplanation = formatJudgment(
      `${topSymbol} still dominates the book`,
      "avoid for now",
    );
  }

  return {
    topSymbol,
    currentPct,
    idealPct,
    sellPercent,
    sellExplanation,
  };
}

export function buildDecisionDepth(input: DecisionDepthInput): DecisionDepth {
  const marketRegime =
    input.planMarketRegime ??
    resolveExecutionPlanMarketRegime(input, input.entryTiming);

  const picks = input.picks ?? [];
  const topPicks = picks.slice(0, 3);

  return {
    whyBullets: buildWhyBullets(input, marketRegime),
    watchNext: buildWatchNext(input),
    systemContext: {
      confidenceLevel: resolveConfidenceLevel(
        input.confidence,
        input.confidenceMetrics?.probability,
      ),
      marketRegime,
      conviction: input.planConviction,
    },
    protectAllocation: buildProtectAllocation(input),
    exploreSetups: topPicks.map((pick) => formatSetupObservation(pick, input.intent)),
    exploreSetupItems: topPicks.map((pick) =>
      generateSetupInsightFromPick(pick, input.intent),
    ),
  };
}

export function convictionLabel(
  conviction: ExecutionPlanConviction | undefined,
): string | null {
  if (!conviction) {
    return null;
  }

  if (conviction === "strong") {
    return "Strong";
  }

  if (conviction === "moderate") {
    return "Moderate";
  }

  return "Weak";
}
