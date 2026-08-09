import { formatInr } from "@/lib/funds";
import type {
  CapitalAction,
  CapitalDecision,
  CapitalDecisionInput,
  CapitalStructure,
} from "@/lib/dailyLoop/capitalDecision";

const CONCENTRATION_LIMIT = 25;

export type CapitalFinalPosition = {
  symbol: string;
  weight: number;
};

export type CapitalFinalState = {
  cash: number;
  finalPortfolioValue: number;
  maxWeight: number;
  largestPosition: CapitalFinalPosition | null;
  risk: "Concentration risk remains" | "No concentration risk";
  positions: CapitalFinalPosition[];
};

type MutableHolding = {
  value: number;
};

function normalizePercent(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) {
    return 0;
  }

  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

function clonePortfolio(
  input: CapitalDecisionInput,
  capital: CapitalStructure,
): Map<string, MutableHolding> {
  const portfolio = new Map<string, MutableHolding>();

  if (capital.portfolioValue <= 0) {
    return portfolio;
  }

  if (input.holdings?.length) {
    for (const holding of input.holdings) {
      portfolio.set(holding.symbol, {
        value: Math.round((holding.weight / 100) * capital.portfolioValue),
      });
    }

    return portfolio;
  }

  const topWeight = normalizePercent(input.topAllocationPct);

  if (input.stock && topWeight > 0) {
    portfolio.set(input.stock, {
      value: Math.round((topWeight / 100) * capital.portfolioValue),
    });
  }

  return portfolio;
}

function orderExecutableActions(actions: CapitalAction[]): CapitalAction[] {
  return [
    ...actions.filter((action) => action.action === "SELL"),
    ...actions.filter((action) => action.action === "BUY"),
  ];
}

function applySellAction(
  action: CapitalAction,
  cash: number,
  portfolio: Map<string, MutableHolding>,
): number {
  const holding = portfolio.get(action.symbol) ?? { value: 0 };
  const sellAmount = Math.round((action.deployPercentage / 100) * holding.value);
  const nextValue = Math.max(0, holding.value - sellAmount);

  if (nextValue <= 0) {
    portfolio.delete(action.symbol);
  } else {
    portfolio.set(action.symbol, { value: nextValue });
  }

  return cash + sellAmount;
}

function applyBuyAction(
  action: CapitalAction,
  cash: number,
  portfolio: Map<string, MutableHolding>,
): number {
  const deployAmount = Math.max(0, action.deployAmount ?? 0);
  const holding = portfolio.get(action.symbol) ?? { value: 0 };

  portfolio.set(action.symbol, {
    value: holding.value + deployAmount,
  });

  return Math.max(0, cash - deployAmount);
}

export function simulateCombinedFinalState(
  decision: CapitalDecision,
  input: CapitalDecisionInput,
): CapitalFinalState {
  const capital: CapitalStructure = {
    availableCash: decision.availableCash,
    portfolioValue: decision.portfolioValue,
    totalCapital: decision.totalCapital,
  };
  const portfolio = clonePortfolio(input, capital);
  let cash = capital.availableCash;

  for (const action of orderExecutableActions(decision.actions)) {
    if (action.action === "SELL") {
      cash = applySellAction(action, cash, portfolio);
      continue;
    }

    if (action.action === "BUY") {
      cash = applyBuyAction(action, cash, portfolio);
    }
  }

  const finalPortfolioValue = [...portfolio.values()].reduce(
    (sum, holding) => sum + holding.value,
    0,
  );
  const totalCapital = cash + finalPortfolioValue;

  const positions = [...portfolio.entries()]
    .filter(([, holding]) => holding.value > 0)
    .map(([symbol, holding]) => ({
      symbol,
      weight:
        totalCapital > 0 ? (holding.value / totalCapital) * 100 : 0,
    }))
    .sort((left, right) => right.weight - left.weight);

  const largestPosition = positions[0] ?? null;
  const maxWeight = largestPosition?.weight ?? 0;

  return {
    cash,
    finalPortfolioValue,
    maxWeight,
    largestPosition,
    risk:
      maxWeight > CONCENTRATION_LIMIT
        ? "Concentration risk remains"
        : "No concentration risk",
    positions,
  };
}

export function formatFinalStateSummary(state: CapitalFinalState): string[] {
  const largestLine = state.largestPosition
    ? `Largest position ${Math.round(state.largestPosition.weight)}%`
    : "Largest position 0%";

  return [
    "After execution:",
    `${formatInr(state.cash)} cash`,
    largestLine,
    state.risk,
    `${state.positions.length} positions active`,
  ];
}

/** Simulates portfolio state after all actions execute together. */
export function attachCapitalFinalState(
  decision: CapitalDecision,
  input: CapitalDecisionInput,
): CapitalDecision {
  if (decision.mode === "explore") {
    return decision;
  }

  const finalState = simulateCombinedFinalState(decision, input);

  return {
    ...decision,
    finalState,
  };
}

export function runCapitalFinalStateSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Capital final-state self-check failed: ${message}`);
    }
  };

  const finalState = simulateCombinedFinalState(
    {
      mode: "grow",
      stance: "Partial Deployment",
      availableCash: 100_000,
      portfolioValue: 400_000,
      totalCapital: 500_000,
      deployAmount: 10_000,
      cashPercentage: 80,
      deploymentPercentage: 10,
      capitalMode: "CASH",
      collateral: 0,
      deployableCapital: 100_000,
      actions: [
        {
          symbol: "RELIANCE",
          action: "SELL",
          deployPercentage: 25,
          portfolioWeight: 32,
          reason: { missing: "", confirm: "", timing: "" },
        },
        {
          symbol: "INFY",
          action: "BUY",
          deployPercentage: 10,
          deployAmount: 10_000,
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
    },
    {
      intent: "grow",
      action: "buy",
      stock: "INFY",
      availableCash: 100_000,
      portfolioValue: 400_000,
      holdings: [{ symbol: "RELIANCE", weight: 32 }],
    },
  );

  assert(finalState.cash === 122_000, "Combined simulation must apply SELL before BUY");
  assert(
    finalState.positions.some((item) => item.symbol === "INFY"),
    "Combined simulation must include new BUY position",
  );
  assert(
    formatFinalStateSummary(finalState)[0] === "After execution:",
    "Final state summary must start with After execution",
  );
}
