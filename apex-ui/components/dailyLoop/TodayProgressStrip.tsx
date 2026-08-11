"use client";

import { getDisciplineInterpretation } from "@/lib/dailyLoop/disciplineCopy";
import { formatInr } from "@/lib/funds";

export type TodayProgressStripProps = {
  dayPnl?: number | null;
  openPnlPending?: boolean;
  sessionExpired?: boolean;
  trustScore: number;
  trustDelta: number;
  streakCount: number;
  streakMessage: string;
};

function formatDayPnl(value: number): string {
  const rounded = Math.round(value);
  const prefix = rounded > 0 ? "+" : "";
  return `${prefix}${formatInr(rounded)}`;
}

function TrustDelta({ delta }: { delta: number }) {
  if (delta > 0) {
    return <span className="text-emerald-300/90">↑ {delta}</span>;
  }

  if (delta < 0) {
    return <span className="text-amber-200/90">↓ {Math.abs(delta)}</span>;
  }

  return <span className="text-apex-muted/70">—</span>;
}

export default function TodayProgressStrip({
  dayPnl,
  openPnlPending = false,
  sessionExpired = false,
  trustScore,
  trustDelta,
  streakCount,
  streakMessage,
}: TodayProgressStripProps) {
  const dayKnown = dayPnl !== null && dayPnl !== undefined && Number.isFinite(dayPnl);
  const disciplineLine = getDisciplineInterpretation(trustScore);

  return (
    <div
      className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3"
      aria-label="Today's progress"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Open P&amp;L
          </p>
          {dayKnown ? (
            <p
              className={[
                "mt-1 text-xl font-semibold tabular-nums tracking-tight",
                (dayPnl ?? 0) >= 0 ? "text-emerald-300/95" : "text-amber-200/95",
              ].join(" ")}
            >
              {formatDayPnl(dayPnl ?? 0)}
            </p>
          ) : sessionExpired ? (
            <p className="mt-1 text-sm text-amber-200/90">
              Session expired —{" "}
              <a href="/api/zerodha/login" className="underline underline-offset-2">
                reconnect Zerodha
              </a>
            </p>
          ) : openPnlPending ? (
            <p className="mt-1 text-sm text-apex-muted/70">Open P&amp;L syncing…</p>
          ) : (
            <p className="mt-1 text-sm text-apex-muted/70">No open positions</p>
          )}
        </div>

        <div className="text-right">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Discipline
          </p>
          <div className="mt-1 flex items-baseline justify-end gap-2">
            <p className="text-xl font-semibold tabular-nums text-apex-text">
              {trustScore}
            </p>
            <p className="text-sm">
              <TrustDelta delta={trustDelta} />
            </p>
          </div>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-apex-muted/75">
        <span>
          Streak: {streakCount} day{streakCount === 1 ? "" : "s"}
        </span>
        <span>{disciplineLine}</span>
        <span>{streakMessage}</span>
      </div>
    </div>
  );

}
