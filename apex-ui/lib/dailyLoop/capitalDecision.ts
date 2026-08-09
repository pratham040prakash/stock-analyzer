import type { StockPick } from "@/types/decision";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import { formatInr } from "@/lib/funds";

export type DeploymentStance =
  | "No Deployment"
  | "Partial Deployment"
  | "Active Deployment";

export type CapitalActionType = "BUY" | "WAIT" | "SELL";

export type WaitStage = "Close to trigger" | "Developing" | "Early stage";

export type CapitalAction = {
  symbol: string;
  action: CapitalActionType;
  allocation: number;
  deployLabel: string;
  stage?: WaitStage;
  missing?: string;
  confirm?: string;
  timing?: string;
  ifIgnored?: string;
  postActionImpact?: string;
  isPrimary?: boolean;
  reason: string;
};

export type DecisionMode = "grow" | "explore" | "protect";

export type ExplorePipelineStage =
  | "Close to readiness"
  | "Developing setup"
  | "Early formation";

export type ExplorePriorityMarker = "Closest to activation" | "High priority";

export type ExploreSetup = {
  symbol: string;
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

function deployLabel(allocation: number): string {
  return `Deploy ${allocation}% of your capital`;
}

function resolveWaitStage(pick: StockPick | undefined): WaitStage {
  if (!pick) {
    return "Early stage";
  }

  const score = Math.round(pick.score);

  if (score >= 70) {
    return "Close to trigger";
  }

  if (score >= 55) {
    return "Developing";
  }

  return "Early stage";
}

function waitTiming(stage: WaitStage): string {
  if (stage === "Close to trigger") {
    return "If confirmation clears, act within next 1–2 sessions — delay adds entry risk.";
  }

  if (stage === "Developing") {
    return "Reassess within next 2–3 sessions — hold capital until structure completes.";
  }

  return "Hold over next sessions — setup still forming, no capital move yet.";
}

function composeReason(parts: {
  missing: string;
  confirm: string;
  timing?: string;
}): string {
  const lines = [`Missing: ${parts.missing}`, `Confirm: ${parts.confirm}`];

  if (parts.timing) {
    lines.push(`Timing: ${parts.timing}`);
  }

  return sanitizeCopy(lines.join(" "));
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
      ? `Trim ${trimPct}% of ${input.stock} to protect your capital.`
      : "Trim exposure to protect your capital.";
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
    return "Delaying the trim keeps concentration risk on your capital.";
  }

  if (stance === "No Deployment") {
    if (action === "buy" && input.entryTiming?.enter === false) {
      return "Deploying now increases risk to your capital without entry confirmation.";
    }

    return "Deploying now increases risk to your capital without confirmation.";
  }

  if (stance === "Partial Deployment") {
    return `${cashPercentage}% of your capital stays in cash — exceeding ${deploymentPercentage}% adds uncompensated risk.`;
  }

  return `${deploymentPercentage}% of your capital is deployed — ${cashPercentage}% remains in reserve.`;
}

type WaitContext = {
  stage: WaitStage;
  missing: string;
  confirm: string;
  timing: string;
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
      stage: "Close to trigger",
      missing: "Breakout above resistance not confirmed.",
      confirm: "Buy only on breakout above resistance with volume.",
      timing:
        "If breakout confirms, deploy within next 1–2 sessions — acting early risks a false break.",
      ifIgnored:
        "If ignored: capital enters before confirmation and risks a false breakout.",
    };
  }

  if (input.intent === "protect" && isPrimary) {
    return {
      stage,
      missing: "Book concentration must clear before new capital moves.",
      confirm: "Buy only after the trim rebalance completes.",
      timing,
      ifIgnored:
        "If ignored: new capital adds to an unbalanced book before the trim completes.",
    };
  }

  if (!pick) {
    return {
      stage: "Early stage",
      missing: "Primary trigger not confirmed for your capital.",
      confirm: "Buy only when APEX confirms the lead symbol.",
      timing: "Hold over next sessions — lead symbol not yet confirmed for deployment.",
      ifIgnored:
        "If ignored: capital moves before the lead symbol confirms and faces avoidable risk.",
    };
  }

  const alignment = Math.round(pick.score);
  const { trend, momentum } = pick.signals;

  if (alignment < 65) {
    return {
      stage,
      missing: "Structure incomplete — below deployment threshold.",
      confirm: "Buy when alignment crosses threshold on a confirmed close.",
      timing,
      ifIgnored:
        "If ignored: capital deploys below threshold and faces avoidable drawdown.",
    };
  }

  if (trend < 60) {
    return {
      stage,
      missing: "Direction not confirmed — price below prior range.",
      confirm: "Buy only when trend validates above the recent range.",
      timing,
      ifIgnored:
        "If ignored: capital buys into a range before direction is confirmed.",
    };
  }

  if (momentum < 60) {
    return {
      stage,
      missing: "Momentum not confirmed — follow-through absent.",
      confirm: "Buy when momentum confirms on volume over next sessions.",
      timing:
        stage === "Close to trigger"
          ? "If volume follows through, act within next 1–2 sessions — otherwise wait."
          : timing,
      ifIgnored:
        "If ignored: capital chases price without volume follow-through.",
    };
  }

  return {
    stage: "Close to trigger",
    missing: "Final confirmation bar not cleared yet.",
    confirm: "Buy only on breakout above resistance.",
    timing:
      "If resistance breaks on volume, deploy within next 1–2 sessions — patience until then.",
    ifIgnored:
      "If ignored: capital enters before the break confirms and takes entry risk.",
  };
}

