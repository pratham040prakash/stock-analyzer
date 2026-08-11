"use client";

import { formatInr } from "@/lib/funds";
import { resolvePortfolioDisplayValue } from "@/lib/portfolio/displayValue";
import type { PortfolioHoldingRow } from "@/types/portfolioApi";

export type TodayPortfolioHoldingsProps = {
  holdings: PortfolioHoldingRow[];
  totalValue?: number | null;
  totalPnl?: number | null;
  loading?: boolean;
  showEmptyWhenSynced?: boolean;
  stale?: boolean;
};

function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

function pnlClass(pnl: number): string {
  if (pnl > 0) return "text-emerald-300/90";
  if (pnl < 0) return "text-amber-200/90";
  return "text-apex-muted/70";
}

export default function TodayPortfolioHoldings({
  holdings,
  totalValue,
  totalPnl,
  loading = false,
  showEmptyWhenSynced = false,
  stale = false,
}: TodayPortfolioHoldingsProps) {
  if (loading) {
    return (
      <div
        className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3"
        aria-label="Portfolio holdings loading"
      >
        <p className="text-xs text-apex-muted/75">Loading your holdings…</p>
      </div>
    );
  }

  if (holdings.length === 0) {
    if (!showEmptyWhenSynced) {
      return null;
    }

    return (
      <div
        className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3"
        aria-label="Portfolio holdings empty"
      >
        <p className="text-xs text-apex-muted/75">
          Holdings not synced yet.{" "}
          <a
            href="/api/zerodha/login"
            className="underline underline-offset-2 hover:text-apex-text/90"
          >
            Reconnect Zerodha
          </a>{" "}
          or wait until the market opens for a fresh sync.
        </p>
      </div>
    );
  }

  const resolvedTotal = resolvePortfolioDisplayValue(totalValue, holdings);
  const resolvedPnl =
    typeof totalPnl === "number" && Number.isFinite(totalPnl)
      ? totalPnl
      : holdings.reduce((sum, row) => sum + row.pnl, 0);

  return (
    <div
      className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3"
      aria-label="Portfolio holdings"
    >
      <details open className="text-xs text-apex-muted/75">
        <summary className="cursor-pointer select-none text-sm text-apex-text/80 hover:text-apex-text">
          Your holdings · {formatInr(Math.round(resolvedTotal))}
          {stale ? (
            <span className="ml-2 text-amber-200/90">· stale</span>
          ) : null}
          <span className={`ml-2 tabular-nums ${pnlClass(resolvedPnl)}`}>
            {resolvedPnl >= 0 ? "+" : ""}
            {formatInr(Math.round(resolvedPnl))} total P&amp;L
          </span>
        </summary>

        <ul className="mt-2 space-y-2 border-t border-apex-border/10 pt-2">
          {holdings.map((row) => (
            <li
              key={row.tradingsymbol}
              className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-1 tabular-nums"
            >
              <div>
                <p className="text-sm font-medium text-apex-text/90">
                  {row.tradingsymbol}
                </p>
                <p className="text-[11px] text-apex-muted/60">
                  {row.quantity} × avg {formatPrice(row.average_price)} · LTP{" "}
                  {formatPrice(row.last_price)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-apex-text/85">
                  {formatInr(Math.round(row.value))}
                </p>
                <p className={`text-[11px] ${pnlClass(row.pnl)}`}>
                  {row.pnl >= 0 ? "+" : ""}
                  {formatInr(Math.round(row.pnl))}
                  <span className="text-apex-muted/55">
                    {" "}
                    · {Math.round(row.allocation_pct)}% alloc
                  </span>
                </p>
              </div>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
