import type { StockPick } from "@/types/decision";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import { formatInr } from "@/lib/funds";

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

export type CapitalAction = {
  symbol: string;
  action: CapitalActionType;
  deployPercentage: number;
  stage?: GrowActionStage;
  reason: CapitalActionReason;
  ifIgnored?: string;
  postActionImpact?: string;
  isPrimary?: boolean;
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

export type CapitalDecision = {
  mode: DecisionMode;
  stance: DeploymentStance;
  cashPercentage: number;
  deploymentPercentage: number;
  actions: CapitalAction[];
  exploreSetups: ExploreSetup[];
  explorePipelineSummary?: string;
  growEmptyMessage?: string;
  heroHeadline: string;
  heroSubline: string;
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
  entryTiming?: { enter?: boolean };
  confidence?: number;
};

const FORBIDDEN_COPY = /\b(good setup|bad setup|strong|weak|not enough edge)\b/i;
const GROW_EMPTY_MESSAGE = "No setup meets deployment criteria today.";

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

function deployLabel(deployPercentage: number): string {
  return `Deploy ${deployPercentage}% of your capital`;
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
    return "Act within 1–2 sessions if confirmed.";
  }

  if (stage === "developing") {
    return "Reassess in 2–3 sessions.";
  }

  return "Hold — setup still forming.";
}

function buildHeroHeadline(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  cashPercentage: number,
): string {
  const action = input.action;

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    const trimPct = normalizePercent(input.suggested_sell_percent) || 25;
    return input.stock
      ? `Trim ${trimPct}% of ${input.stock}.`
      : "Trim exposure to protect capital.";
  }

  if (deploymentPercentage <= 0) {
    return `${cashPercentage}% of your capital stays in cash.`;
  }

  return `Deploy ${deploymentPercentage}% of your capital today.`;
}

function buildHeroSubline(
  input: CapitalDecisionInput,
  stance: DeploymentStance,
  cashPercentage: number,
  deploymentPercentage: number,
): string {
  const action = input.action;

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
): WaitContext {
  const stage = resolveWaitStage(pick);
  const timing = waitTiming(stage);

  if (isPrimary && input.action === "buy" && input.entryTiming?.enter === false) {
    return {
      stage: "close",
      reason: {
        missing: "Breakout above resistance not confirmed.",
        confirm: "Buy on breakout above resistance with volume.",
        timing: "Deploy within 1–2 sessions if confirmed.",
      },
      ifIgnored: "If ignored: capital enters before confirmation.",
    };
  }

  if (input.intent === "protect" && isPrimary) {
    return {
      stage,
      reason: {
        missing: "Concentration must clear before new capital.",
        confirm: "Buy only after trim rebalance completes.",
        timing,
      },
      ifIgnored: "If ignored: capital adds to unbalanced book.",
    };
  }

  if (!pick) {
    return {
      stage: "early",
      reason: {
        missing: "Primary trigger not confirmed yet.",
        confirm: "Buy when APEX confirms lead symbol.",
        timing: "Hold until lead symbol confirms.",
      },
      ifIgnored: "If ignored: capital moves before confirmation.",
    };
  }

  const alignment = Math.round(pick.score);
  const { trend, momentum } = pick.signals;

  if (alignment < 65) {
    return {
      stage,
      reason: {
        missing: "Structure below deployment threshold.",
        confirm: "Buy when alignment crosses threshold.",
        timing,
      },
      ifIgnored: "If ignored: capital deploys below threshold.",
    };
  }

  if (trend < 60) {
    return {
      stage,
      reason: {
        missing: "Direction not confirmed — below range.",
        confirm: "Buy when trend validates above range.",
        timing,
      },
      ifIgnored: "If ignored: capital buys before direction confirms.",
    };
  }

  if (momentum < 60) {
    return {
      stage,
      reason: {
        missing: "Momentum not confirmed — no follow-through.",
        confirm: "Buy when momentum confirms on volume.",
        timing:
          stage === "close"
            ? "Act within 1–2 sessions if volume follows."
            : timing,
      },
      ifIgnored: "If ignored: capital chases without volume.",
    };
  }

  return {
    stage: "close",
    reason: {
      missing: "Final confirmation bar not cleared.",
      confirm: "Buy on breakout above resistance.",
      timing: "Deploy within 1–2 sessions if break confirms.",
    },
    ifIgnored: "If ignored: capital enters before break confirms.",
  };
}