function buildBuyAction(
  symbol: string,
  deploymentPercentage: number,
  pick: StockPick | undefined,
  isPrimary: boolean,
): CapitalAction {
  const confirmed =
    pick && Math.round(pick.score) >= 75
      ? "Structure validated — entry trigger confirmed."
      : "Entry trigger confirmed — deploy only the allocated sleeve.";

  return {
    symbol,
    action: "BUY",
    allocation: deploymentPercentage,
    deployLabel: deployLabel(deploymentPercentage),
    isPrimary,
    confirm: sanitizeCopy(confirmed),
    timing: "Deploy today within the allocated limit.",
    reason: composeReason({
      missing: "No blockers — capital is cleared to deploy.",
      confirm: confirmed,
      timing: "Deploy today within the allocated limit.",
    }),
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

  return `Position at ${concentration}% → trim ${trimPct}% → post-trim ${postTrimPct}%`;
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

  return "Based on current market conditions.";
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
      headline: "Defensive — protecting concentrated exposure",
      detail: `${cashPercentage}% of your capital stays elsewhere until the rebalance clears concentration risk.`,
    };
  }

  if (deploymentPercentage >= 50 || buyCount >= 2) {
    return {
      headline: "Active — multiple aligned opportunities",
      detail: `${deploymentPercentage}% of your capital may deploy today — ${cashPercentage}% held in reserve as buffer.`,
    };
  }

  if (deploymentPercentage > 0 || buyCount === 1) {
    return {
      headline: "Selective — limited confirmed setups",
      detail: `Only ${deploymentPercentage}% of your capital clears for deployment; ${cashPercentage}% remains idle until more confirms.`,
    };
  }

  return {
    headline: "Defensive — no valid deployment",
    detail: `${cashPercentage}% of your capital remains idle — no entry trigger confirmed today.`,
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
      detail:
        "Delaying the trim leaves single-name concentration on your capital.",
    };
  }

  const primaryBuy = actions.find((item) => item.action === "BUY");
  if (primaryBuy && deploymentPercentage > 0) {
    return {
      headline: `Deploy ${primaryBuy.allocation}% into ${primaryBuy.symbol}`,
      detail: `${cashPercentage}% stays in cash — exceeding the allocated sleeve adds uncompensated risk.`,
    };
  }

  if (action === "buy" && input.entryTiming?.enter === false) {
    return {
      headline: "Remain in cash",
      detail:
        "Entry is not confirmed — deploying now risks capital on an unvalidated break.",
    };
  }

  return {
    headline: "Remain in cash",
    detail:
      "Premature deployment increases risk to your capital without confirmation.",
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
    return `Breakout above ${formatInr(level)} with volume confirms entry.`;
  }

  return "Breakout above the recent range high with volume confirms entry.";
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
  pick: StockPick,
): string {
  const level = resolveActivationLevel(pick);
  const levelRef = level ? formatInr(level) : "the activation level";

  if (stage === "Close to readiness") {
    return `If ${levelRef} breaks on volume, activation within 1–2 sessions — without confirmation, stays in pipeline.`;
  }

  if (stage === "Developing setup") {
    return "If structure completes, moves to readiness in 2–3 sessions — without follow-through, timeline extends.";
  }

  return "If trend builds, reassess over next sessions — without momentum, remains early formation.";
}

