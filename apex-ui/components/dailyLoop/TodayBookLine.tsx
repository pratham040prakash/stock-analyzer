"use client";

import Link from "next/link";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { formatInr } from "@/lib/funds";

type Props = {
  connectionStatus: ConnectionStatus;
  portfolioValue?: number | null;
  cashInr?: number | null;
  dayPnl?: number | null;
};

function knownAmount(value?: number | null): value is number {
  return value !== null && value !== undefined && Number.isFinite(value);
}

export default function TodayBookLine({
  connectionStatus,
  portfolioValue,
  cashInr,
  dayPnl,
}: Props) {
  if (connectionStatus !== "CONNECTED" && connectionStatus !== "TOKEN_EXPIRED") {
    return null;
  }

  const pnl =
    knownAmount(dayPnl) && dayPnl !== 0
      ? `${dayPnl > 0 ? "+" : "−"}${formatInr(Math.abs(dayPnl))} today`
      : knownAmount(dayPnl)
        ? "Flat today"
        : null;
  const book = knownAmount(portfolioValue) ? formatInr(portfolioValue) : null;
  const cash =
    knownAmount(cashInr) && (portfolioValue === 0 || portfolioValue == null)
      ? `${formatInr(cashInr)} cash`
      : null;

  return (
    <Link
      href="/app/portfolio"
      className="flex items-center justify-between gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 transition-colors hover:bg-white/[0.05]"
    >
      <div>
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-apex-muted/70">
          {connectionStatus === "TOKEN_EXPIRED"
            ? "Zerodha session expired"
            : "Your book"}
        </p>
        <p className="mt-0.5 text-sm font-medium text-apex-text">
          {book ?? "Zerodha connected"}
          {cash ? ` · ${cash}` : ""}
          {pnl ? ` · ${pnl}` : ""}
        </p>
      </div>
      <span className="text-xs text-apex-muted/70">Portfolio →</span>
    </Link>
  );
}
