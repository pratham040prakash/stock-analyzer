"use client";

import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { formatInr } from "@/lib/funds";
import type { ZerodhaPositionPnlRow } from "@/services/brokers/zerodha";

export type TodayTrustStripProps = {
  connectionStatus: ConnectionStatus;
  marginAvailable?: number | null;
  ledgerCash?: number | null;
  collateral?: number | null;
  portfolioValue?: number | null;
  totalCapital?: number | null;
  dayPnl?: number | null;
  positionsBreakdown?: ZerodhaPositionPnlRow[];
  updatedAt?: string | null;
  fundsLoading?: boolean;
  fundsSynced?: boolean;
  fundsSyncError?: string | null;
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

function knownAmount(value?: number | null): value is number {
  return value !== null && value !== undefined && Number.isFinite(value);
}

export default function TodayTrustStrip({
  connectionStatus,
  marginAvailable,
  ledgerCash,
  collateral,
  portfolioValue,
  totalCapital,
  dayPnl,
  positionsBreakdown = [],
  updatedAt,
  fundsLoading = false,
  fundsSynced = false,
  fundsSyncError = null,
}: TodayTrustStripProps) {
  const syncedAt = formatUpdatedAt(updatedAt);
  const deployableResolved = knownAmount(marginAvailable)
    ? Math.max(0, marginAvailable)
    : fundsSynced && !fundsSyncError
      ? 0
      : null;
  const portfolioKnown = knownAmount(portfolioValue);
  const totalKnown = knownAmount(totalCapital);
  const dayKnown = knownAmount(dayPnl);
  const resolvedTotal =
    totalKnown
      ? totalCapital
      : portfolioKnown && knownAmount(ledgerCash)
        ? (portfolioValue ?? 0) + (ledgerCash ?? 0)
        : null;

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
        {fundsLoading ? <span>Syncing Zerodha funds…</span> : null}
        {fundsSyncError && !fundsLoading ? (
          <span className="text-amber-200/90">
            {fundsSyncError}{" "}
            <a
              href="/api/zerodha/login"
              className="underline underline-offset-2 hover:text-amber-100"
            >
              Reconnect Zerodha
            </a>
          </span>
        ) : null}
      </div>

      <div className="mt-2 space-y-1.5 text-sm text-apex-text/80">
        <p>
          <span className="text-apex-muted/75">Available to deploy: </span>
          {deployableResolved !== null ? (
            formatInr(deployableResolved)
          ) : fundsLoading ? (
            "…"
          ) : (
            "—"
          )}
          <span className="text-xs text-apex-muted/60"> · Cash + Collateral</span>
        </p>

        {fundsSynced && !fundsSyncError ? (
          <p className="text-xs text-apex-muted/75">
            <span>Cash {formatInr(Math.max(0, ledgerCash ?? 0))}</span>
            {(collateral ?? 0) > 0 ? (
              <span> · Collateral {formatInr(Math.max(0, collateral ?? 0))}</span>
            ) : null}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {portfolioKnown ? (
            <span>Portfolio {formatInr(Math.max(0, portfolioValue ?? 0))}</span>
          ) : null}
          {resolvedTotal !== null ? (
            <span>Total capital {formatInr(Math.max(0, resolvedTotal))}</span>
          ) : null}
          {dayKnown ? (
            <span
              className={
                (dayPnl ?? 0) >= 0 ? "text-emerald-300/90" : "text-amber-200/90"
              }
            >
              Open P&amp;L {(dayPnl ?? 0) >= 0 ? "+" : ""}
              {formatInr(Math.round(dayPnl ?? 0))}
            </span>
          ) : null}
        </div>

        {dayKnown && positionsBreakdown.length === 0 ? (
          <p className="mt-2 text-xs text-amber-200/80">
            Zerodha net positions are syncing — expand after refresh if rows are
            missing.
          </p>
        ) : null}

        {dayKnown && positionsBreakdown.length > 0 ? (
          <details className="mt-2 text-xs text-apex-muted/75" open>
            <summary className="cursor-pointer select-none hover:text-apex-muted">
              How Open P&amp;L is calculated (matches Zerodha Positions)
            </summary>
            <ul className="mt-1.5 space-y-1 border-t border-apex-border/10 pt-1.5">
              {positionsBreakdown.map((row) => (
                <li
                  key={row.symbol}
                  className="flex items-baseline justify-between gap-3 tabular-nums"
                >
                  <span>
                    {row.symbol}{" "}
                    <span className="text-apex-muted/60">×{row.quantity}</span>
                  </span>
                  <span
                    className={
                      row.pnl >= 0 ? "text-emerald-300/90" : "text-amber-200/90"
                    }
                  >
                    {row.pnl >= 0 ? "+" : ""}
                    {formatInr(Math.round(row.pnl))}
                  </span>
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </div>
    </div>
  );
}
