import type { StockPick } from "@/types/decision";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import { formatInr } from "@/lib/funds";
import { getTrustMicroReward } from "@/lib/dailyLoop/disciplineStreak";
import { attachCapitalProjections } from "@/lib/dailyLoop/capitalProjection";
import {
  attachCapitalFinalState,
  type CapitalFinalState,
} from "@/lib/dailyLoop/capitalFinalState";
import { attachDecisionLock, type CapitalDecisionLock } from "@/lib/dailyLoop/capitalDecisionLock";
import type { CapitalFundingMode } from "@/lib/dailyLoop/capitalMargin";
import {
  applyMarginPolicy,
  applyMarginToDecisionLock,
} from "@/lib/dailyLoop/capitalMargin";

export type DeploymentStance =
  | "No Deployment"
  | "Partial Deployment"
  | "Active Deployment";

export type CapitalActionType = "BUY" | "WAIT" | "SELL";

export type GrowActionStage = "close" | "developing" | "early";

export type CapitalActionReason = {
  missing: string;
  confirm: string;
  timing: string;
};

export type CapitalActionProjection = {
  cashAfter: number;
  weightAfter: number;
  note: string;
  warning?: string;
};

export type CapitalAction = {
  symbol: string;
  action: CapitalActionType;
  deployPercentage: number;
  deployAmount?: number;
  portfolioWeight?: number;
  stage?: GrowActionStage;
  reason: CapitalActionReason;
  ifIgnored?: string;
  postActionImpact?: string;
  postAction?: CapitalActionProjection;
  isPrimary?: boolean;
};

export type CapitalHoldingWeight = {
  symbol: string;
  weight: number;
};

export type CapitalStructure = {
  availableCash: number;
  portfolioValue: number;
  totalCapital: number;
};

export type DecisionMode = "grow" | "explore" | "protect";

export type ExplorePipelineStage =
  | "Close to readiness"
  | "Developing setup"
  | "Early formation";

export type ExplorePriorityMarker = "Closest to activation" | "High priority";

export type ExploreSetup = {
  symbol: string;
  scanLine: string;
  stageLine: string;
  stage: ExplorePipelineStage;
  priorityMarker?: ExplorePriorityMarker;
  setupDescription: string;
  progressDelta: string;
  progressLine: string;
  whyThisMatters?: string;
  activation: string;
  timeHorizon: string;
  readinessScore: number;
  isPrimary?: boolean;
};

export const EXPLORE_PIPELINE_EMPTY_HEADLINE =
  "Nothing close to activation yet.";
export const EXPLORE_PIPELINE_EMPTY_BODY =
  "APEX is scanning for setups — opportunities enter the pipeline as conditions improve.";

export type { CapitalFinalPosition, CapitalFinalState } from "@/lib/dailyLoop/capitalFinalState";
export type { CapitalDecisionLock, DecisionLockType } from "@/lib/dailyLoop/capitalDecisionLock";
export type { CapitalFundingMode } from "@/lib/dailyLoop/capitalMargin";

export type CapitalDecision = {
  mode: DecisionMode;
  stance: DeploymentStance;
  availableCash: number;
  portfolioValue: number;
  totalCapital: number;
  deployAmount: number;
  cashPercentage: number;
  deploymentPercentage: number;
  capitalMode: CapitalFundingMode;
  collateral: number;
  deployableCapital: number;
  marginWarning?: string | null;
  marginBlocked?: boolean;
  actions: CapitalAction[];
  finalState?: CapitalFinalState;
  decisionLock?: CapitalDecisionLock;
  exploreSetups: ExploreSetup[];
  explorePipelineSummary?: string;
  growEmptyMessage?: string;
  heroHeadline: string;
  heroSubline: string;
  heroDecisionCue?: string;
  behaviorLock?: string;
  heroAccountability: string;
  portfolioStance: string;
  portfolioStanceDetail: string;
  primaryAction: string;
  primaryActionDetail: string;
};

export type CapitalDecisionInput = {
  intent: UserIntent;
  action: string;
  stock?: string;
  picks?: StockPick[];
  allocationPercent?: number;
  suggested_sell_percent?: number;
  topAllocationPct?: number;
  availableCash?: number;
  /** Ledger cash from Zerodha — used for total capital and margin pool sizing. */
  ledgerCash?: number;
  portfolioValue?: number;
  holdings?: CapitalHoldingWeight[];
  capitalMode?: CapitalFundingMode;
  collateral?: number;
  entryTiming?: { enter?: boolean };
  confidence?: number;
};

const FORBIDDEN_COPY = /\b(good setup|bad setup|strong|weak|not enough edge)\b/i;
const GROW_EMPTY_MESSAGE = "No capital deployment allowed today.";
const CONCENTRATION_LIMIT = 25;

function resolveCapitalStructure(input: CapitalDecisionInput): CapitalStructure {
  const availableCash = Math.max(0, Math.round(input.availableCash ?? 0));
  const ledgerCash = Math.max(
    0,
    Math.round(input.ledgerCash ?? input.availableCash ?? 0),
  );
  const portfolioValue = Math.max(0, Math.round(input.portfolioValue ?? 0));

  return {
    availableCash,
    portfolioValue,
    totalCapital: ledgerCash + portfolioValue,
  };
}

