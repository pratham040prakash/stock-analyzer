"use client";

import { formatInr } from "@/lib/funds";

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
  const fillTone = targetReached
    ? "from-emerald-400 to-emerald-500"
    : thesisBroken
      ? "from-amber-400/90 to-amber-600/80"
      : "from-violet-400/90 to-emerald-400/90";

  return (
    <div className={className}>
      <p
        className={[
          "font-semibold tracking-tight text-apex-text",
          compact ? "text-base" : "text-xl",
        ].join(" ")}
      >
        {symbol}
      </p>

      <div
        className={[
          "mt-3 flex items-center justify-between gap-2 text-xs tabular-nums text-apex-text/85",
          compact ? "mt-2" : "",
        ].join(" ")}
      >
        <span className="shrink-0">
          Entry <span className="font-medium text-apex-text">{formatPrice(entryPriceInr)}</span>
        </span>
        <span className="text-apex-muted/50" aria-hidden>
          ───────────────►
        </span>
        <span className="shrink-0 text-right">
          Target{" "}
          <span className="font-medium text-emerald-200/95">{formatPrice(targetPriceInr)}</span>
        </span>
      </div>

      <div className={compact ? "mt-2" : "mt-3"}>
        <div
          className="relative h-3 overflow-visible rounded-full bg-black/30"
          role="progressbar"
          aria-valuenow={clampedPct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${symbol} progress from entry to target`}
        >
          <div
            className={[
              "absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-all duration-500",
              fillTone,
            ].join(" ")}
            style={{ width: `${clampedPct}%` }}
          />
          {!targetReached && clampedPct > 0 && clampedPct < 100 ? (
            <span
              className="absolute top-1/2 z-10 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white/90 bg-violet-300 shadow-md"
              style={{ left: `${clampedPct}%` }}
              title={
                currentPriceInr !== null && currentPriceInr !== undefined
                  ? `Now ${formatPrice(currentPriceInr)}`
                  : `${clampedPct}% toward target`
              }
            />
          ) : null}
          {targetReached ? (
            <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold uppercase tracking-wider text-emerald-950/90">
              Target met
            </span>
          ) : null}
        </div>

        <div className="mt-1.5 flex items-center justify-between text-[11px] text-apex-muted/70">
          <span>{clampedPct}% to target</span>
          {currentPriceInr !== null && currentPriceInr !== undefined ? (
            <span>Now {formatPrice(currentPriceInr)}</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
