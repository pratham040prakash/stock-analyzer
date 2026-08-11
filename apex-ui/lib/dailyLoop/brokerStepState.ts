import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";

const STORAGE_PREFIX = "apex_broker_step_done";
const COMPLETED_VALUE = "1";
const SKIPPED_VALUE = "skip";

function buildKey(symbol: string, dateKey = tradingDateKey()): string {
  return `${STORAGE_PREFIX}:${dateKey}:${symbol.trim().toUpperCase()}`;
}

export type BrokerStepOutcome = "completed" | "skipped" | null;

export function readBrokerStepOutcome(
  symbol: string | undefined,
  dateKey = tradingDateKey(),
): BrokerStepOutcome {
  if (!symbol || typeof window === "undefined") {
    return null;
  }

  const value = window.sessionStorage.getItem(buildKey(symbol, dateKey));

  if (value === COMPLETED_VALUE) {
    return "completed";
  }

  if (value === SKIPPED_VALUE) {
    return "skipped";
  }

  return null;
}

export function readBrokerStepCompleted(
  symbol: string | undefined,
  dateKey = tradingDateKey(),
): boolean {
  return readBrokerStepOutcome(symbol, dateKey) === "completed";
}

export function readBrokerStepSkipped(
  symbol: string | undefined,
  dateKey = tradingDateKey(),
): boolean {
  return readBrokerStepOutcome(symbol, dateKey) === "skipped";
}

export function markBrokerStepCompleted(
  symbol: string,
  dateKey = tradingDateKey(),
): void {
  if (typeof window === "undefined" || !symbol.trim()) {
    return;
  }

  window.sessionStorage.setItem(buildKey(symbol, dateKey), COMPLETED_VALUE);
}

export function markBrokerStepSkipped(
  symbol: string,
  dateKey = tradingDateKey(),
): void {
  if (typeof window === "undefined" || !symbol.trim()) {
    return;
  }

  window.sessionStorage.setItem(buildKey(symbol, dateKey), SKIPPED_VALUE);
}

export function runBrokerStepStateSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Broker step state self-check failed: ${message}`);
    }
  };

  const store = new Map<string, string>();
  const originalWindow = globalThis.window;

  Object.defineProperty(globalThis, "window", {
    configurable: true,
    writable: true,
    value: {
      sessionStorage: {
        getItem: (key: string) => store.get(key) ?? null,
        setItem: (key: string, value: string) => {
          store.set(key, value);
        },
      },
    },
  });

  try {
    const dateKey = "2026-08-09";
    const key = buildKey("JIOFIN", dateKey);

    assert(key === "apex_broker_step_done:2026-08-09:JIOFIN", "Key must be date-scoped");
    assert(readBrokerStepCompleted(undefined, dateKey) === false, "Missing symbol is false");
    assert(readBrokerStepOutcome("JIOFIN", dateKey) === null, "Missing entry is null");

    markBrokerStepSkipped("JIOFIN", dateKey);
    assert(readBrokerStepSkipped("JIOFIN", dateKey) === true, "Skip must persist");
    assert(readBrokerStepCompleted("JIOFIN", dateKey) === false, "Skip is not completed");

    markBrokerStepCompleted("JIOFIN", dateKey);
    assert(readBrokerStepOutcome("JIOFIN", dateKey) === "completed", "Complete overrides skip");
  } finally {
    if (originalWindow === undefined) {
      // @ts-expect-error - restore Node test environment
      delete globalThis.window;
    } else {
      globalThis.window = originalWindow;
    }
  }
}