function resolveOverweightHoldings(
  input: CapitalDecisionInput,
): CapitalHoldingWeight[] {
  const capital = resolveCapitalStructure(input);

  if (capital.portfolioValue <= 0) {
    return [];
  }

  if (input.holdings?.length) {
    return input.holdings
      .filter((holding) => holding.weight > CONCENTRATION_LIMIT)
      .sort((left, right) => right.weight - left.weight);
  }

  const topWeight = normalizePercent(input.topAllocationPct);

  if (topWeight > CONCENTRATION_LIMIT && input.stock) {
    return [{ symbol: input.stock, weight: topWeight }];
  }

  return [];
}

function computeDeployAmount(cash: number, deploymentPercentage: number): number {
  if (cash <= 0 || deploymentPercentage <= 0) {
    return 0;
  }

  return Math.round((deploymentPercentage / 100) * cash);
}

function computeTrimPercentTo25(weight: number): number {
  if (weight <= CONCENTRATION_LIMIT) {
    return 0;
  }

  return Math.min(
    100,
    Math.max(1, Math.round((1 - CONCENTRATION_LIMIT / weight) * 100)),
  );
}

function canDeployCapital(
  input: CapitalDecisionInput,
  capital: CapitalStructure,
  overweight: CapitalHoldingWeight[],
  deploymentPercentage: number,
): boolean {
  if (deploymentPercentage <= 0 || capital.availableCash <= 0) {
    return false;
  }

  if (overweight.length > 0 && input.action === "buy") {
    return false;
  }

  return true;
}

export function validateCapitalDecision(decision: CapitalDecision): void {
  const hasBuy = decision.actions.some((item) => item.action === "BUY");
  const hasOverweightSell = decision.actions.some(
    (item) =>
      item.action === "SELL" &&
      (item.portfolioWeight ?? 0) > CONCENTRATION_LIMIT,
  );

  if (decision.availableCash <= 0 && hasBuy) {
    throw new Error("Capital validation: BUY allowed without cash");
  }

  if (hasOverweightSell && hasBuy) {
    throw new Error("Capital validation: BUY allowed during concentration risk");
  }

  if (decision.deploymentPercentage > 0 && decision.deployAmount <= 0) {
    throw new Error("Capital validation: deployment shown without ₹ value");
  }

  for (const action of decision.actions) {
    if (action.action !== "BUY") {
      continue;
    }

    if (action.deployAmount === undefined || action.deployAmount <= 0) {
      throw new Error("Capital validation: BUY deployment without ₹ value");
    }
  }
}

function normalizePercent(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) {
    return 0;
  }

  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

function sanitizeCopy(text: string): string {
  return text.replace(FORBIDDEN_COPY, "").replace(/\s{2,}/g, " ").trim();
}

function resolveStance(deploymentPercentage: number): DeploymentStance {
  if (deploymentPercentage <= 0) {
    return "No Deployment";
  }

  if (deploymentPercentage < 50) {
    return "Partial Deployment";
  }

  return "Active Deployment";
}

function resolveDeploymentPercentage(input: CapitalDecisionInput): number {
  const action = input.action;

  if (input.intent === "explore" || action === "explore") {
    return 0;
  }

  if (action === "wait" || action === "hold") {
    return 0;
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return 0;
  }

  if (action === "buy") {
    if (input.entryTiming?.enter === false) {
      return 0;
    }

    const explicit = normalizePercent(input.allocationPercent);
    return explicit > 0 ? explicit : 20;
  }

  return 0;
}

function findPick(input: CapitalDecisionInput, symbol: string): StockPick | undefined {
  return input.picks?.find((pick) => pick.stock === symbol);
}

function deployLabel(deployPercentage: number, deployAmount?: number): string {
  if (deployAmount !== undefined && deployAmount > 0) {
    return `Deploy ${formatInr(deployAmount)} (${deployPercentage}% of available cash)`;
  }

  return `Deploy ${deployPercentage}% of available cash`;
}

export function formatGrowActionStage(stage: GrowActionStage): string {
  if (stage === "close") {
    return "Close to trigger";
  }

  if (stage === "developing") {
    return "Developing setup";
  }

  return "Early stage";
}

function resolveWaitStage(pick: StockPick | undefined): GrowActionStage {
  if (!pick) {
    return "early";
  }

  const score = Math.round(pick.score);

  if (score >= 70) {
    return "close";
  }

  if (score >= 55) {
    return "developing";
  }

  return "early";
}

function waitTiming(stage: GrowActionStage): string {
  if (stage === "close") {
    return "Act within 1–2 sessions after confirmation.";
  }

  if (stage === "developing") {
    return "Wait — reassess in 2–3 sessions.";
  }

  return "No action — setup not ready.";
}

function buildBuyConfirm(pick: StockPick | undefined): string {
  const level = pick ? resolveActivationLevel(pick) : undefined;

  if (level) {
    return `Buy above ${formatInr(level)} with volume.`;
  }

  return "Buy above breakout with volume.";
}

function buildHeroDecisionCue(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  actions: CapitalAction[],
): string {
  const hasSell =
    actions.some((item) => item.action === "SELL") ||
    isSellAction(input.action as DecisionActionType) ||
    input.action === "sell";

  if (hasSell) {
    return "Capital reduction required.";
  }

  if (deploymentPercentage > 0) {
    return "Capital deployment is active.";
  }

  return "No capital deployed today.";
}

