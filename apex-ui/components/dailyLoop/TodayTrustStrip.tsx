"use client";

import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { formatInr } from "@/lib/funds";

export type TodayTrustStripProps = {
  connectionStatus: ConnectionStatus;
  availableCash?: number | null;
  portfolioValue?: number;
  dayPnl?: number | null;
  updatedAt?: string | null;
  fundsLoading?: boolean;
};

function formatUpdatedAt(updatedAt?: string | null): string | null {
  if (!updatedAt) {
    return null;
  }

  const date = new Date(updatedAt);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toLocaleTimeString("en-IN", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "Asia/Kolkata",
  });
}

function connectionLabel(status: ConnectionStatus): string {
  if (status === "CONNECTED") {
    return "Zerodha connected";
  }

  if (status === "TOKEN_EXPIRED") {
    return "Session expired — reconnect";
  }

  return "Zerodha not connected";
}

export default function TodayTrustStrip({
  connectionStatus,
  availableCash,
  portfolioValue,
  dayPnl,
  updatedAt,
  fundsLoading = false,
}: TodayTrustStripProps) {
  const syncedAt = formatUpdatedAt(updatedAt);
  const cashKnown = availableCash !== null && availableCash !== undefined;
  const portfolioKnown =
    portfolioValue !== undefined && Number.isFinite(portfolioValue);
  const dayKnown = dayPnl !== null && dayPnl !== undefined && Number.isFinite(dayPnl);

  return (
    <div
      className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3"
      aria-label="Capital sync status"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-apex-muted/80">
        <span
          className={
            connectionStatus === "CONNECTED"
              ? "font-medium text-emerald-200/90"
              : "font-medium text-amber-200/90"
          }
        >
          {connectionLabel(connectionStatus)}
        </span>
        {syncedAt ? <span>Updated {syncedAt} IST</span> : null}
        {fundsLoading ? <span>Refreshing funds…</span> : null}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-apex-text/80">
        <span>
          Available cash:{" "}
          {cashKnown ? formatInr(Math.max(0, availableCash ?? 0)) : "—"}
        </span>
        {portfolioKnown ? (
          <span>Portfolio: {formatInr(Math.max(0, portfolioValue ?? 0))}</span>
        ) : null}
        {dayKnown ? (
          <span
            className={
              (dayPnl ?? 0) >= 0 ? "text-emerald-300/90" : "text-amber-200/90"
            }
          >
            Day P&amp;L: {(dayPnl ?? 0) >= 0 ? "+" : ""}
            {formatInr(Math.round(dayPnl ?? 0))}
          </span>
        ) : null}
      </div>
    </div>
  );
}
