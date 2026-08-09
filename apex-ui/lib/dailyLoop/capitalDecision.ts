import type { StockPick } from "@/types/decision";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { UserIntent } from "@/types/intent";

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
  reason: string;
};

export type CapitalDecision = {
  stance: DeploymentStance;
  cashPercentage: number;
  deploymentPercentage: number;
  actions: CapitalAction[];
  heroHeadline: string;
  heroSubline: string;
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
    return "within next 1–2 sessions";
  }

  if (stage === "Developing") {
    return "within next 2–3 sessions";
  }

  return "over next sessions";
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
    if (input.intent === "explore") {
      return "Deploying here puts your capital at work without a deployment mandate.";
    }

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
};

function resolveWaitContext(
  pick: StockPick | undefined,
  input: CapitalDecisionInput,
  isPrimary: boolean,
): WaitContext {
  const stage = resolveWaitStage(pick);
  const timing = waitTiming(stage);

  if (input.intent === "explore") {
    return {
      stage,
      missing: "No deployment mandate — capital stays idle.",
      confirm: "Capital moves only on an explicit grow or protect decision.",
      timing: "over next sessions",
    };
  }

  if (isPrimary && input.action === "buy" && input.entryTiming?.enter === false) {
    return {
      stage: "Close to trigger",
      missing: "Breakout above resistance not confirmed.",
      confirm: "Buy only on breakout above resistance with volume.",
      timing: "within next 1–2 sessions",
    };
  }

  if (input.intent === "protect" && isPrimary) {
    return {
      stage,
      missing: "Book concentration must clear before new capital moves.",
      confirm: "Buy only after the trim rebalance completes.",
      timing,
    };
  }

  if (!pick) {
    return {
      stage: "Early stage",
      missing: "Primary trigger not confirmed for your capital.",
      confirm: "Buy only when APEX confirms the lead symbol.",
      timing: "over next sessions",
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
    };
  }

  if (trend < 60) {
    return {
      stage,
      missing: "Direction not confirmed — price below prior range.",
      confirm: "Buy only when trend validates above the recent range.",
      timing,
    };
  }

  if (momentum < 60) {
    return {
      stage,
      missing: "Momentum not confirmed — follow-through absent.",
      confirm: "Buy when momentum confirms on volume over next sessions.",
      timing,
    };
  }

  return {
    stage: "Close to trigger",
    missing: "Final confirmation bar not cleared yet.",
    confirm: "Buy only on breakout above resistance.",
    timing: "within next 1–2 sessions",
  };
}

function buildBuyAction(
  symbol: string,
  deploymentPercentage: number,
  pick: StockPick | undefined,
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
    confirm: sanitizeCopy(confirmed),
    timing: "Deploy today within the allocated limit.",
    reason: composeReason({
      missing: "No blockers — capital is cleared to deploy.",
      confirm: confirmed,
      timing: "Deploy today within the allocated limit.",
    }),
  };
}

function buildSellAction(
  symbol: string,
  trimPct: number,
  concentration: number,
): CapitalAction {
  const missing =
    concentration > 25
      ? `Position at ${concentration}% — above single-name limit.`
      : "Concentration limit requires a reduction.";

  return {
    symbol,
    action: "SELL",
    allocation: trimPct,
    deployLabel: deployLabel(0),
    missing: sanitizeCopy(missing),
    confirm: sanitizeCopy(`Trim ${trimPct}% of ${symbol} to rebalance your capital.`),
    timing: "Act this session.",
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
    stage: context.stage,
    missing: sanitizeCopy(context.missing),
    confirm: sanitizeCopy(context.confirm),
    timing: sanitizeCopy(context.timing),
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
    return buildSellAction(symbol, trimPct, concentration);
  }

  if (action === "buy" && isPrimary && deploymentPercentage > 0) {
    return buildBuyAction(symbol, deploymentPercentage, pick);
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

  return {
    stance,
    cashPercentage,
    deploymentPercentage,
    actions,
    heroHeadline: buildHeroHeadline(input, deploymentPercentage, cashPercentage),
    heroSubline: buildHeroSubline(
      input,
      stance,
      cashPercentage,
      deploymentPercentage,
    ),
  };
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
  return lines.join("\n");
}

export function summarizeCapitalDecision(decision: CapitalDecision): string {
  if (decision.actions.length === 0) {
    return `${decision.heroHeadline} ${decision.heroSubline}`;
  }

  const lead = decision.actions[0];
  return `${decision.heroHeadline} ${lead.symbol}: ${lead.action} — ${lead.deployLabel}. ${lead.reason}`;
}