function buildBehaviorLock(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  actions: CapitalAction[],
): string | undefined {
  const hasSell =
    actions.some((item) => item.action === "SELL") ||
    isSellAction(input.action as DecisionActionType) ||
    input.action === "sell";
  const hasWait = actions.some((item) => item.action === "WAIT");

  if (hasSell) {
    return "Reduce exposure before new deployment.";
  }

  if (deploymentPercentage === 0) {
    return "Do not deploy capital today.";
  }

  if (hasWait) {
    return "Do not act until conditions confirm.";
  }

  return undefined;
}

function buildHeroHeadline(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  cashPercentage: number,
  actions: CapitalAction[] = [],
): string {
  const action = input.action;
  const prioritizedSell = actions.find((item) => item.action === "SELL");

  if (prioritizedSell) {
    return `Trim ${prioritizedSell.deployPercentage}% of ${prioritizedSell.symbol} before deploying.`;
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    const trimPct = normalizePercent(input.suggested_sell_percent) || 25;
    return input.stock
      ? `Trim ${trimPct}% of ${input.stock}.`
      : "Trim exposure to protect capital.";
  }

  if (deploymentPercentage <= 0) {
    return `${cashPercentage}% of available cash stays idle.`;
  }

  return `Deploy ${deploymentPercentage}% of available cash today.`;
}

function buildHeroSubline(
  input: CapitalDecisionInput,
  stance: DeploymentStance,
  cashPercentage: number,
  deploymentPercentage: number,
  actions: CapitalAction[] = [],
): string {
  const action = input.action;
  const prioritizedSell = actions.find((item) => item.action === "SELL");

  if (prioritizedSell) {
    return (
      prioritizedSell.postActionImpact ??
      "Reduce exposure before new deployment."
    );
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return "Delaying trim keeps concentration risk.";
  }

  if (stance === "No Deployment") {
    if (action === "buy" && input.entryTiming?.enter === false) {
      return "Deploying now increases risk without confirmation.";
    }

    return "Deploying now increases risk without confirmation.";
  }

  if (stance === "Partial Deployment") {
    return `${cashPercentage}% stays in cash — exceeding this adds risk.`;
  }

  return `${cashPercentage}% stays in cash — exceeding this adds risk.`;
}

type WaitContext = {
  stage: GrowActionStage;
  reason: CapitalActionReason;
  ifIgnored: string;
};

function resolveWaitContext(
  pick: StockPick | undefined,
  input: CapitalDecisionInput,
  isPrimary: boolean,
  concentrationBlocked = false,
): WaitContext {
  const stage = resolveWaitStage(pick);
  const timing = waitTiming(stage);

  if (isPrimary && input.action === "buy" && input.entryTiming?.enter === false) {
    return {
      stage: "close",
      reason: {
        missing: "Breakout not confirmed.",
        confirm: sanitizeCopy(buildBuyConfirm(pick)),
        timing: waitTiming("close"),
      },
      ifIgnored: "If ignored: capital exposed to false breakout.",
    };
  }

  if (input.intent === "protect" && isPrimary && concentrationBlocked) {
    return {
      stage,
      reason: {
        missing: "Concentration not cleared.",
        confirm: "Buy after trim completes.",
        timing,
      },
      ifIgnored: "If ignored: capital enters before confirmation.",
    };
  }

  if (!pick) {
    return {
      stage: "early",
      reason: {
        missing: "Trigger not confirmed.",
        confirm: "Buy when lead symbol confirms.",
        timing: "No action — setup not ready.",
      },
      ifIgnored: "If ignored: capital enters before confirmation.",
    };
  }

  const alignment = Math.round(pick.score);
  const { trend, momentum } = pick.signals;

  if (alignment < 65) {
    return {
      stage,
      reason: {
        missing: "Breakout not confirmed.",
        confirm: "Buy above threshold on close.",
        timing,
      },
      ifIgnored: "If ignored: capital deploys below threshold.",
    };
  }

  if (trend < 60) {
    return {
      stage,
      reason: {
        missing: "Breakout not confirmed.",
        confirm: sanitizeCopy(buildBuyConfirm(pick)),
        timing,
      },
      ifIgnored: "If ignored: capital enters before confirmation.",
    };
  }

  if (momentum < 60) {
    return {
      stage,
      reason: {
        missing: "Volume not confirmed.",
        confirm: sanitizeCopy(buildBuyConfirm(pick)),
        timing:
          stage === "close" ? waitTiming("close") : timing,
      },
      ifIgnored: "If ignored: capital exposed to false breakout.",
    };
  }

  return {
    stage: "close",
    reason: {
      missing: "Breakout not confirmed.",
      confirm: sanitizeCopy(buildBuyConfirm(pick)),
      timing: waitTiming("close"),
    },
    ifIgnored: "If ignored: capital exposed to false breakout.",
  };
}

