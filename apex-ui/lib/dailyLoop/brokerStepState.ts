import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";

const STORAGE_PREFIX = "apex_broker_step_done";

function buildKey(symbol: string, dateKey = tradingDateKey()): string {
  return `${STORAGE_PREFIX}:${dateKey}:${symbol.trim().toUpperCase()}`;
}

export function readBrokerStepCompleted(
  symbol: string | undefined,
  dateKey = tradingDateKey(),
): boolean {
  if (!symbol || typeof window === "undefined") {
    return false;
  }

  return window.sessionStorage.getItem(buildKey(symbol, dateKey)) === "1";
}

export function markBrokerStepCompleted(
  symbol: string,
  dateKey = tradingDateKey(),
): void {
  if (typeof window === "undefined" || !symbol.trim()) {
    return;
  }

  window.sessionStorage.setItem(buildKey(symbol, dateKey), "1");
}

export function runBrokerStepStateSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Broker step state self-check failed: ${message}`);
    }
  };

  const dateKey = "2026-08-09";
  const key = buildKey("JIOFIN", dateKey);

  assert(key === "apex_broker_step_done:2026-08-09:JIOFIN", "Key must be date-scoped");
  assert(readBrokerStepCompleted(undefined, dateKey) === false, "Missing symbol is false");
}
