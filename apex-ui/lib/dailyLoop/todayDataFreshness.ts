import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { TODAY_SYNC_RECOVERY } from "@/lib/dailyLoop/todaySyncRecoveryCopy";

export type TodayDataFreshness = {
  isStale: boolean;
  headline: string;
  detail: string;
  reconnectHref: string;
  suppressTrustScore: boolean;
  trustFootnote: string;
  showSoftRefresh: boolean;
  softRefreshLabel: string;
};

export function resolveTodayDataFreshness(input: {
  connectionStatus: ConnectionStatus;
  portfolioStale?: boolean;
  pollError?: string | null;
  fundsSyncError?: string | null;
}): TodayDataFreshness {
  const reconnectHref = "/api/zerodha/login";
  const softRefreshLabel = TODAY_SYNC_RECOVERY.softRefreshLabel;

  if (input.connectionStatus === "TOKEN_EXPIRED") {
    return {
      isStale: true,
      headline: "Session expired",
      detail: "Reconnect Zerodha to refresh cash, holdings, and live prices.",
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · reconnect for live prices",
      showSoftRefresh: false,
      softRefreshLabel,
    };
  }

  if (input.fundsSyncError) {
    return {
      isStale: true,
      headline: "Broker sync issue",
      detail: `${input.fundsSyncError} ${TODAY_SYNC_RECOVERY.fundsSyncDetailSuffix}`,
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · prices may be outdated",
      showSoftRefresh: true,
      softRefreshLabel,
    };
  }

  if (input.pollError) {
    return {
      isStale: true,
      headline: "Live prices updating",
      detail: TODAY_SYNC_RECOVERY.pollErrorDetail,
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · live quotes may lag",
      showSoftRefresh: true,
      softRefreshLabel,
    };
  }

  if (input.portfolioStale) {
    return {
      isStale: true,
      headline: "Portfolio data is stale",
      detail: TODAY_SYNC_RECOVERY.portfolioStaleDetail,
      reconnectHref,
      suppressTrustScore: true,
      trustFootnote: "Discipline score · portfolio snapshot may lag",
      showSoftRefresh: true,
      softRefreshLabel,
    };
  }

  return {
    isStale: false,
    headline: "",
    detail: "",
    reconnectHref,
    suppressTrustScore: false,
    trustFootnote: "",
    showSoftRefresh: false,
    softRefreshLabel,
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

  if (!stale.showSoftRefresh) {
    throw new Error("Today data freshness self-check failed: portfolio stale refresh");
  }

  const expired = resolveTodayDataFreshness({
    connectionStatus: "TOKEN_EXPIRED",
  });

  if (expired.showSoftRefresh) {
    throw new Error("Today data freshness self-check failed: token expired refresh");
  }

  const fresh = resolveTodayDataFreshness({
    connectionStatus: "CONNECTED",
    portfolioStale: false,
  });

  if (fresh.isStale) {
    throw new Error("Today data freshness self-check failed: fresh state");
  }
}