function buildBuyAction(
  symbol: string,
  deploymentPercentage: number,
  deployAmount: number,
  pick: StockPick | undefined,
  isPrimary: boolean,
): CapitalAction {
  return {
    symbol,
    action: "BUY",
    deployPercentage: deploymentPercentage,
    deployAmount,
    isPrimary,
    reason: {
      missing: sanitizeCopy("All triggers confirmed."),
      confirm: sanitizeCopy(
        deployAmount > 0
          ? `Deploy ${formatInr(deployAmount)} today.`
          : buildBuyConfirm(pick),
      ),
      timing: sanitizeCopy("Deploy today."),
    },
  };
}

function buildPostActionImpact(
  concentration: number,
  trimPct: number,
): string | undefined {
  if (concentration <= 0) {
    return undefined;
  }

  const postTrimPct = Math.max(
    0,
    Math.round(concentration * (1 - trimPct / 100)),
  );

  return `Position ${concentration}% → ${postTrimPct}% after trim`;
}

function buildHeroAccountability(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
): string {
  const action = input.action;
  const concentration = normalizePercent(input.topAllocationPct);

  if (
    isSellAction(action as DecisionActionType) ||
    action === "sell" ||
    input.intent === "protect" ||
    deploymentPercentage <= 0 ||
    concentration > 25
  ) {
    return "Reflecting current risk environment.";
  }

  return "Reflecting current market conditions.";
}

function buildPortfolioStance(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  cashPercentage: number,
  actions: CapitalAction[],
): { headline: string; detail: string } {
  const action = input.action;
  const buyCount = actions.filter((item) => item.action === "BUY").length;

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return {
      headline: "Defensive — no valid deployment",
      detail: `${cashPercentage}% capital idle — trim clears concentration.`,
    };
  }

  if (deploymentPercentage >= 50 || buyCount >= 2) {
    return {
      headline: "Active — multiple opportunities",
      detail: `${deploymentPercentage}% deploys — ${cashPercentage}% in reserve.`,
    };
  }

  if (deploymentPercentage > 0 || buyCount === 1) {
    return {
      headline: "Selective — limited deployment",
      detail: `Only ${deploymentPercentage}% clears for deployment.`,
    };
  }

  return {
    headline: "Defensive — no valid deployment",
    detail: `${cashPercentage}% capital idle — no entry confirmed.`,
  };
}

function buildPrimaryAction(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  cashPercentage: number,
  actions: CapitalAction[],
  deployAmount: number,
): { headline: string; detail: string } {
  const prioritizedSell = actions.find((item) => item.action === "SELL");

  if (prioritizedSell) {
    return {
      headline: `Trim ${prioritizedSell.symbol} by ${prioritizedSell.deployPercentage}% today`,
      detail:
        prioritizedSell.postActionImpact ??
        "Delaying trim keeps concentration risk.",
    };
  }

  const action = input.action;

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    const symbol =
      input.stock ?? actions.find((item) => item.action === "SELL")?.symbol;
    const trimPct =
      normalizePercent(input.suggested_sell_percent) ||
      actions.find((item) => item.action === "SELL")?.deployPercentage ||
      25;

    return {
      headline: symbol
        ? `Trim ${symbol} by ${trimPct}% today`
        : "Trim concentrated exposure today",
      detail: "Delaying trim keeps concentration risk.",
    };
  }

  const primaryBuy = actions.find((item) => item.action === "BUY");
  if (primaryBuy && deploymentPercentage > 0) {
    const amountLabel =
      deployAmount > 0
        ? formatInr(deployAmount)
        : `${primaryBuy.deployPercentage}% of available cash`;

    return {
      headline: `Deploy ${amountLabel} into ${primaryBuy.symbol} today`,
      detail: "Exceeding allocation adds risk.",
    };
  }

  return {
    headline: "Remain fully in cash today",
    detail: "Premature deployment increases risk.",
  };
}

function resolveExplorePipelineStage(pick: StockPick): ExplorePipelineStage {
  const score = Math.round(pick.score);

  if (score >= 70) {
    return "Close to readiness";
  }

  if (score >= 55) {
    return "Developing setup";
  }

  return "Early formation";
}

function readinessScore(pick: StockPick): number {
  const score = Math.round(pick.score);
  const { trend, momentum } = pick.signals;
  return score * 100 + trend * 10 + momentum;
}

function resolveActivationLevel(pick: StockPick): number | undefined {
  if (pick.activationLevel && pick.activationLevel > 0) {
    return Math.round(pick.activationLevel);
  }

  if (pick.price && pick.price > 0) {
    return Math.round(pick.price * 1.02);
  }

  return undefined;
}

function buildActivationCondition(pick: StockPick): string {
  const level = resolveActivationLevel(pick);

  if (level) {
    return `Break above ${formatInr(level)} on volume.`;
  }

  return "Break above range high on volume.";
}

function buildProgressiveSetupDescription(
  pick: StockPick,
  stage: ExplorePipelineStage,
): string {
  const level = resolveActivationLevel(pick);
  const price = pick.price;

  if (stage === "Close to readiness") {
    if (level && price && price > 0) {
      const gapPct = Math.max(0, Math.round(((level - price) / price) * 100));

      if (gapPct <= 3) {
        return `Structure is tightening — price is within ${gapPct}% of the ${formatInr(level)} activation level.`;
      }

      return `Structure is tightening — price is advancing toward ${formatInr(level)}.`;
    }

    return "Structure is tightening — setup is approaching activation range.";
  }

  if (stage === "Developing setup") {
    return "Setup is building — direction is emerging but confirmation is not set yet.";
  }

  return "Formation is early — structure still assembling before readiness.";
}