function buildProgressDelta(
  pick: StockPick,
  stage: ExplorePipelineStage,
): string {
  const level = resolveActivationLevel(pick);
  const price = pick.price;
  const alignment = Math.round(pick.score);
  const { trend, momentum } = pick.signals;

  if (
    stage === "Close to readiness" &&
    level &&
    price &&
    price > 0 &&
    level > price
  ) {
    const gap = Math.round(level - price);
    const gapPct = Math.max(1, Math.round(((level - price) / price) * 100));

    return `Needs +${formatInr(gap)} (${gapPct}%) to clear ${formatInr(level)} on volume.`;
  }

  if (alignment < 65) {
    const gap = 65 - alignment;
    return `Needs +${gap} alignment points to reach Grow threshold (at ${alignment} now).`;
  }

  if (trend < 60) {
    if (level) {
      return `Needs sustained close above ${formatInr(level)} to confirm direction.`;
    }

    return "Needs a closing hold above the recent range high.";
  }

  if (momentum < 60) {
    return "Needs volume expansion above the 20-day average on the next push.";
  }

  if (level && price && level > price) {
    const gap = Math.round(level - price);
    return `Needs +${formatInr(gap)} breakout close above ${formatInr(level)} with volume.`;
  }

  return "Needs confirmed breakout with volume before Grow can activate.";
}

function buildProgressLine(
  pick: StockPick,
  stage: ExplorePipelineStage,
): string {
  const alignment = Math.round(pick.score);
  const { trend, momentum, volume } = pick.signals;
  const lines: string[] = [];

  if (stage === "Close to readiness") {
    lines.push("Price compressed toward the activation range.");
  }

  if (trend >= 60) {
    lines.push("Trend held above the 50-day baseline recently.");
  }

  if (momentum >= 80) {
    lines.push("Momentum is holding at elevated levels.");
  } else if (momentum >= 55) {
    lines.push("Momentum has picked up over recent sessions.");
  }

  if (volume >= 65) {
    lines.push("Volume participation improved vs the recent average.");
  }

  if (alignment >= 55 && stage === "Developing setup") {
    lines.push("Alignment moved into the development band.");
  }

  if (lines.length === 0) {
    return "Base structure is forming — early signal improvement pending.";
  }

  return lines.slice(0, 2).join(" ");
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
    return "Leads the pipeline — first slot for Grow capital if activation confirms.";
  }

  return "Top-ranked in today's scan — moves to front of line as readiness improves.";
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
    stage,
    priorityMarker,
    setupDescription: sanitizeCopy(
      buildProgressiveSetupDescription(pick, stage),
    ),
    progressDelta: sanitizeCopy(buildProgressDelta(pick, stage)),
    progressLine: sanitizeCopy(buildProgressLine(pick, stage)),
    whyThisMatters: buildWhyThisMatters(pick, rank),
    activation: sanitizeCopy(buildActivationCondition(pick)),
    timeHorizon: sanitizeCopy(exploreTimeHorizon(stage, pick)),
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
      ? `Position at ${concentration}% — above single-name limit.`
      : "Concentration limit requires a reduction.";
  const ifIgnored =
    concentration > 25
      ? `If ignored: ${symbol} stays at ${concentration}% — concentration risk remains on your capital.`
      : `If ignored: the rebalance is delayed and book risk persists on your capital.`;

  return {
    symbol,
    action: "SELL",
    allocation: trimPct,
    deployLabel: deployLabel(0),
    isPrimary,
    postActionImpact: buildPostActionImpact(concentration, trimPct),
    missing: sanitizeCopy(missing),
    confirm: sanitizeCopy(`Trim ${trimPct}% of ${symbol} to rebalance your capital.`),
    timing: "Act this session.",
    ifIgnored: sanitizeCopy(ifIgnored),
    reason: composeReason({
      missing,
      confirm: `Trim ${trimPct}% of ${symbol} to rebalance your capital.`,
      timing: "Act this session.",
    }),
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
    allocation: 0,
    deployLabel: deployLabel(0),
    isPrimary: isPrimary && symbol === input.stock,
    stage: context.stage,
    missing: sanitizeCopy(context.missing),
    confirm: sanitizeCopy(context.confirm),
    timing: sanitizeCopy(context.timing),
    ifIgnored: sanitizeCopy(context.ifIgnored),
    reason: composeReason(context),
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
    return buildBuyAction(symbol, deploymentPercentage, pick, isPrimary);
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
  const lines = [
    action.symbol,
    `Action: ${action.action}`,
    action.deployLabel,
  ];

  if (action.stage) {
    lines.push(`Stage: ${action.stage}`);
  }

  lines.push(`Reason: ${action.reason}`);

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

  return `${decision.heroAccountability} ${lead}. ${emptyPrefix}${decision.heroHeadline} ${action.symbol}: ${action.action} — ${action.deployLabel}. ${action.reason}`;
}
