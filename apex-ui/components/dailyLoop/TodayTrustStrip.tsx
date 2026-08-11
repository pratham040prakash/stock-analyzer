"use client";

import Link from "next/link";
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
  openPnl?: number | null;
  portfolioDayPnl?: number | null;
  positionsBreakdown?: ZerodhaPositionPnlRow[];
  lastSyncedAt?: string | null;
  portfolioStale?: boolean;
  pollError?: string | null;
  breakdownLoading?: boolean;
  isPolling?: boolean;
  fundsLoading?: boolean;
  fundsSynced?: boolean;
  fundsSyncError?: string | null;
  proofHref?: string | null;
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
    return "Session expired — reconnect to refresh live data";
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
  openPnl,
  portfolioDayPnl,
  positionsBreakdown = [],
  lastSyncedAt,
  portfolioStale = false,
  pollError = null,
  breakdownLoading = false,
  isPolling = false,
  fundsLoading = false,
  fundsSynced = false,
  fundsSyncError = null,
  proofHref = null,
}: TodayTrustStripProps) {
  const syncedAt = formatUpdatedAt(lastSyncedAt);
  const deployableResolved = knownAmount(marginAvailable)
    ? Math.max(0, marginAvailable)
    : fundsSynced && !fundsSyncError
      ? 0
      : null;
  const showLiveCapital = connectionStatus === "CONNECTED";
  const portfolioKnown = showLiveCapital && knownAmount(portfolioValue);
  const totalKnown = showLiveCapital && knownAmount(totalCapital);
  const breakdownSum =
    positionsBreakdown.length > 0
      ? positionsBreakdown.reduce((sum, row) => sum + row.pnl, 0)
      : null;
  const displayOpenPnl = knownAmount(openPnl)
    ? openPnl
    : breakdownSum !== null && Number.isFinite(breakdownSum)
      ? Math.round(breakdownSum * 10) / 10
      : null;
  const openPnlKnown = knownAmount(displayOpenPnl);
  const showOpenPnl = openPnlKnown && !breakdownLoading;
  const dayPnlKnown = knownAmount(portfolioDayPnl);
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
        {syncedAt ? <span>Synced {syncedAt} IST</span> : null}
        {portfolioStale ? (
          <span className="text-amber-200/90">Stale · reconnect to refresh</span>
        ) : null}
        {pollError ? <span className="text-amber-200/90">{pollError}</span> : null}
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
        {connectionStatus === "TOKEN_EXPIRED" && !fundsSyncError ? (
          <span className="text-amber-200/90">
            <a
              href="/api/zerodha/login"
              className="underline underline-offset-2 hover:text-amber-100"
            >
              Reconnect Zerodha
            </a>{" "}
            to refresh portfolio and live P&amp;L
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
          {dayPnlKnown ? (
            <span
              className={
                (portfolioDayPnl ?? 0) >= 0
                  ? "text-emerald-300/90"
                  : "text-amber-200/90"
              }
            >
              Day P&amp;L {(portfolioDayPnl ?? 0) >= 0 ? "+" : ""}
              {formatInr(Math.round(portfolioDayPnl ?? 0))}
            </span>
          ) : connectionStatus === "CONNECTED" && !pollError ? (
            <span className="text-apex-muted/70">Day P&amp;L …</span>
          ) : null}
          {showOpenPnl ? (
            <span
              className={
                (displayOpenPnl ?? 0) >= 0 ? "text-emerald-300/90" : "text-amber-200/90"
              }
            >
              Open P&amp;L {(displayOpenPnl ?? 0) >= 0 ? "+" : ""}
              {formatInr(Math.round(displayOpenPnl ?? 0))}
            </span>
          ) : connectionStatus === "CONNECTED" && !pollError && breakdownLoading ? (
            <span className="text-apex-muted/70">Open P&amp;L syncing…</span>
          ) : connectionStatus === "CONNECTED" && !pollError && isPolling ? (
            <span className="text-apex-muted/70">Open P&amp;L syncing…</span>
          ) : null}
        </div>

        {breakdownLoading && !pollError ? (
          <p className="mt-2 text-xs text-apex-muted/70">
            Fetching position breakdown…
          </p>
        ) : null}

        {positionsBreakdown.length > 0 ? (
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
            <p className="mt-1.5 text-[11px] text-apex-muted/55">
              LTP − avg × qty · live quote when available
            </p>
          </details>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
        <Link
          href="/app/portfolio"
          className="text-blue-200/90 transition-colors hover:text-blue-100"
        >
          Portfolio details →
        </Link>
        {proofHref ? (
          <Link
            href={proofHref}
            className="text-blue-200/90 transition-colors hover:text-blue-100"
          >
            Decision proof →
          </Link>
        ) : null}
      </div>
    </div>
  );
}