function exploreTimeHorizon(
  stage: ExplorePipelineStage,
): string {
  if (stage === "Close to readiness") {
    return "1–2 sessions on confirmed break.";
  }

  if (stage === "Developing setup") {
    return "2–3 sessions if structure completes.";
  }

  return "Next sessions if momentum builds.";
}

function resolveActivationGap(
  pick: StockPick,
): { gap: number; gapPct: number; level: number } | undefined {
  const level = resolveActivationLevel(pick);
  const price = pick.price;

  if (!level || !price || price <= 0 || level <= price) {
    return undefined;
  }

  return {
    gap: Math.round(level - price),
    gapPct: Math.max(1, Math.round(((level - price) / price) * 100)),
    level,
  };
}

function buildScanLine(
  pick: StockPick,
  stage: ExplorePipelineStage,
): string {
  const activationGap = resolveActivationGap(pick);
  const alignment = Math.round(pick.score);
  const { trend, momentum } = pick.signals;

  if (activationGap) {
    if (activationGap.gapPct <= 3) {
      return `${activationGap.gapPct}% below breakout level`;
    }

    return `${formatInr(activationGap.gap)} away from activation`;
  }

  if (alignment < 65) {
    return `${65 - alignment} points to Grow threshold`;
  }

  if (trend < 60) {
    return "Direction not confirmed";
  }

  if (momentum < 60) {
    return "Volume follow-through pending";
  }

  if (stage === "Early formation") {
    return "Early formation — building";
  }

  return "Breakout confirmation pending";
}

function buildProgressDelta(
  pick: StockPick,
  stage: ExplorePipelineStage,
): string {
  const activationGap = resolveActivationGap(pick);
  const alignment = Math.round(pick.score);
  const { trend, momentum } = pick.signals;

  if (activationGap) {
    return `${formatInr(activationGap.gap)} (${activationGap.gapPct}%) move to activation`;
  }

  if (alignment < 65) {
    return `+${65 - alignment} alignment move to Grow`;
  }

  if (trend < 60) {
    return "Range break move to activation";
  }

  if (momentum < 60) {
    return "Volume push move to activation";
  }

  if (stage === "Early formation") {
    return "Structure build move to activation";
  }

  return "Breakout + volume move to activation";
}

function buildProgressLine(
  pick: StockPick,
  stage: ExplorePipelineStage,
): string {
  const { trend, momentum, volume } = pick.signals;

  if (stage === "Close to readiness") {
    return "Price compressing toward activation.";
  }

  if (volume >= 65) {
    return "Volume improved vs recent average.";
  }

  if (momentum >= 55) {
    return "Momentum picking up recently.";
  }

  if (trend >= 60) {
    return "Trend holding above 50-day baseline.";
  }

  if (stage === "Developing setup") {
    return "Direction emerging — confirmation pending.";
  }

  return "Early structure forming — signals pending.";
}

function compressExploreStage(stage: ExplorePipelineStage): string {
  if (stage === "Close to readiness") {
    return "Close";
  }

  if (stage === "Developing setup") {
    return "Developing";
  }

  return "Early";
}

function compressExplorePriority(
  rank: number,
  pick: StockPick,
): string {
  if (rank === 0 || (rank <= 2 && Math.round(pick.score) >= 65)) {
    return "High";
  }

  return "Medium";
}

function buildExploreStageLine(
  stage: ExplorePipelineStage,
  rank: number,
  pick: StockPick,
): string {
  return `${compressExploreStage(stage)} · ${compressExplorePriority(rank, pick)}`;
}

function buildWhyThisMatters(
  pick: StockPick,
  rank: number,
): string | undefined {
  if (rank !== 0) {
    return undefined;
  }

  const stage = resolveExplorePipelineStage(pick);

  if (stage === "Close to readiness") {
    return "First Grow slot if activation confirms.";
  }

  return "Pipeline lead as readiness improves.";
}

function buildExplorePipelineSummary(setups: ExploreSetup[]): string | undefined {
  if (setups.length === 0) {
    return undefined;
  }

  const closeCount = setups.filter(
    (item) => item.stage === "Close to readiness",
  ).length;
  const buildingCount = setups.length - closeCount;

  return `${closeCount} almost ready · ${buildingCount} still building`;
}

function buildExploreSetup(
  pick: StockPick,
  input: CapitalDecisionInput,
  rank: number,
): ExploreSetup {
  const stage = resolveExplorePipelineStage(pick);
  let priorityMarker: ExplorePriorityMarker | undefined;

  if (rank === 0) {
    priorityMarker = "Closest to activation";
  } else if (rank <= 2 && Math.round(pick.score) >= 65) {
    priorityMarker = "High priority";
  }

  return {
    symbol: pick.stock,
    scanLine: sanitizeCopy(buildScanLine(pick, stage)),
    stageLine: buildExploreStageLine(stage, rank, pick),
    stage,
    priorityMarker,
    setupDescription: sanitizeCopy(
      buildProgressiveSetupDescription(pick, stage),
    ),
    progressDelta: sanitizeCopy(buildProgressDelta(pick, stage)),
    progressLine: sanitizeCopy(buildProgressLine(pick, stage)),
    whyThisMatters: buildWhyThisMatters(pick, rank),
    activation: sanitizeCopy(buildActivationCondition(pick)),
    timeHorizon: sanitizeCopy(exploreTimeHorizon(stage)),
    readinessScore: readinessScore(pick),
    isPrimary: pick.stock === input.stock,
  };
}

