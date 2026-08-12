"use client";

import { formatInr } from "@/lib/funds";
import { journeyBarGradient } from "@/lib/journey/journeyBarStyle";

export type JourneyTargetTrackProps = {
  symbol: string;
  entryPriceInr: number;
  targetPriceInr: number;
  currentPriceInr?: number | null;
  progressPct: number;
  targetReached?: boolean;
  thesisBroken?: boolean;
  compact?: boolean;
  className?: string;
};

function formatPrice(value: number): string {
  return formatInr(Math.round(value));
}

export default function JourneyTargetTrack({
  symbol,
  entryPriceInr,
  targetPriceInr,
  currentPriceInr,
  progressPct,
  targetReached = false,
  thesisBroken = false,
  compact = false,
  className = "",
}: JourneyTargetTrackProps) {
  const clampedPct = Math.max(0, Math.min(100, progressPct));
  const barStyle = journeyBarGradient(symbol, { targetReached, thesisBroken });
  const barHeight = compact ? "h-7" : "h-9";
  const pctInsideFill = clampedPct >= 14;
  const fillWidth = targetReached
    ? 100
    : clampedPct > 0
      ? Math.max(clampedPct, 8)
      : 0;

  return (
    <div className={className}>
      <div
        className={[
          "grid items-center gap-x-3",
          compact
            ? "grid-cols-[minmax(5.5rem,6.5rem)_1fr_minmax(3.5rem,4.5rem)] sm:gap-x-4"
            : "grid-cols-[minmax(6rem,7.5rem)_1fr_minmax(4rem,5rem)] sm:gap-x-4",
        ].join(" ")}
      >
        {/* Left label */}
        <div className="min-w-0">
          <div className="flex items-start gap-1.5">
            <span
              className={["mt-1.5 h-2 w-2 shrink-0 rounded-full", barStyle.dotClass].join(" ")}
              aria-hidden
            />
            <div className="min-w-0">
              <p
                className={[
                  "truncate font-semibold leading-tight text-apex-text",
                  compact ? "text-sm" : "text-base",
                ].join(" ")}
              >
                {symbol}
              </p>
              <p className="mt-0.5 truncate text-[10px] tabular-nums text-apex-muted/75 sm:text-[11px]">
                Entry {formatPrice(entryPriceInr)}
              </p>
            </div>
          </div>
        </div>

        {/* Infographic bar */}
        <div className="min-w-0">
          <div
            className={[
              "relative overflow-hidden rounded-full bg-black/55 shadow-[inset_0_1px_3px_rgba(0,0,0,0.45),0_2px_8px_rgba(0,0,0,0.2)]",
              barHeight,
            ].join(" ")}
            role="progressbar"
            aria-valuenow={clampedPct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${symbol}: ${clampedPct}% from entry to target`}
          >
            <div
              className={[
                "absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-[width] duration-700 ease-out",
                barStyle.fillClass,
                targetReached ? "shadow-[0_0_14px_rgba(52,211,153,0.4)]" : "",
              ].join(" ")}
              style={{ width: `${fillWidth}%` }}
            >
              {pctInsideFill ? (
                <span
                  className={[
                    "absolute inset-y-0 right-2 flex items-center font-bold tabular-nums text-white drop-shadow-sm",
                    compact ? "text-[11px]" : "text-xs",
                  ].join(" ")}
                >
                  {targetReached ? "100%" : `${clampedPct}%`}
                </span>
              ) : null}
            </div>

            {targetReached ? (
              <span className="pointer-events-none absolute inset-0 flex items-center justify-center text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-50/95">
                Target met
              </span>
            ) : null}
          </div>

          {!pctInsideFill && clampedPct > 0 && !targetReached ? (
            <p className="mt-1 text-center text-[10px] font-semibold tabular-nums text-apex-muted/80">
              {clampedPct}%
            </p>
          ) : null}
        </div>

        {/* Right target */}
        <div className="min-w-0 text-right">
          <p className="text-[10px] uppercase tracking-wide text-apex-muted/55">Target</p>
          <p
            className={[
              "font-semibold tabular-nums leading-tight text-apex-text",
              compact ? "text-xs" : "text-sm",
            ].join(" ")}
          >
            {formatPrice(targetPriceInr)}
          </p>
        </div>
      </div>

      {currentPriceInr !== null && currentPriceInr !== undefined && !compact ? (
        <p className="mt-2 text-[11px] tabular-nums text-apex-muted/65 sm:ml-[calc(7.5rem+1rem)]">
          Now {formatPrice(currentPriceInr)}
          {clampedPct < 100 && !targetReached ? ` · ${100 - clampedPct}% left` : ""}
        </p>
      ) : null}
    </div>
  );
}
