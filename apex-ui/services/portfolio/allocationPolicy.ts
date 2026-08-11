import type { PortfolioHoldingRow } from "@/types/portfolioApi";

export type AllocationBucket = "core" | "tactical" | "cash";

export type AllocationPolicyTarget = {
  core: number;
  tactical: number;
  cash: number;
};

export type HoldingAllocationRow = PortfolioHoldingRow & {
  bucket: AllocationBucket;
  policy_target_pct: number;
  drift_pct: number;
};

export type AllocationPolicySummary = {
  targets: AllocationPolicyTarget;
  actual: AllocationPolicyTarget;
  drift: AllocationPolicyTarget;
  holdings: HoldingAllocationRow[];
  cash_available_inr: number | null;
  policy_note: string;
};

const DEFAULT_TARGETS: AllocationPolicyTarget = {
  core: 60,
  tactical: 30,
  cash: 10,
};

export function resolveAllocationTargets(
  topAllocationPct?: number,
): AllocationPolicyTarget {
  if (topAllocationPct !== undefined && topAllocationPct > 70) {
    return { core: 50, tactical: 35, cash: 15 };
  }

  return DEFAULT_TARGETS;
}

export function classifyBucket(
  holding: PortfolioHoldingRow,
  topSymbol?: string,
): AllocationBucket {
  if (
    topSymbol &&
    holding.tradingsymbol.trim().toUpperCase() === topSymbol.trim().toUpperCase() &&
    holding.allocation_pct >= 40
  ) {
    return "core";
  }

  if (holding.allocation_pct >= 15) {
    return "core";
  }

  return "tactical";
}

export function isSacredCoreSymbol(input: {
  symbol: string;
  holdings: PortfolioHoldingRow[];
  topSymbol?: string;
}): boolean {
  const normalized = input.symbol.trim().toUpperCase();
  const holding = input.holdings.find(
    (row) => row.tradingsymbol.trim().toUpperCase() === normalized,
  );

  if (!holding) {
    return false;
  }

  return classifyBucket(holding, input.topSymbol) === "core";
}

export function buildAllocationPolicySummary(input: {
  holdings: PortfolioHoldingRow[];
  cashAvailableInr?: number | null;
  totalValue?: number | null;
  topSymbol?: string;
  topAllocationPct?: number;
}): AllocationPolicySummary {
  const targets = resolveAllocationTargets(input.topAllocationPct);
  const totalValue = Math.max(0, input.totalValue ?? 0);
  const cashInr = Math.max(0, input.cashAvailableInr ?? 0);
  const investedValue = input.holdings.reduce((sum, row) => sum + row.value, 0);
  const portfolioTotal = totalValue > 0 ? totalValue + cashInr : investedValue + cashInr;

  const actual: AllocationPolicyTarget = { core: 0, tactical: 0, cash: 0 };

  const holdings: HoldingAllocationRow[] = input.holdings.map((holding) => {
    const bucket = classifyBucket(holding, input.topSymbol);
    const weight =
      portfolioTotal > 0 ? (holding.value / portfolioTotal) * 100 : holding.allocation_pct;

    actual[bucket] += weight;

    return {
      ...holding,
      bucket,
      policy_target_pct: targets[bucket],
      drift_pct: Math.round((weight - targets[bucket] / Math.max(input.holdings.filter((h) => classifyBucket(h, input.topSymbol) === bucket).length, 1)) * 10) / 10,
    };
  });

  if (portfolioTotal > 0) {
    actual.cash = (cashInr / portfolioTotal) * 100;
  } else if (cashInr > 0) {
    actual.cash = 100;
  }

  const drift: AllocationPolicyTarget = {
    core: Math.round((actual.core - targets.core) * 10) / 10,
    tactical: Math.round((actual.tactical - targets.tactical) * 10) / 10,
    cash: Math.round((actual.cash - targets.cash) * 10) / 10,
  };

  const overweightCore = drift.core > 5;
  const lowCash = drift.cash < -5;

  let policy_note = "Allocation is within policy bands.";
  if (overweightCore && lowCash) {
    policy_note = "Core concentration is high and cash is below target.";
  } else if (overweightCore) {
    policy_note = "Core bucket is above policy — consider trimming before new buys.";
  } else if (lowCash) {
    policy_note = "Cash buffer is below target.";
  }

  return {
    targets,
    actual: {
      core: Math.round(actual.core * 10) / 10,
      tactical: Math.round(actual.tactical * 10) / 10,
      cash: Math.round(actual.cash * 10) / 10,
    },
    drift,
    holdings,
    cash_available_inr: input.cashAvailableInr ?? null,
    policy_note,
  };
}

export function runAllocationPolicySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Allocation policy self-check failed: ${message}`);
    }
  };

  const summary = buildAllocationPolicySummary({
    holdings: [
      {
        tradingsymbol: "RELIANCE",
        quantity: 10,
        average_price: 100,
        last_price: 110,
        pnl: 100,
        value: 1100,
        allocation_pct: 70,
      },
      {
        tradingsymbol: "TCS",
        quantity: 5,
        average_price: 200,
        last_price: 210,
        pnl: 50,
        value: 1050,
        allocation_pct: 10,
      },
    ],
    cashAvailableInr: 200,
    totalValue: 2150,
    topSymbol: "RELIANCE",
    topAllocationPct: 70,
  });

  assert(summary.holdings.length === 2, "Must map all holdings");
  assert(summary.targets.core > 0, "Targets must be populated");
  assert(summary.policy_note.length > 0, "Policy note required");

  assert(
    isSacredCoreSymbol({
      symbol: "RELIANCE",
      holdings: summary.holdings,
      topSymbol: "RELIANCE",
    }),
    "Large top holding must classify as sacred core",
  );

  assert(
    !isSacredCoreSymbol({
      symbol: "TCS",
      holdings: summary.holdings,
      topSymbol: "RELIANCE",
    }),
    "Small tactical holding must not block Today buys",
  );
}
