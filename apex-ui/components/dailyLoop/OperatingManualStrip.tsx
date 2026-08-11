"use client";

import Link from "next/link";
import type { DailyVerdict } from "@/lib/dailyLoop/dailyVerdict";

export type OperatingManualStripProps = {
  dailyVerdict: DailyVerdict;
  tacticalPoolInr?: number | null;
  className?: string;
};

function formatTacticalPool(value?: number | null): string | null {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }

  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export default function OperatingManualStrip({
  dailyVerdict,
  tacticalPoolInr,
  className = "",
}: OperatingManualStripProps) {
  const tactical = formatTacticalPool(tacticalPoolInr);

  return (
    <div
      className={`rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 text-xs text-apex-muted/80 ${className}`.trim()}
      aria-label="Your investment plan"
    >
      <p className="font-medium text-apex-text/85">Your plan</p>
      <ul className="mt-1.5 space-y-1">
        <li>Long-term core · hold for years · not traded on Today</li>
        <li>Tactical pool · swing 2–8 weeks · only on Trade days</li>
        <li>Intraday · not APEX — use Kite separately</li>
      </ul>
      {dailyVerdict === "trade" && tactical ? (
        <p className="mt-2 text-apex-text/80">
          Today applies to tactical capital only · {tactical} deployable
        </p>
      ) : dailyVerdict === "pause" ? (
        <p className="mt-2 text-amber-100/85">
          Pause day — protect capital. No tactical trades today.
        </p>
      ) : (
        <p className="mt-2 text-apex-text/75">
          {dailyVerdict === "wait"
            ? "Wait day — no tactical action required."
            : "Review your plan before acting."}
        </p>
      )}
      <Link
        href="/app/you"
        className="mt-2 inline-block text-blue-200/90 underline-offset-2 hover:text-blue-100 hover:underline"
      >
        How APEX works →
      </Link>
    </div>
  );
}
