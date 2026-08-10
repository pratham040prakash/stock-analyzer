"use client";

import type {
  MonitorLiveTick,
  OpenMonitorPosition,
} from "@/services/monitor/openPositions";

export type TodayMonitorStripProps = {
  positions: OpenMonitorPosition[];
  dayPnl?: number | null;
  liveTicksById?: Record<string, MonitorLiveTick>;
  loading?: boolean;
};

function MonitorRow({
  position,
  liveTick,
}: {
  position: OpenMonitorPosition;
  liveTick?: MonitorLiveTick;
}) {
  const currentPrice = liveTick?.currentPrice ?? position.currentPrice;
  const unrealizedPnl = liveTick?.unrealizedPnl ?? position.unrealizedPnl;
  const pnlPct = liveTick?.pnlPct ?? position.pnlPct;
  const positionDayPnl = liveTick?.positionDayPnl;
  const pnlPositive = unrealizedPnl >= 0;
  const dayPositive =
    positionDayPnl !== null &&
    positionDayPnl !== undefined &&
    positionDayPnl >= 0;

  return (
    <div className="rounded-lg border border-apex-border/15 bg-white/[0.02] px-3 py-3 space-y-2">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-medium text-apex-text/90">
          {position.stock} · {position.quantity} shares
        </p>
        <p
          className={
            pnlPositive ? "text-sm text-emerald-200/90" : "text-sm text-amber-200/90"
          }
        >
          {pnlPositive ? "+" : ""}
          ₹{Math.abs(unrealizedPnl).toLocaleString("en-IN")}
          <span className="text-xs text-apex-muted/70">
            {" "}
            ({pnlPositive ? "+" : ""}
            {pnlPct.toFixed(1)}%)
          </span>
        </p>
      </div>

      <p className="text-xs text-apex-muted/75">
        Entry ₹{position.entryPrice.toLocaleString("en-IN")} · Now ₹
        {currentPrice.toLocaleString("en-IN")}
      </p>

      {positionDayPnl !== null && positionDayPnl !== undefined ? (
        <p
          className={
            dayPositive
              ? "text-[11px] text-emerald-200/75"
              : "text-[11px] text-amber-200/75"
          }
        >
          Today {dayPositive ? "+" : "−"}₹
          {Math.abs(positionDayPnl).toLocaleString("en-IN")}
        </p>
      ) : null}
    </div>
  );
}

export default function TodayMonitorStrip({
  positions,
  dayPnl,
  liveTicksById,
  loading = false,
}: TodayMonitorStripProps) {
  if (loading) {
    return (
      <div
        className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3"
        aria-label="Open position monitor"
      >
        <p className="text-xs text-apex-muted/70">Loading open positions…</p>
      </div>
    );
  }

  if (positions.length === 0) {
    return null;
  }

  return (
    <div
      className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3 space-y-3"
      aria-label="Open position monitor"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Open positions
        </p>
        {dayPnl !== null && dayPnl !== undefined ? (
          <p
            className={
              dayPnl >= 0
                ? "text-xs text-emerald-200/90"
                : "text-xs text-amber-200/90"
            }
          >
            Day P&amp;L {dayPnl >= 0 ? "+" : "−"}₹
            {Math.abs(dayPnl).toLocaleString("en-IN")}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        {positions.map((position) => (
          <MonitorRow
            key={position.id}
            position={position}
            liveTick={liveTicksById?.[position.id]}
          />
        ))}
      </div>

      <p className="text-[11px] leading-snug text-apex-muted/60">
        Live prices update every 5s during market hours · positions refresh after trades.
      </p>
    </div>
  );
}
