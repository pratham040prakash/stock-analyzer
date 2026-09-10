"use client";

import Link from "next/link";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { formatInr } from "@/lib/funds";

type Props = {
  connectionStatus: ConnectionStatus;
  bookValue?: number | null;
  dayPnl?: number | null;
  cashInr?: number | null;
  lastSyncedAt?: string | null;
  proofHref?: string | null;
};

function knownAmount(value?: number | null): value is number {
  return value !== null && value !== undefined && Number.isFinite(value);
}

function formatSyncedAt(updatedAt?: string | null): string | null {
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

function pnlTone(value: number): string {
  if (Math.abs(value) < 0.5) {
    return "text-apex-text";
  }

  return value > 0 ? "text-emerald-200" : "text-rose-200";
}

export default function PortfolioBookHero({
  connectionStatus,
  bookValue,
  dayPnl,
  cashInr,
  lastSyncedAt,
  proofHref,
}: Props) {
  const syncedAt = formatSyncedAt(lastSyncedAt);
  const bookKnown = knownAmount(bookValue);
  const dayKnown = knownAmount(dayPnl);
  const cashKnown = knownAmount(cashInr) && cashInr > 0;

  return (
    <section
      aria-label="Your book"
      className="relative overflow-hidden rounded-[28px] border border-white/[0.08] bg-gradient-to-b from-slate-400/[0.08] to-transparent px-5 py-7 sm:px-8 sm:py-9"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(148,163,184,0.20),transparent_58%)]" />

      <div className="relative text-center">
        <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-apex-muted/70">
          Your book
        </p>
        <p className="mt-3 text-5xl font-semibold tracking-tight text-white sm:text-6xl">
          {bookKnown ? formatInr(bookValue) : "—"}
        </p>
        {dayKnown ? (
          <p className={`mt-2 text-sm font-medium ${pnlTone(dayPnl)}`}>
            {Math.abs(dayPnl) < 0.5
              ? "Flat today"
              : `${dayPnl > 0 ? "+" : "−"}${formatInr(Math.abs(dayPnl))} today`}
          </p>
        ) : null}
        {cashKnown ? (
          <p className="mt-4 text-sm text-apex-muted/85">
            {formatInr(cashInr)} cash ready
          </p>
        ) : null}
        <p className="mt-3 text-[11px] text-apex-muted/65">
          {connectionStatus === "CONNECTED"
            ? "Zerodha connected"
            : connectionStatus === "TOKEN_EXPIRED"
              ? "Session expired"
              : "Zerodha not connected"}
          {syncedAt ? ` · ${syncedAt} IST` : ""}
        </p>
        {proofHref ? (
          <Link
            href={proofHref}
            className="mt-3 inline-flex text-xs text-apex-muted/70 underline-offset-2 hover:text-apex-text hover:underline"
          >
            Decision proof →
          </Link>
        ) : null}
      </div>
    </section>
  );
}
