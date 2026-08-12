"use client";

import Link from "next/link";
import type { DailyVerdict } from "@/lib/dailyLoop/dailyVerdict";
import { OPERATING_MANUAL } from "@/lib/dailyLoop/operatingManualCopy";

export type OperatingManualStripProps = {
  dailyVerdict: DailyVerdict;
  tacticalPoolInr?: number | null;
  collapseByDefault?: boolean;
  className?: string;
};

function formatTacticalPool(value?: number | null): string | null {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }

  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

function PlanBody({
  dailyVerdict,
  tacticalPoolInr,
}: Pick<OperatingManualStripProps, "dailyVerdict" | "tacticalPoolInr">) {
  const tactical = formatTacticalPool(tacticalPoolInr);

  return (
    <>
      <ul className="mt-1.5 space-y-1">
        <li>{OPERATING_MANUAL.coreLine}</li>
        <li>{OPERATING_MANUAL.tacticalLine}</li>
        <li>{OPERATING_MANUAL.intradayLine}</li>
      </ul>
      {dailyVerdict === "trade" && tactical ? (
        <p className="mt-2 text-apex-text/80">
          {OPERATING_MANUAL.tradeTacticalPrefix} · {tactical} deployable
        </p>
      ) : dailyVerdict === "pause" ? (
        <p className="mt-2 text-amber-100/85">{OPERATING_MANUAL.pauseDay}</p>
      ) : (
        <p className="mt-2 text-apex-text/75">
          {dailyVerdict === "wait"
            ? OPERATING_MANUAL.waitDay
            : "Review your plan before acting."}
        </p>
      )}
      <Link
        href={OPERATING_MANUAL.helpHref}
        className="mt-2 inline-block text-blue-200/90 underline-offset-2 hover:text-blue-100 hover:underline"
      >
        {OPERATING_MANUAL.helpLink}
      </Link>
    </>
  );
}

export default function OperatingManualStrip({
  dailyVerdict,
  tacticalPoolInr,
  collapseByDefault = false,
  className = "",
}: OperatingManualStripProps) {
  if (collapseByDefault) {
    return (
      <details
        className={`rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 text-xs text-apex-muted/80 ${className}`.trim()}
      >
        <summary className="cursor-pointer list-none font-medium text-apex-text/85 marker:content-none [&::-webkit-details-marker]:hidden">
          {OPERATING_MANUAL.planTitle}
          <span className="ml-2 font-normal text-apex-muted/60">
            · tap to expand
          </span>
        </summary>
        <PlanBody dailyVerdict={dailyVerdict} tacticalPoolInr={tacticalPoolInr} />
      </details>
    );
  }

  return (
    <div
      className={`rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 text-xs text-apex-muted/80 ${className}`.trim()}
      aria-label="Your investment plan"
    >
      <p className="font-medium text-apex-text/85">{OPERATING_MANUAL.planTitle}</p>
      <PlanBody dailyVerdict={dailyVerdict} tacticalPoolInr={tacticalPoolInr} />
    </div>
  );
}
