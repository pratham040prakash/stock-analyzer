import type {
  CapitalAction,
  CapitalDecision,
  CapitalDecisionInput,
  CapitalHoldingWeight,
} from "@/lib/dailyLoop/capitalDecision";

export type CapitalFundingMode = "CASH" | "MARGIN";

export const MARGIN_MAX_DEPLOYMENT_PCT = 30;
export const MARGIN_MAX_SINGLE_STOCK_PCT = 15;
export const MARGIN_MIN_CASH_COLLATERAL_RATIO = 0.5;
export const MARGIN_LEVERAGE_WARNING = "Using leverage increases risk.";
export const MARGIN_DECISION_LOCK_NOTE =
  "This uses leveraged capital. Follow limits strictly.";

const CAPITAL_MODE_STORAGE_KEY = "apex_capital_mode";

export function readStoredCapitalMode(): CapitalFundingMode {
  if (typeof window === "undefined") {
    return "CASH";
  }

  try {
    return localStorage.getItem(CAPITAL_MODE_STORAGE_KEY) === "MARGIN"
      ? "MARGIN"
      : "CASH";
  } catch {
    return "CASH";
  }
}

export function writeStoredCapitalMode(mode: CapitalFundingMode): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(CAPITAL_MODE_STORAGE_KEY, mode);
  } catch {
    // Ignore storage failures — engine defaults to CASH on next read.
  }
}

function normalizePercent(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) {
    return 0;
  }

  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

function resolveHoldingValue(
  symbol: string,
  input: CapitalDecisionInput,
  portfolioValue: number,
): number {
  const holding = input.holdings?.find((item) => item.symbol === symbol);

  if (holding && portfolioValue > 0) {
    return Math.round((holding.weight / 100) * portfolioValue);
  }

  if (input.stock === symbol) {
    const weight = normalizePercent(input.topAllocationPct);
    return Math.round((weight / 100) * portfolioValue);
  }

  return 0;
}

function projectedBuyWeight(
  symbol: string,
  deployAmount: number,
  input: CapitalDecisionInput,
  decision: CapitalDecision,
): number {
  const holdingValue = resolveHoldingValue(
    symbol,
    input,
    decision.portfolioValue,
  );
  const totalCapital = decision.totalCapital;

  if (totalCapital <= 0) {
    return 0;
  }

  return ((holdingValue + deployAmount) / totalCapital) * 100;
}

function marginRulesViolated(
  decision: CapitalDecision,
  input: CapitalDecisionInput,
  collateral: number,
  deployAmount: number,
): boolean {
  const ledgerCash = Math.max(
    0,
    Math.round(input.ledgerCash ?? decision.availableCash ?? 0),
  );

  if (ledgerCash < collateral * MARGIN_MIN_CASH_COLLATERAL_RATIO) {
    return true;
  }

  if (decision.deploymentPercentage > MARGIN_MAX_DEPLOYMENT_PCT) {
    return true;
  }

  const buyActions = decision.actions.filter((action) => action.action === "BUY");

  for (const action of buyActions) {
    const amount = action.deployAmount ?? deployAmount;

    if (
      projectedBuyWeight(action.symbol, amount, input, decision) >
      MARGIN_MAX_SINGLE_STOCK_PCT
    ) {
      return true;
    }
  }

  return false;
}

function stripMarginDeployment(decision: CapitalDecision): CapitalDecision {
  return {
    ...decision,
    deploymentPercentage: 0,
    deployAmount: 0,
    cashPercentage: 100,
    stance: "No Deployment",
    actions: decision.actions.map((action) =>
      action.action === "BUY"
        ? {
            ...action,
            action: "WAIT" as const,
            deployPercentage: 0,
            deployAmount: 0,
            reason: {
              missing: "Margin limits not met.",
              confirm: "Do not deploy until limits clear.",
              timing: "Reassess after risk improves.",
            },
          }
        : action,
    ),
    growEmptyMessage: decision.growEmptyMessage ?? "No capital deployment allowed today.",
    marginBlocked: true,
  };
}

function applyMarginDeployment(
  decision: CapitalDecision,
  deployableCapital: number,
): CapitalDecision {
  if (decision.deploymentPercentage <= 0) {
    return {
      ...decision,
      deployAmount: 0,
    };
  }

  const deployAmount = Math.round(
    (decision.deploymentPercentage / 100) * deployableCapital,
  );

  return {
    ...decision,
    deployAmount,
    actions: decision.actions.map((action) =>
      action.action === "BUY"
        ? {
            ...action,
            deployAmount,
          }
        : action,
    ),
  };
}

