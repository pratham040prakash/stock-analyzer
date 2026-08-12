import type { ConnectionStatus } from "@/lib/broker/zerodha";

export type StaleAutoRetryTrigger = "mount" | "focus" | "pull";

export const STALE_AUTO_RETRY_COOLDOWN_MS = 60_000;

export function shouldAttemptStaleAutoRetry(input: {
  enabled: boolean;
  connectionStatus: ConnectionStatus;
  portfolioStale: boolean;
  trigger: StaleAutoRetryTrigger;
  mountAttempted: boolean;
  lastAttemptAt: number | null;
  now?: number;
}): boolean {
  if (!input.enabled || !input.portfolioStale) {
    return false;
  }

  if (input.connectionStatus !== "CONNECTED") {
    return false;
  }

  if (input.trigger === "mount") {
    return !input.mountAttempted;
  }

  if (input.trigger === "pull") {
    return true;
  }

  if (input.lastAttemptAt === null) {
    return true;
  }

  const now = input.now ?? Date.now();
  return now - input.lastAttemptAt >= STALE_AUTO_RETRY_COOLDOWN_MS;
}

export function runTodaySyncAutoRetrySelfCheck(): void {
  const base = {
    enabled: true,
    connectionStatus: "CONNECTED" as const,
    portfolioStale: true,
    mountAttempted: false,
    lastAttemptAt: null,
  };

  if (!shouldAttemptStaleAutoRetry({ ...base, trigger: "mount" })) {
    throw new Error("Today sync auto-retry self-check failed: mount");
  }

  if (
    shouldAttemptStaleAutoRetry({
      ...base,
      trigger: "mount",
      mountAttempted: true,
    })
  ) {
    throw new Error("Today sync auto-retry self-check failed: mount duplicate");
  }

  if (
    shouldAttemptStaleAutoRetry({
      ...base,
      trigger: "focus",
      lastAttemptAt: Date.now() - 1_000,
      now: Date.now(),
    })
  ) {
    throw new Error("Today sync auto-retry self-check failed: focus cooldown");
  }

  if (
    !shouldAttemptStaleAutoRetry({
      ...base,
      trigger: "focus",
      lastAttemptAt: Date.now() - STALE_AUTO_RETRY_COOLDOWN_MS - 1,
      now: Date.now(),
    })
  ) {
    throw new Error("Today sync auto-retry self-check failed: focus retry");
  }

  if (
    shouldAttemptStaleAutoRetry({
      enabled: true,
      connectionStatus: "TOKEN_EXPIRED",
      portfolioStale: true,
      trigger: "pull",
      mountAttempted: false,
      lastAttemptAt: null,
    })
  ) {
    throw new Error("Today sync auto-retry self-check failed: expired pull");
  }
}