function buildExploreSetups(input: CapitalDecisionInput): ExploreSetup[] {
  const picks = [...(input.picks ?? [])].sort(
    (left, right) => readinessScore(right) - readinessScore(left),
  );

  return picks.slice(0, 5).map((pick, index) => buildExploreSetup(pick, input, index));
}

function buildExploreCapitalDecision(input: CapitalDecisionInput): CapitalDecision {
  const exploreSetups = buildExploreSetups(input);
  const capital = resolveCapitalStructure(input);

  return {
    mode: "explore",
    stance: "No Deployment",
    availableCash: capital.availableCash,
    portfolioValue: capital.portfolioValue,
    totalCapital: capital.totalCapital,
    deployAmount: 0,
    cashPercentage: 100,
    deploymentPercentage: 0,
    actions: [],
    exploreSetups,
    explorePipelineSummary: buildExplorePipelineSummary(exploreSetups),
    heroHeadline: "Watch today — your cash stays put.",
    heroSubline:
      "Track the watchlist below. Switch to Trade when a setup confirms.",
    heroAccountability: "Based on current market conditions.",
    portfolioStance: "Cash reserved — watching for entry",
    portfolioStanceDetail:
      "No money moves until price and volume confirm at your buy level.",
    primaryAction: "Check your watchlist",
    primaryActionDetail:
      "Switch to Trade when a stock hits its buy level.",
    capitalMode: "CASH",
    collateral: Math.max(0, Math.round(input.collateral ?? 0)),
    deployableCapital: capital.availableCash,
  };
}

function resolveGrowEmptyMessage(
  deploymentPercentage: number,
  actions: CapitalAction[],
): string | undefined {
  const hasBuy = actions.some((item) => item.action === "BUY");

  if (hasBuy || deploymentPercentage > 0) {
    return undefined;
  }

  if (actions.length === 0 || actions.every((item) => item.action === "WAIT")) {
    return GROW_EMPTY_MESSAGE;
  }

  return undefined;
}

function buildGrowCapitalDecision(input: CapitalDecisionInput): CapitalDecision {
  const mode: DecisionMode = input.intent === "protect" ? "protect" : "grow";
  const capital = resolveCapitalStructure(input);
  const overweight = resolveOverweightHoldings(input);
  let deploymentPercentage = resolveDeploymentPercentage(input);

  if (capital.availableCash <= 0) {
    deploymentPercentage = 0;
  }

  if (overweight.length > 0 && input.action === "buy") {
    deploymentPercentage = 0;
  }

  const deployAmount = computeDeployAmount(
    capital.availableCash,
    deploymentPercentage,
  );
  const cashPercentage = Math.max(0, 100 - deploymentPercentage);
  const stance = resolveStance(deploymentPercentage);
  const actions = buildGrowActions(
    input,
    deploymentPercentage,
    deployAmount,
    capital,
    overweight,
  );

  const portfolioStance = buildPortfolioStance(
    input,
    deploymentPercentage,
    cashPercentage,
    actions,
  );
  const primaryAction = buildPrimaryAction(
    input,
    deploymentPercentage,
    cashPercentage,
    actions,
    deployAmount,
  );

  const decision: CapitalDecision = {
    mode,
    stance,
    availableCash: capital.availableCash,
    portfolioValue: capital.portfolioValue,
    totalCapital: capital.totalCapital,
    deployAmount,
    cashPercentage,
    deploymentPercentage,
    actions,
    exploreSetups: [],
    growEmptyMessage: resolveGrowEmptyMessage(deploymentPercentage, actions),
    heroHeadline: buildHeroHeadline(
      input,
      deploymentPercentage,
      cashPercentage,
      actions,
    ),
    heroSubline: buildHeroSubline(
      input,
      stance,
      cashPercentage,
      deploymentPercentage,
      actions,
    ),
    heroDecisionCue: buildHeroDecisionCue(input, deploymentPercentage, actions),
    behaviorLock: buildBehaviorLock(input, deploymentPercentage, actions),
    heroAccountability: buildHeroAccountability(input, deploymentPercentage),
    portfolioStance: portfolioStance.headline,
    portfolioStanceDetail: portfolioStance.detail,
    primaryAction: primaryAction.headline,
    primaryActionDetail: primaryAction.detail,
    capitalMode: "CASH",
    collateral: Math.max(0, Math.round(input.collateral ?? 0)),
    deployableCapital: capital.availableCash,
  };

  validateCapitalDecision(decision);

  return decision;
}