function buildBuyAction(
  symbol: string,
  deploymentPercentage: number,
  isPrimary: boolean,
): CapitalAction {
  return {
    symbol,
    action: "BUY",
    deployPercentage: deploymentPercentage,
    isPrimary,
    reason: {
      missing: sanitizeCopy("No blockers — cleared to deploy."),
      confirm: sanitizeCopy("Deploy on confirmed entry trigger."),
      timing: sanitizeCopy("Deploy today within allocated limit."),
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
      detail: `${deploymentPercentage}% may deploy — ${cashPercentage}% in reserve.`,
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
): { headline: string; detail: string } {
  const action = input.action;

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    const symbol =
      input.stock ?? actions.find((item) => item.action === "SELL")?.symbol;

    return {
      headline: symbol ? `Trim ${symbol} exposure` : "Trim concentrated exposure",
      detail: "Delaying trim keeps concentration risk.",
    };
  }

  const primaryBuy = actions.find((item) => item.action === "BUY");
  if (primaryBuy && deploymentPercentage > 0) {
    return {
      headline: `Deploy ${primaryBuy.deployPercentage}% into ${primaryBuy.symbol}`,
      detail: "Exceeding allocation adds risk.",
    };
  }

  return {
    headline: "Remain in cash",
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
  const closeLabel = closeCount === 1 ? "setup" : "setups";

  return `${closeCount} ${closeLabel} close to activation · ${buildingCount} building`;
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

  return {
    mode: "explore",
    stance: "No Deployment",
    cashPercentage: 100,
    deploymentPercentage: 0,
    actions: [],
    exploreSetups,
    explorePipelineSummary: buildExplorePipelineSummary(exploreSetups),
    heroHeadline: "Opportunity pipeline — capital stays in reserve.",
    heroSubline:
      "Track setups as they progress toward activation — switch to Grow to deploy.",
    heroAccountability: "Based on current market conditions.",
    portfolioStance: "Observational — pipeline under review",
    portfolioStanceDetail:
      "Setups are ranked by readiness — capital deploys only after activation in Grow.",
    primaryAction: "Monitor the pipeline",
    primaryActionDetail:
      "Move to Grow when a setup confirms at its activation level.",
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
  const deploymentPercentage = resolveDeploymentPercentage(input);
  const cashPercentage = Math.max(0, 100 - deploymentPercentage);
  const stance = resolveStance(deploymentPercentage);
  const symbols = collectSymbols(input);

  const actions =
    symbols.length > 0
      ? symbols.map((symbol) =>
          resolveActionForSymbol(symbol, input, deploymentPercentage),
        )
      : [];

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
  );

  return {
    mode,
    stance,
    cashPercentage,
    deploymentPercentage,
    actions,
    exploreSetups: [],
    growEmptyMessage: resolveGrowEmptyMessage(deploymentPercentage, actions),
    heroHeadline: buildHeroHeadline(input, deploymentPercentage, cashPercentage),
    heroSubline: buildHeroSubline(
      input,
      stance,
      cashPercentage,
      deploymentPercentage,
    ),
    heroAccountability: buildHeroAccountability(input, deploymentPercentage),
    portfolioStance: portfolioStance.headline,
    portfolioStanceDetail: portfolioStance.detail,
    primaryAction: primaryAction.headline,
    primaryActionDetail: primaryAction.detail,
  };
}

function buildSellAction(
  symbol: string,
  trimPct: number,
  concentration: number,
  isPrimary: boolean,
): CapitalAction {
  const missing =
    concentration > 25
      ? `Position at ${concentration}% — above limit.`
      : "Concentration limit requires reduction.";
  const ifIgnored =
    concentration > 25
      ? "If ignored: concentration risk remains."
      : "If ignored: rebalance delay keeps book risk.";

  return {
    symbol,
    action: "SELL",
    deployPercentage: trimPct,
    isPrimary,
    postActionImpact: buildPostActionImpact(concentration, trimPct),
    reason: {
      missing: sanitizeCopy(missing),
      confirm: sanitizeCopy(`Trim ${trimPct}% of ${symbol} to rebalance.`),
      timing: sanitizeCopy("Act this session."),
    },
    ifIgnored: sanitizeCopy(ifIgnored),
  };
}

function buildWaitAction(
  symbol: string,
  pick: StockPick | undefined,
  input: CapitalDecisionInput,
  isPrimary: boolean,
): CapitalAction {
  const context = resolveWaitContext(pick, input, isPrimary);

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

function resolveActionForSymbol(
  symbol: string,
  input: CapitalDecisionInput,
  deploymentPercentage: number,
): CapitalAction {
  const action = input.action;
  const isPrimary = symbol === input.stock;
  const pick = findPick(input, symbol);

  if (
    (isSellAction(action as DecisionActionType) || action === "sell") &&
    isPrimary
  ) {
    const trimPct = normalizePercent(input.suggested_sell_percent) || 25;
    const concentration = normalizePercent(input.topAllocationPct);
    return buildSellAction(symbol, trimPct, concentration, isPrimary);
  }

  if (action === "buy" && isPrimary && deploymentPercentage > 0) {
    return buildBuyAction(symbol, deploymentPercentage, isPrimary);
  }

  return buildWaitAction(symbol, pick, input, isPrimary);
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
  if (input.intent === "explore" || input.action === "explore") {
    return buildExploreCapitalDecision(input);
  }

  return buildGrowCapitalDecision(input);
}

export function formatCapitalAction(action: CapitalAction): string {
  const lines = [action.symbol, `Action: ${action.action}`];

  if (action.action === "BUY") {
    lines.push(deployLabel(action.deployPercentage));
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

  return `${decision.heroAccountability} ${lead}. ${emptyPrefix}${decision.heroHeadline} ${action.symbol}: ${action.action} — ${deployLabel(action.deployPercentage)}. Missing: ${action.reason.missing}`;
}
