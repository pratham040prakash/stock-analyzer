import type { ConnectionStatus } from "@/lib/broker/zerodha";

export function shouldAttemptStaleAutoRetry(input: {
  enabled: boolean;
  connectionStatus: ConnectionStatus;
  portfolioStale: boolean;
  alreadyAttempted: boolean;
}): boolean {
  if (!input.enabled || !input.portfolioStale || input.alreadyAttempted) {
    return false;
  }

  return input.connectionStatus === "CONNECTED";
}

export function runTodaySyncAutoRetrySelfCheck(): void {
  if (
    !shouldAttemptStaleAutoRetry({
      enabled: true,
      connectionStatus: "CONNECTED",
      portfolioStale: true,
      alreadyAttempted: false,
    })
  ) {
    throw new Error("Today sync auto-retry self-check failed: connected stale");
  }

  if (
    shouldAttemptStaleAutoRetry({
      enabled: true,
      connectionStatus: "TOKEN_EXPIRED",
      portfolioStale: true,
      alreadyAttempted: false,
    })
  ) {
    throw new Error("Today sync auto-retry self-check failed: expired session");
  }

  if (
    shouldAttemptStaleAutoRetry({
      enabled: true,
      connectionStatus: "CONNECTED",
      portfolioStale: true,
      alreadyAttempted: true,
    })
  ) {
    throw new Error("Today sync auto-retry self-check failed: duplicate attempt");
  }
}
