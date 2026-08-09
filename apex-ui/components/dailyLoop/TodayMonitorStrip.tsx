"use client";

import { formatInr } from "@/lib/funds";
import type { OpenMonitorPosition } from "@/services/monitor/openPositions";

export type TodayMonitorStripProps = {
  positions: OpenMonitorPosition[];
  dayPnl?: number | null;
  loading?: boolean;
};

function stopStatusLabel(status: OpenMonitorPosition["stopStatus"]): string {
  if (status === "breached") {
    return "Stop breached — review in Zerodha";
  }

  if (status === "near") {
    return "Near stop — watch closely";
  }

  return "Above stop";
}

function stopStatusClass(status: OpenMonitorPosition["stopStatus"]): string {
  if (status === "breached") {
    return "text-amber-200/95";
  }

  if (status === "near") {
    return "text-amber-200/80";
  }

  return "text-emerald-200/90";
}

function MonitorRow({ position }: { position: OpenMonitorPosition }) {
  const pnlPositive = position.unrealizedPnl >= 0;

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
          {formatInr(position.unrealizedPnl)}
          <span className="text-xs text-apex-muted/70">
            {" "}
            ({pnlPositive ? "+" : ""}
            {position.pnlPct.toFixed(1)}%)
          </span>
        </p>
      </div>

      <p className="text-xs text-apex-muted/75">
        Entry {formatInr(position.entryPrice)} · Now {formatInr(position.currentPrice)}
      </p>

      <p className={`text-xs ${stopStatusClass(position.stopStatus)}`}>
        Stop {formatInr(position.stopLoss)} · {stopStatusLabel(position.stopStatus)}
        {position.stopStatus === "safe" && position.distanceToStopPct > 0 ? (
          <span className="text-apex-muted/65">
            {" "}
            · {position.distanceToStopPct.toFixed(1)}% above stop
          </span>
        ) : null}
      </p>
    </div>
  );
}

export default function TodayMonitorStrip({
  positions,
  dayPnl,
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
          Open position monitor
        </p>
        {dayPnl !== null && dayPnl !== undefined ? (
          <p
            className={
              dayPnl >= 0
                ? "text-xs text-emerald-200/90"
                : "text-xs text-amber-200/90"
            }
          >
            Day P&amp;L {dayPnl >= 0 ? "+" : ""}
            {formatInr(Math.round(dayPnl))}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        {positions.map((position) => (
          <MonitorRow key={position.id} position={position} />
        ))}
      </div>

      <p className="text-[11px] leading-snug text-apex-muted/60">
        Prices from Zerodha holdings. Stop levels from your APEX execution plan.
      </p>
    </div>
  );
}
