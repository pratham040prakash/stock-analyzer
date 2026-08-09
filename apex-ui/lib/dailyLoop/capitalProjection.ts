import { formatInr } from "@/lib/funds";
import type {
  CapitalAction,
  CapitalActionProjection,
  CapitalDecision,
  CapitalDecisionInput,
  CapitalStructure,
} from "@/lib/dailyLoop/capitalDecision";

const CONCENTRATION_LIMIT = 25;

type HoldingSnapshot = {
  value: number;
  weight: number;
};

function normalizePercent(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) {
    return 0;
  }

  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

function resolveHoldingSnapshots(
  input: CapitalDecisionInput,
  capital: CapitalStructure,
): Map<string, HoldingSnapshot> {
  const snapshots = new Map<string, HoldingSnapshot>();

  if (capital.portfolioValue <= 0) {
    return snapshots;
  }

  if (input.holdings?.length) {
    for (const holding of input.holdings) {
      snapshots.set(holding.symbol, {
        weight: holding.weight,
        value: Math.round((holding.weight / 100) * capital.portfolioValue),
      });
    }

    return snapshots;
  }

  const topWeight = normalizePercent(input.topAllocationPct);

  if (input.stock && topWeight > 0) {
    snapshots.set(input.stock, {
      weight: topWeight,
      value: Math.round((topWeight / 100) * capital.portfolioValue),
    });
  }

  return snapshots;
}

function projectBuyAction(
  action: CapitalAction,
  cash: number,
  totalCapital: number,
  holding: HoldingSnapshot,
): CapitalActionProjection {
  const deployAmount = Math.max(0, action.deployAmount ?? 0);
  const cashAfter = Math.max(0, cash - deployAmount);
  const newHoldingValue = holding.value + deployAmount;
  const weightAfter =
    totalCapital > 0 ? (newHoldingValue / totalCapital) * 100 : 0;

  const note = `After: ${formatInr(cashAfter)} cash · ${action.symbol} ${Math.round(weightAfter)}%`;

  return {
    cashAfter,
    weightAfter,
    note,
    warning:
      weightAfter > CONCENTRATION_LIMIT
        ? "Warning: creates concentration risk"
        : undefined,
  };
}

function projectSellAction(
  action: CapitalAction,
  cash: number,
  totalCapital: number,
  holding: HoldingSnapshot,
): CapitalActionProjection {
  const weightBefore =
    action.portfolioWeight !== undefined
      ? action.portfolioWeight
      : holding.weight;
  const sellAmount = Math.round((action.deployPercentage / 100) * holding.value);
  const newHoldingValue = Math.max(0, holding.value - sellAmount);
  const cashAfter = cash + sellAmount;
  const weightAfter =
    totalCapital > 0 ? (newHoldingValue / totalCapital) * 100 : 0;

  return {
    cashAfter,
    weightAfter,
    note: `After: ${action.symbol} ${Math.round(weightBefore)}% → ${Math.round(weightAfter)}%`,
  };
}

function projectWaitAction(
  cash: number,
  holding: HoldingSnapshot,
): CapitalActionProjection {
  return {
    cashAfter: cash,
    weightAfter: holding.weight,
    note: "Capital unchanged",
  };
}

function projectAction(
  action: CapitalAction,
  cash: number,
  totalCapital: number,
  holdings: Map<string, HoldingSnapshot>,
): CapitalActionProjection {
  const holding = holdings.get(action.symbol) ?? { value: 0, weight: 0 };

  if (action.action === "BUY") {
    return projectBuyAction(action, cash, totalCapital, holding);
  }

  if (action.action === "SELL") {
    return projectSellAction(action, cash, totalCapital, holding);
  }

  return projectWaitAction(cash, holding);
}

/** Simulates post-action capital state without changing decision logic. */
export function attachCapitalProjections(
  decision: CapitalDecision,
  input: CapitalDecisionInput,
): CapitalDecision {
  if (decision.actions.length === 0) {
    return decision;
  }

  const capital: CapitalStructure = {
    availableCash: decision.availableCash,
    portfolioValue: decision.portfolioValue,
    totalCapital: decision.totalCapital,
  };
  const holdings = resolveHoldingSnapshots(input, capital);

  return {
    ...decision,
    actions: decision.actions.map((action) => ({
      ...action,
      postAction: projectAction(
        action,
        capital.availableCash,
        capital.totalCapital,
        holdings,
      ),
    })),
  };
}

export function runCapitalProjectionSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Capital projection self-check failed: ${message}`);
    }
  };

  const buyProjection = projectAction(
    {
      symbol: "HINDALCO",
      action: "BUY",
      deployPercentage: 20,
      deployAmount: 20_000,
      reason: { missing: "", confirm: "", timing: "" },
    },
    100_000,
    500_000,
    new Map([["HINDALCO", { value: 40_000, weight: 8 }]]),
  );

  assert(buyProjection.cashAfter === 80_000, "BUY must reduce cash");
  assert(
    buyProjection.note.includes("80,000"),
    "BUY note must show projected cash",
  );

  const sellProjection = projectAction(
    {
      symbol: "RELIANCE",
      action: "SELL",
      deployPercentage: 25,
      portfolioWeight: 32,
      reason: { missing: "", confirm: "", timing: "" },
    },
    50_000,
    500_000,
    new Map([["RELIANCE", { value: 160_000, weight: 32 }]]),
  );

  assert(
    sellProjection.note.includes("32%") && sellProjection.note.includes("→"),
    "SELL note must show weight transition",
  );

  const waitProjection = projectAction(
    {
      symbol: "INFY",
      action: "WAIT",
      deployPercentage: 0,
      reason: { missing: "", confirm: "", timing: "" },
    },
    50_000,
    500_000,
    new Map([["INFY", { value: 50_000, weight: 10 }]]),
  );

  assert(waitProjection.note === "Capital unchanged", "WAIT must leave capital unchanged");
}
