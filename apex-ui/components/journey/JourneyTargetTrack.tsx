"use client";

import { formatInr } from "@/lib/funds";
import { journeyBarGradient } from "@/lib/journey/journeyBarStyle";
import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";
import { resolveJourneyWaitPathInsight } from "@/lib/journey/journeyWaitPathInsight";

export type JourneyTargetTrackProps = {
  symbol: string;
  entryPriceInr: number;
  targetPriceInr: number;
  currentPriceInr?: number | null;
  progressPct: number;
  /** When true, show live price marker only — no trade progress fill. */
  waitingForEntry?: boolean;
  targetReached?: boolean;
  thesisBroken?: boolean;
  compact?: boolean;
  className?: string;
  timeTargetLabel?: string | null;
  timeProgressPct?: number | null;
  timeRemainingLabel?: string | null;
  timeOverdue?: boolean;
  patienceUntilLabel?: string | null;
};

function formatPrice(value: number): string {
  return formatInr(Math.round(value));
}

function pricePathPositionPct(
  entry: number,
  target: number,
  current: number | null | undefined,
): number | null {
  if (current === null || current === undefined || !Number.isFinite(current)) {
    return null;
  }

  if (target === entry) {
    return null;
  }

  const raw = ((current - entry) / (target - entry)) * 100;
  return Math.max(0, Math.min(100, raw));
}

export default function JourneyTargetTrack({
  symbol,
  entryPriceInr,
  targetPriceInr,
  currentPriceInr,
  progressPct,
  waitingForEntry = false,
  targetReached = false,
  thesisBroken = false,
  compact = false,
  className = "",
  timeTargetLabel = null,
  timeProgressPct = null,
  timeRemainingLabel = null,
  timeOverdue = false,
  patienceUntilLabel = null,
}: JourneyTargetTrackProps) {
  const clampedPct = Math.max(0, Math.min(100, progressPct));
  const showTradeProgress = !waitingForEntry;
  const displayPct = showTradeProgress ? clampedPct : 0;
  const priceMarkerPct = waitingForEntry
    ? pricePathPositionPct(entryPriceInr, targetPriceInr, currentPriceInr)
    : null;
  const barStyle = journeyBarGradient(symbol, { targetReached, thesisBroken });
  const barHeight = compact ? "h-7" : "h-9";
  const pctInsideFill = showTradeProgress && displayPct >= 14;
  const fillWidth = targetReached
    ? 100
    : showTradeProgress && displayPct > 0
      ? Math.max(displayPct, 8)
      : 0;

  const timeClamped =
    timeProgressPct === null ? null : Math.max(0, Math.min(100, timeProgressPct));

  const waitPathInsight = resolveJourneyWaitPathInsight({
    waitingForEntry,
    entryPriceInr,
    targetPriceInr,
    currentPriceInr,
  });

  return (
    <div className={className}>
      {patienceUntilLabel && !compact ? (
        <p className="mb-3 text-sm font-medium leading-snug text-sky-100/95">
          {patienceUntilLabel}
        </p>
      ) : null}
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
              <p
                className={[
                  "mt-0.5 truncate text-[10px] tabular-nums sm:text-[11px]",
                  currentPriceInr !== null && currentPriceInr !== undefined
                    ? "font-medium text-sky-200/95"
                    : "text-apex-muted/55",
                ].join(" ")}
              >
                {currentPriceInr !== null && currentPriceInr !== undefined
                  ? `Now ${formatPrice(currentPriceInr)}`
                  : JOURNEY_COPY.currentPricePending}
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
            aria-valuenow={displayPct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={
              waitingForEntry
                ? `${symbol}: not in trade — live price on chart path`
                : `${symbol}: ${displayPct}% from entry to target`
            }
          >
            {showTradeProgress ? (
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
                    {targetReached ? "100%" : `${displayPct}%`}
                  </span>
                ) : null}
              </div>
            ) : null}

            {waitingForEntry && priceMarkerPct !== null ? (
              <span
                className="pointer-events-none absolute top-1/2 z-10 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-sky-100/90 bg-sky-400 shadow-[0_0_10px_rgba(56,189,248,0.55)]"
                style={{ left: `${priceMarkerPct}%` }}
                aria-hidden
              />
            ) : null}

            {targetReached ? (
              <span className="pointer-events-none absolute inset-0 flex items-center justify-center text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-50/95">
                Target met
              </span>
            ) : waitingForEntry ? (
              <span className="pointer-events-none absolute inset-0 flex items-center justify-center text-[10px] font-semibold uppercase tracking-[0.1em] text-apex-muted/70">
                {JOURNEY_COPY.waitBarLabel}
              </span>
            ) : null}
          </div>

          {waitingForEntry && !compact ? (
            <p className="mt-1 text-center text-[10px] leading-relaxed text-apex-muted/60">
              {JOURNEY_COPY.waitBarHint}
            </p>
          ) : null}

          {!pctInsideFill && showTradeProgress && displayPct > 0 && !targetReached ? (
            <p className="mt-1 text-center text-[10px] font-semibold tabular-nums text-apex-muted/80">
              {displayPct}%
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
          {timeTargetLabel ? (
            <p
              className={[
                "mt-0.5 text-[10px] tabular-nums leading-tight",
                timeOverdue ? "text-amber-300/90" : "text-apex-muted/65",
              ].join(" ")}
            >
              {timeTargetLabel}
            </p>
          ) : null}
          {timeRemainingLabel ? (
            <p
              className={[
                "text-[10px] tabular-nums",
                timeOverdue ? "text-amber-200/80" : "text-violet-200/70",
              ].join(" ")}
            >
              {timeRemainingLabel}
            </p>
          ) : null}
        </div>
      </div>

      {timeClamped !== null && timeTargetLabel ? (
        <div
          className={[
            "mt-2 grid items-center gap-x-3",
            compact
              ? "grid-cols-[minmax(5.5rem,6.5rem)_1fr_minmax(3.5rem,4.5rem)] sm:gap-x-4"
              : "grid-cols-[minmax(6rem,7.5rem)_1fr_minmax(4rem,5rem)] sm:gap-x-4",
          ].join(" ")}
        >
          <p className="text-[10px] text-apex-muted/55">Time</p>
          <div
            className="relative h-1.5 overflow-hidden rounded-full bg-black/45"
            role="progressbar"
            aria-valuenow={timeClamped}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${symbol} time progress`}
          >
            <div
              className={[
                "absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-[width] duration-500",
                timeOverdue
                  ? "from-amber-400/80 to-amber-500/80"
                  : "from-sky-400/70 to-violet-400/70",
              ].join(" ")}
              style={{ width: `${Math.max(timeClamped, timeClamped > 0 ? 6 : 0)}%` }}
            />
          </div>
          <p className="text-right text-[10px] tabular-nums text-apex-muted/60">
            {timeClamped}%
          </p>
        </div>
      ) : null}

      {waitPathInsight ? (
        <p className="mt-2 rounded-lg border border-amber-500/25 bg-amber-500/[0.06] px-3 py-2 text-[11px] leading-relaxed text-amber-100/90">
          {waitPathInsight.message}
        </p>
      ) : null}
    </div>
  );
}
