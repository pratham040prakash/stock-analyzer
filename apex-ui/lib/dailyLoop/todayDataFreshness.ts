import type { ConnectionStatus } from "@/lib/broker/zerodha";

export type TodayDataFreshness = {
  isStale: boolean;
  headline: string;
  detail: string;
  reconnectHref: string;
  suppressTrustScore: boolean;
  trustFootnote: string;
};

export function resolveTodayDataFreshness(input: {
  connectionStatus: ConnectionStatus;
  portfolioStale?: boolean;
  pollError?: string | null;
  fundsSyncError?: string | null;
}): TodayDataFreshness {
  const reconnectHref = "/api/zerodha/login";

  if (input.connectionStatus === "TOKEN_EXPIRED") {
    return {
      isStale: true,
      headline: "Session expired",
      detail: "Reconnect Zerodha to refresh cash, holdings, and live prices.",
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · reconnect for live prices",
    };
  }

  if (input.fundsSyncError) {
    return {
      isStale: true,
      headline: "Broker sync issue",
      detail: input.fundsSyncError,
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · prices may be outdated",
    };
  }

  if (input.pollError) {
    return {
      isStale: true,
      headline: "Live prices updating",
      detail: input.pollError,
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · live quotes may lag",
    };
  }

  if (input.portfolioStale) {
    return {
      isStale: true,
      headline: "Portfolio data is stale",
      detail: "Cash may still be accurate. Reconnect to refresh holdings and LTP.",
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · portfolio snapshot may lag",
    };
  }

  return {
    isStale: false,
    headline: "",
    detail: "",
    reconnectHref,
    suppressTrustScore: false,
    trustFootnote: "",
  };
}

export function runTodayDataFreshnessSelfCheck(): void {
  const stale = resolveTodayDataFreshness({
    connectionStatus: "CONNECTED",
    portfolioStale: true,
  });

  if (!stale.isStale || !stale.suppressTrustScore) {
    throw new Error("Today data freshness self-check failed: stale portfolio");
  }

  const fresh = resolveTodayDataFreshness({
    connectionStatus: "CONNECTED",
    portfolioStale: false,
  });

  if (fresh.isStale) {
    throw new Error("Today data freshness self-check failed: fresh state");
  }
}