function buildGrowActions(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  deployAmount: number,
  capital: CapitalStructure,
  overweight: CapitalHoldingWeight[],
): CapitalAction[] {
  const actions: CapitalAction[] = [];
  const actionBySymbol = new Map<string, CapitalAction>();
  const hasConcentrationRisk = overweight.length > 0;
  const canBuy = canDeployCapital(
    input,
    capital,
    overweight,
    deploymentPercentage,
  );

  const addAction = (next: CapitalAction) => {
    const existing = actionBySymbol.get(next.symbol);

    if (existing?.action === "SELL") {
      return;
    }

    if (next.action === "SELL") {
      actionBySymbol.set(next.symbol, next);
      return;
    }

    if (!existing) {
      actionBySymbol.set(next.symbol, next);
    }
  };

  for (const [index, holding] of overweight.entries()) {
    addAction(
      buildSellAction(
        holding.symbol,
        computeTrimPercentTo25(holding.weight),
        holding.weight,
        index === 0 || holding.symbol === input.stock,
      ),
    );
  }

  const action = input.action;
  const isExplicitSell =
    (isSellAction(action as DecisionActionType) || action === "sell") &&
    input.stock;

  if (
    isExplicitSell &&
    input.stock &&
    !actionBySymbol.has(input.stock) &&
    !hasConcentrationRisk
  ) {
    const sellSymbol = input.stock;
    const trimPct = normalizePercent(input.suggested_sell_percent) || 25;
    const concentration = normalizePercent(input.topAllocationPct);
    addAction(buildSellAction(sellSymbol, trimPct, concentration, true));
  }

  for (const symbol of collectSymbols(input)) {
    if (actionBySymbol.has(symbol)) {
      continue;
    }

    const pick = findPick(input, symbol);
    const isPrimary = symbol === input.stock;

    if (hasConcentrationRisk) {
      addAction(buildWaitAction(symbol, pick, input, isPrimary, true));
      continue;
    }

    if (canBuy && action === "buy" && isPrimary) {
      addAction(
        buildBuyAction(
          symbol,
          deploymentPercentage,
          deployAmount,
          pick,
          isPrimary,
        ),
      );
      continue;
    }

    addAction(buildWaitAction(symbol, pick, input, isPrimary));
  }

  for (const item of actionBySymbol.values()) {
    actions.push(item);
  }

  const actionRank: Record<CapitalActionType, number> = {
    SELL: 0,
    BUY: 1,
    WAIT: 2,
  };

  return actions.sort(
    (left, right) => actionRank[left.action] - actionRank[right.action],
  );
}

function buildSellAction(
  symbol: string,
  trimPct: number,
  concentration: number,
  isPrimary: boolean,
): CapitalAction {
  return {
    symbol,
    action: "SELL",
    deployPercentage: trimPct,
    portfolioWeight: concentration,
    isPrimary,
    postActionImpact: buildPostActionImpact(concentration, trimPct),
    reason: {
      missing: sanitizeCopy("Position above limit."),
      confirm: sanitizeCopy("Trim to 25%."),
      timing: sanitizeCopy("Act today."),
    },
    ifIgnored: sanitizeCopy("If ignored: concentration risk remains high."),
  };
}

function buildWaitAction(
  symbol: string,
  pick: StockPick | undefined,
  input: CapitalDecisionInput,
  isPrimary: boolean,
  concentrationBlocked = false,
): CapitalAction {
  const context = resolveWaitContext(pick, input, isPrimary, concentrationBlocked);

  return {
    symbol,
    action: "WAIT",
    deployPercentage: 0,
    isPrimary: isPrimary && symbol === input.stock,
    stage: context.stage,
    reason: {
      missing: sanitizeCopy(context.reason.missing),
      confirm: sanitizeCopy(context.reason.confirm),
      timing: sanitizeCopy(context.reason.timing),
    },
    ifIgnored: sanitizeCopy(context.ifIgnored),
  };
}

function collectSymbols(input: CapitalDecisionInput): string[] {
  const symbols: string[] = [];
  const seen = new Set<string>();

  const add = (symbol?: string) => {
    if (!symbol || seen.has(symbol)) {
      return;
    }

    seen.add(symbol);
    symbols.push(symbol);
  };

  add(input.stock);
  for (const pick of input.picks ?? []) {
    add(pick.stock);
  }

  return symbols.slice(0, 3);
}

/** Converts engine output into explicit capital deployment instructions. */
export function buildCapitalDecision(input: CapitalDecisionInput): CapitalDecision {
  const decision =
    input.intent === "explore" || input.action === "explore"
      ? buildExploreCapitalDecision(input)
      : buildGrowCapitalDecision(input);

  return applyMarginToDecisionLock(
    attachDecisionLock(
      attachCapitalFinalState(
        attachCapitalProjections(applyMarginPolicy(decision, input), input),
        input,
      ),
    ),
  );
}

export type TrustReinforcement = {
  confirmation: string;
  framing: string;
  nextStep: string;
  microReward: string | null;
};

export function buildTrustReinforcement(
  decision: CapitalDecision,
  seed?: string,
): TrustReinforcement {
  const hasSell = decision.actions.some((item) => item.action === "SELL");

  let framing: string;

  if (hasSell) {
    framing = "Risk reduced. Capital rebalanced.";
  } else if (decision.deploymentPercentage > 0) {
    framing = "Capital deployed under confirmation. Risk controlled.";
  } else {
    framing = "Capital remained protected. No unnecessary risk taken.";
  }

  const rewardSeed =
    seed ??
    `${new Date().toISOString().slice(0, 10)}:${decision.mode}:${decision.primaryAction}`;

  return {
    confirmation: "You followed the system today.",
    framing,
    nextStep: "Next review: after market close or on new signal.",
    microReward: getTrustMicroReward(rewardSeed),
  };
}

