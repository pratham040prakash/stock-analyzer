import {
  applyBearModeAmount,
  BEAR_MODE_SIZE_FACTOR,
} from "@/services/risk/riskControl";
import type { MarketTrend } from "@/types/decision";

export type RegimeConditioning = {
  amount: number;
  lockExecution: boolean;
  reason: string | null;
};

/**
 * Producer-only regime gate. May shrink size or lock execution.
 * Never selects a symbol and never belongs on the client.
 */
export function applyRegimeConditioning(
  amount: number,
  marketTrend?: MarketTrend,
): RegimeConditioning {
  const sized = applyBearModeAmount(amount, marketTrend);
  if (marketTrend === "bearish" && sized <= 0) {
    return {
      amount: 0,
      lockExecution: true,
      reason: "Bear regime locked new size",
    };
  }

  return {
    amount: sized,
    lockExecution: false,
    reason:
      marketTrend === "bearish"
        ? `Bear mode — ${Math.round(BEAR_MODE_SIZE_FACTOR * 100)}% size`
        : null,
  };
}

export function runRegimeConditioningSelfCheck(): void {
  const bear = applyRegimeConditioning(10_000, "bearish");
  if (bear.amount !== 5_000 || bear.lockExecution) {
    throw new Error("Regime conditioning self-check failed: bearish must halve size");
  }

  const locked = applyRegimeConditioning(0, "bearish");
  if (!locked.lockExecution || locked.amount !== 0) {
    throw new Error("Regime conditioning self-check failed: zero bear size must lock");
  }

  const sideways = applyRegimeConditioning(8_000, "sideways");
  if (sideways.amount !== 8_000 || sideways.reason !== null) {
    throw new Error("Regime conditioning self-check failed: sideways must keep size");
  }

  if ("symbol" in bear) {
    throw new Error("Regime conditioning self-check failed: must not hunt a symbol");
  }
}
