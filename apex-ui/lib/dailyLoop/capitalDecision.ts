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

function normalizePercent(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) {
    return 0;
  }

  return value <= 1 ? Math.round(value * 100) : Math.round(value);
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

function buildHeroHeadline(
  input: CapitalDecisionInput,
  deploymentPercentage: number,
  stance: DeploymentStance,
): string {
  const action = input.action;

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return input.stock
      ? `Reduce ${input.stock} today.`
      : "Reduce exposure today.";
  }

  if (stance === "No Deployment") {
    if (input.intent === "explore") {
      return "No deployment today. Observe only.";
    }

    return "No deployment today. Stay in cash.";
  }

  return `Deploy ${deploymentPercentage}% capital today.`;
}

function buildHeroSubline(
  stance: DeploymentStance,
  cashPercentage: number,
  deploymentPercentage: number,
): string {
  return `${cashPercentage}% cash · ${stance}`;
}

function waitReason(intent: UserIntent, isPrimary: boolean): string {
  if (inputIntentIsProtect(intent) && isPrimary) {
    return "Capital stays protected.";
  }

  return "Not enough edge yet.";
}

function inputIntentIsProtect(intent: UserIntent): boolean {
  return intent === "protect";
}

function resolveActionForSymbol(
  symbol: string,
  input: CapitalDecisionInput,
  deploymentPercentage: number,
): CapitalAction {
  const action = input.action;
  const isPrimary = symbol === input.stock;

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
      reason:
        concentration > 25
          ? "Concentration is too high."
          : "Protect capital first.",
    };
  }

  if (action === "buy" && isPrimary && deploymentPercentage > 0) {
    return {
      symbol,
      action: "BUY",
      allocation: deploymentPercentage,
      reason: "Clear enough to deploy.",
    };
  }

  if (action === "buy" && isPrimary) {
    return {
      symbol,
      action: "WAIT",
      allocation: 0,
      reason: "Wait for entry confirmation.",
    };
  }

  if (input.intent === "explore") {
    return {
      symbol,
      action: "WAIT",
      allocation: 0,
      reason: "Observation only. No capital.",
    };
  }

  return {
    symbol,
    action: "WAIT",
    allocation: 0,
    reason: waitReason(input.intent, isPrimary),
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

  return {
    stance,
    cashPercentage,
    deploymentPercentage,
    actions,
    heroHeadline: buildHeroHeadline(input, deploymentPercentage, stance),
    heroSubline: buildHeroSubline(stance, cashPercentage, deploymentPercentage),
  };
}

export function formatCapitalAction(action: CapitalAction): string {
  return `${action.symbol}\nAction: ${action.action}\nAllocation: ${action.allocation}%\n${action.reason}`;
}

export function summarizeCapitalDecision(decision: CapitalDecision): string {
  if (decision.actions.length === 0) {
    return `${decision.heroHeadline} ${decision.heroSubline}.`;
  }

  const lead = decision.actions[0];
  return `${decision.heroHeadline} ${lead.symbol}: ${lead.action}, ${lead.allocation}% — ${lead.reason}`;
}
