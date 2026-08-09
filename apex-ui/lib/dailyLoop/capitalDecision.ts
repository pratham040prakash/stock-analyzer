import type { StockPick } from "@/types/decision";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { UserIntent } from "@/types/intent";

export type DeploymentStance =
  | "No Deployment"
  | "Partial Deployment"
  | "Active Deployment";

export type CapitalActionType = "BUY" | "WAIT" | "SELL";

export type CapitalAction = {
  symbol: string;
  action: CapitalActionType;
  allocation: number;
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
    return `${cashPercentage}% capital stays in cash.`;
  }

  return `Deploy ${deploymentPercentage}% of capital today.`;
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
      return "Deploying here puts capital at work without a deployment mandate.";
    }

    if (action === "buy" && input.entryTiming?.enter === false) {
      return "Deploying now increases risk without entry confirmation.";
    }

    return "Deploying now increases risk without confirmation.";
  }

  if (stance === "Partial Deployment") {
    return `${cashPercentage}% stays in cash — exceeding ${deploymentPercentage}% adds uncompensated risk.`;
  }

  return `${deploymentPercentage}% is deployed — ${cashPercentage}% remains in reserve.`;
}

function waitReasonForPick(
  pick: StockPick | undefined,
  input: CapitalDecisionInput,
  isPrimary: boolean,
): string {
  if (input.intent === "explore") {
    return "Capital allocation locked at 0% — observe mode only.";
  }

  if (isPrimary && input.action === "buy" && input.entryTiming?.enter === false) {
    return "Entry trigger not confirmed — wait for breakout validation.";
  }

  if (input.intent === "protect" && isPrimary) {
    return "Protection rule active — no new capital until the book rebalances.";
  }

  if (!pick) {
    return isPrimary
      ? "Primary trigger not confirmed — allocation stays at 0%."
      : "Not confirmed for deployment — allocation stays at 0%.";
  }

  const alignment = Math.round(pick.score);
  const { trend, momentum } = pick.signals;

  if (alignment < 65) {
    return "Structure incomplete — alignment below deployment threshold.";
  }

  if (trend < 60) {
    return "Direction not confirmed — trend needs validation.";
  }

  if (momentum < 60) {
    return "Momentum needs validation before capital moves.";
  }

  return "Not confirmed for deployment today.";
}

function buyReason(pick: StockPick | undefined): string {
  if (pick && Math.round(pick.score) >= 75) {
    return "Entry confirmed — structure validated for deployment.";
  }

  return "Entry confirmed — deploy only the allocated sleeve.";
}

function sellReason(
  trimPct: number,
  concentration: number,
): string {
  if (concentration > 25) {
    return `Position at ${concentration}% — trim ${trimPct}% to rebalance the book.`;
  }

  return `Trim ${trimPct}% — concentration limit requires reduction.`;
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

    return {
      symbol,
      action: "SELL",
      allocation: trimPct,
      reason: sanitizeCopy(sellReason(trimPct, concentration)),
    };
  }

  if (action === "buy" && isPrimary && deploymentPercentage > 0) {
    return {
      symbol,
      action: "BUY",
      allocation: deploymentPercentage,
      reason: sanitizeCopy(buyReason(pick)),
    };
  }

  return {
    symbol,
    action: "WAIT",
    allocation: 0,
    reason: sanitizeCopy(waitReasonForPick(pick, input, isPrimary)),
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

  const heroHeadline = buildHeroHeadline(
    input,
    deploymentPercentage,
    cashPercentage,
  );
  const heroSubline = buildHeroSubline(
    input,
    stance,
    cashPercentage,
    deploymentPercentage,
  );

  return {
    stance,
    cashPercentage,
    deploymentPercentage,
    actions,
    heroHeadline,
    heroSubline,
  };
}

export function formatCapitalAction(action: CapitalAction): string {
  return `${action.symbol}\nAction: ${action.action}\nAllocation: ${action.allocation}%\nReason: ${action.reason}`;
}

export function summarizeCapitalDecision(decision: CapitalDecision): string {
  if (decision.actions.length === 0) {
    return `${decision.heroHeadline} ${decision.heroSubline}`;
  }

  const lead = decision.actions[0];
  return `${decision.heroHeadline} ${lead.symbol}: ${lead.action} at ${lead.allocation}%. ${lead.reason}`;
}
