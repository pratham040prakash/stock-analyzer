import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
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
  exploreSetupItems: ExploreSetupItem[];
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
  if (regime === "Favorable") {
    return "conditions support thoughtful action";
  }

  if (regime === "Neutral") {
    return "mixed signals — patience has an edge";
  }

  return "headwinds dominate — defense first";
}

function formatSetupObservation(pick: StockPick): string {
  return `${pick.stock} — trend ${pick.signals.trend}, momentum ${pick.signals.momentum}, alignment score ${Math.round(pick.score)}`;
}

export type ExploreSetupItem = {
  title: string;
  insight: string;
};

function buildExploreSetupItem(pick: StockPick): ExploreSetupItem {
  const agreement =
    pick.signals.trend >= 60 && pick.signals.momentum >= 60
      ? "Signals are aligning — worth studying the chart."
      : pick.signals.trend >= pick.signals.momentum
        ? "Trend leads — watch whether momentum catches up."
        : "Momentum is active — see if trend confirms it.";

  return {
    title: pick.stock,
    insight: agreement,
  };
}

function isNoTradeAction(action: string): boolean {
  return (
    action === "wait" ||
    action === "hold" ||
    action === "explore"
  );
}

function buildStructureBullet(structureScore?: number): string | null {
  if (structureScore === undefined) {
    return null;
  }

  const tone =
    structureScore >= 70
      ? "constructive"
      : structureScore >= 50
        ? "mixed"
        : "weak";

  return `Structure ${structureScore}/100 — price positioning looks ${tone}`;
}

function buildProbabilityBullet(
  confidence?: number,
  probability?: number,
): string | null {
  const pct = normalizePercent(probability ?? confidence);

  if (pct === undefined) {
    return null;
  }

  if (probability !== undefined) {
    return `Estimated success probability ${pct}%`;
  }

  return `Signal confidence ${pct}%`;
}

function buildRegimeBullet(
  input: DecisionDepthInput,
  marketRegime: ExecutionPlanMarketRegime,
): string {
  return `Market regime ${marketRegime} — ${regimeNote(marketRegime)}`;
}

function buildWhyBullets(
  input: DecisionDepthInput,
  marketRegime: ExecutionPlanMarketRegime,
): string[] {
  if (input.intent === "explore") {
    const bullets: string[] = [
      "Scanning aligned trend and momentum without requiring a trade",
      buildRegimeBullet(input, marketRegime),
    ];

    const top = input.picks?.[0];
    if (top) {
      bullets.unshift(
        `${top.stock} leads the watchlist on signal alignment today`,
      );
    }

    return bullets.slice(0, 3);
  }

  const bullets: string[] = [];

  const structureBullet = buildStructureBullet(input.structureScore);
  if (structureBullet) {
    bullets.push(structureBullet);
  }

  const probabilityBullet = buildProbabilityBullet(
    input.confidence,
    input.confidenceMetrics?.probability,
  );
  if (probabilityBullet) {
    bullets.push(probabilityBullet);
  }

  bullets.push(buildRegimeBullet(input, marketRegime));

  if (bullets.length < 3 && input.validation) {
    if (input.validation.signal_agreement) {
      bullets.push("Trend and momentum agree — the setup is internally consistent");
    } else if (bullets.length < 3) {
      bullets.push("Trend and momentum diverge — the edge is not clean");
    }

    if (bullets.length < 3 && input.validation.risk_ok === false) {
      bullets.push("Portfolio risk is elevated relative to your limits");
    }
  }

  if (bullets.length < 2 && input.confidence_factors?.length) {
    for (const factor of input.confidence_factors) {
      if (bullets.length >= 3) {
        break;
      }

      if (!bullets.includes(factor)) {
        bullets.push(factor);
      }
    }
  }

  if (bullets.length === 0 && input.reason) {
    bullets.push(input.reason);
  }

  return bullets.slice(0, 3);
}

function buildWatchNext(input: DecisionDepthInput): string[] {
  const action = input.action as DecisionActionType;
  const picks = input.picks ?? [];

  if (isSellAction(action) || action === "reduce" || action === "sell") {
    const symbol = input.stock ?? "this position";
    return [
      `Re-enter ${symbol} only if single-name weight falls below ${IDEAL_MAX_SINGLE_HOLDING_PCT}%`,
      "Trend and momentum need to realign after the trim",
      "Market regime should shift to Neutral or Favorable before adding back",
    ].slice(0, 3);
  }

  if (isNoTradeAction(action)) {
    if (picks.length === 0) {
      return [
        "Watch for trend and momentum to converge on a leader",
        "Note when market regime moves from Unfavorable to Neutral",
        "Track whether portfolio risk eases back into limits",
      ];
    }

    return picks.slice(0, 3).map(formatSetupObservation);
  }

  if (action === "buy") {
    const items: string[] = [];

    if (input.entryTiming?.enter) {
      items.push("Follow the staged entry — do not rush the full size");
    } else {
      items.push(
        input.stock
          ? `Wait for ${input.stock} to confirm before full deployment`
          : "Wait for price confirmation before full deployment",
      );
    }

    const alternates = picks
      .filter((pick) => pick.stock !== input.stock)
      .slice(0, 2)
      .map(formatSetupObservation);

    return [...items, ...alternates].slice(0, 3);
  }

  return picks.slice(0, 3).map(formatSetupObservation);
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

  let sellExplanation =
    "Ideal diversification keeps any single holding near 25% or below.";

  if (sellPercent !== undefined && topSymbol) {
    sellExplanation =
      sellPercent === 25
        ? `${topSymbol} is above 80% of the portfolio — a 25% trim is the first step toward a healthier ${idealPct}% cap.`
        : `Trimming ${sellPercent}% of ${topSymbol} reduces concentration toward the ${idealPct}% ideal per holding.`;
  } else if (currentPct > idealPct && topSymbol) {
    sellExplanation = `${topSymbol} at ${currentPct}% exceeds the ${idealPct}% ideal — reducing size protects against single-stock shock.`;
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
    exploreSetups: topPicks.map(formatSetupObservation),
    exploreSetupItems: topPicks.map(buildExploreSetupItem),
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