/** Applies margin deployment rules without changing underlying cash logic. */
export function applyMarginPolicy(
  decision: CapitalDecision,
  input: CapitalDecisionInput,
): CapitalDecision {
  const capitalMode: CapitalFundingMode = input.capitalMode ?? "CASH";
  const collateral = Math.max(0, Math.round(input.collateral ?? 0));
  const ledgerCash = Math.max(
    0,
    Math.round(input.ledgerCash ?? decision.availableCash ?? 0),
  );

  if (decision.mode === "explore" || capitalMode === "CASH") {
    return {
      ...decision,
      capitalMode: "CASH",
      collateral,
      deployableCapital: decision.availableCash,
    };
  }

  const deployableCapital = ledgerCash + collateral;
  const base: CapitalDecision = {
    ...decision,
    capitalMode: "MARGIN",
    collateral,
    deployableCapital,
    marginWarning: MARGIN_LEVERAGE_WARNING,
  };

  if (collateral <= 0) {
    return stripMarginDeployment({
      ...base,
      marginBlocked: true,
    });
  }

  const tentative = applyMarginDeployment(base, deployableCapital);

  if (marginRulesViolated(tentative, input, collateral, tentative.deployAmount)) {
    return stripMarginDeployment(base);
  }

  return {
    ...tentative,
    marginBlocked: false,
  };
}

export function applyMarginToDecisionLock(
  decision: CapitalDecision,
): CapitalDecision {
  if (decision.capitalMode !== "MARGIN" || !decision.decisionLock) {
    return decision;
  }

  return {
    ...decision,
    decisionLock: {
      ...decision.decisionLock,
      messageSecondary: `${decision.decisionLock.messageSecondary} ${MARGIN_DECISION_LOCK_NOTE}`,
    },
  };
}

export function runCapitalMarginSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Capital margin self-check failed: ${message}`);
    }
  };

  const baseDecision: CapitalDecision = {
    mode: "grow",
    stance: "Partial Deployment",
    availableCash: 100_000,
    portfolioValue: 400_000,
    totalCapital: 500_000,
    deployAmount: 20_000,
    cashPercentage: 80,
    deploymentPercentage: 20,
    actions: [
      {
        symbol: "INFY",
        action: "BUY",
        deployPercentage: 20,
        deployAmount: 20_000,
        reason: { missing: "", confirm: "", timing: "" },
      },
    ],
    exploreSetups: [],
    heroHeadline: "",
    heroSubline: "",
    heroAccountability: "",
    portfolioStance: "",
    portfolioStanceDetail: "",
    primaryAction: "",
    primaryActionDetail: "",
    capitalMode: "CASH",
    collateral: 0,
    deployableCapital: 100_000,
  };

  const cashResult = applyMarginPolicy(
    baseDecision,
    {
      intent: "grow",
      action: "buy",
      availableCash: 100_000,
      portfolioValue: 400_000,
      capitalMode: "CASH",
      collateral: 50_000,
    },
  );

  assert(cashResult.capitalMode === "CASH", "Default mode must remain CASH");
  assert(
    cashResult.deployAmount === 20_000,
    "Cash mode must preserve cash deployment amounts",
  );

  const marginResult = applyMarginPolicy(baseDecision, {
    intent: "grow",
    action: "buy",
    availableCash: 100_000,
    portfolioValue: 400_000,
    collateral: 100_000,
    capitalMode: "MARGIN",
    holdings: [{ symbol: "INFY", weight: 5 }],
  });

  assert(marginResult.capitalMode === "MARGIN", "Margin mode must be set");
  assert(
    marginResult.deployAmount === 40_000,
    "Margin deploy amount must use cash plus collateral",
  );
  assert(
    marginResult.marginWarning === MARGIN_LEVERAGE_WARNING,
    "Margin mode must expose leverage warning",
  );

  const blocked = applyMarginPolicy(
    {
      ...baseDecision,
      deploymentPercentage: 35,
      deployAmount: 35_000,
    },
    {
      intent: "grow",
      action: "buy",
      availableCash: 100_000,
      portfolioValue: 400_000,
      collateral: 100_000,
      capitalMode: "MARGIN",
    },
  );

  assert(blocked.marginBlocked === true, "Margin rule violations must block deployment");
  assert(
    !blocked.actions.some((action) => action.action === "BUY"),
    "Blocked margin deployment must remove BUY actions",
  );
}