export function formatCapitalAction(action: CapitalAction): string {
  const lines = [action.symbol, `Action: ${action.action}`];

  if (action.action === "BUY") {
    lines.push(deployLabel(action.deployPercentage, action.deployAmount));
  }

  if (action.stage) {
    lines.push(`Stage: ${formatGrowActionStage(action.stage)}`);
  }

  lines.push(
    `Missing: ${action.reason.missing}`,
    `Confirm: ${action.reason.confirm}`,
    `Timing: ${action.reason.timing}`,
  );

  if (action.ifIgnored) {
    lines.push(action.ifIgnored);
  }

  if (action.postActionImpact) {
    lines.push(action.postActionImpact);
  }

  if (action.postAction) {
    lines.push(action.postAction.note);

    if (action.postAction.warning) {
      lines.push(action.postAction.warning);
    }
  }

  return lines.join("\n");
}

export function summarizeCapitalDecision(decision: CapitalDecision): string {
  const lead = `${decision.portfolioStance} ${decision.portfolioStanceDetail} Primary: ${decision.primaryAction} — ${decision.primaryActionDetail}`;

  if (decision.mode === "explore") {
    if (decision.exploreSetups.length === 0) {
      return `${decision.heroAccountability} ${lead}. ${EXPLORE_PIPELINE_EMPTY_HEADLINE} ${EXPLORE_PIPELINE_EMPTY_BODY}`;
    }

    const setup = decision.exploreSetups[0];
    const summary = decision.explorePipelineSummary
      ? `${decision.explorePipelineSummary}. `
      : "";

    return `${decision.heroAccountability} ${summary}${lead}. ${setup.symbol}: ${setup.stage} — ${setup.activation}`;
  }

  if (decision.growEmptyMessage && decision.actions.length === 0) {
    return `${decision.heroAccountability} ${lead}. ${decision.growEmptyMessage} ${decision.heroHeadline}`;
  }

  if (decision.actions.length === 0) {
    return `${decision.heroAccountability} ${lead}. ${decision.heroHeadline} ${decision.heroSubline}`;
  }

  const action = decision.actions[0];
  const emptyPrefix = decision.growEmptyMessage
    ? `${decision.growEmptyMessage} `
    : "";

  return `${decision.heroAccountability} ${lead}. ${emptyPrefix}${decision.heroHeadline} ${action.symbol}: ${action.action} — ${deployLabel(action.deployPercentage, action.deployAmount)}. Missing: ${action.reason.missing}`;
}

function runCapitalDecisionSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Capital self-check failed: ${message}`);
    }
  };

  const noCashBuy = buildCapitalDecision({
    intent: "grow",
    action: "buy",
    stock: "RELIANCE",
    availableCash: 0,
    portfolioValue: 500_000,
    entryTiming: { enter: true },
  });

  assert(
    !noCashBuy.actions.some((item) => item.action === "BUY"),
    "BUY must be blocked when cash is zero",
  );
  assert(noCashBuy.deployAmount === 0, "Deploy amount must be zero without cash");

  const concentratedBuy = buildCapitalDecision({
    intent: "grow",
    action: "buy",
    stock: "RELIANCE",
    availableCash: 100_000,
    portfolioValue: 400_000,
    topAllocationPct: 42,
    entryTiming: { enter: true },
  });

  assert(
    !concentratedBuy.actions.some((item) => item.action === "BUY"),
    "BUY must be blocked during concentration risk",
  );
  assert(
    concentratedBuy.actions.some((item) => item.action === "SELL"),
    "Concentration must force SELL before BUY",
  );
  assert(
    concentratedBuy.primaryAction.includes("Trim"),
    "Primary action must surface trim when concentration SELL exists",
  );
  assert(
    !concentratedBuy.primaryAction.includes("Remain fully in cash"),
    "Primary action must not say cash-only when trim is required",
  );

  const trimBeforeWait = buildCapitalDecision({
    intent: "grow",
    action: "wait",
    stock: "JIOFIN",
    availableCash: 9_631,
    portfolioValue: 257,
    topAllocationPct: 100,
    entryTiming: { enter: false },
  });

  assert(
    trimBeforeWait.actions.some((item) => item.action === "SELL"),
    "Concentrated wait must still include trim action",
  );
  assert(
    trimBeforeWait.primaryAction.includes("JIOFIN"),
    "Wait + concentration must name the trim symbol in primary action",
  );

  const validBuy = buildCapitalDecision({
    intent: "grow",
    action: "buy",
    stock: "INFY",
    availableCash: 50_000,
    portfolioValue: 200_000,
    topAllocationPct: 18,
    allocationPercent: 20,
    entryTiming: { enter: true },
  });

  assert(validBuy.deployAmount === 10_000, "Deploy amount must use cash only");
  assert(
    validBuy.actions.some(
      (item) => item.action === "BUY" && item.deployAmount === 10_000,
    ),
    "BUY must include ₹ deploy amount",
  );

  validateCapitalDecision(validBuy);
}

if (process.env.APEX_CAPITAL_SELF_CHECK === "1") {
  runCapitalDecisionSelfCheck();
}
