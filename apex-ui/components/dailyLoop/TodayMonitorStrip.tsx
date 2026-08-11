"use client";

import type {
  MonitorLiveTick,
  OpenMonitorPosition,
} from "@/services/monitor/openPositions";

export type TodayMonitorStripProps = {
  positions: OpenMonitorPosition[];
  openPnl?: number | null;
  liveTicksById?: Record<string, MonitorLiveTick>;
  loading?: boolean;
  showWhenEmpty?: boolean;
};

function formatSignedPnl(value: number): string {
  const abs = Math.abs(value).toLocaleString("en-IN", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  if (value > 0) {
    return `+₹${abs}`;
  }
  if (value < 0) {
    return `−₹${abs}`;
  }
  return `₹${abs}`;
}

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
  const pnlPositive = unrealizedPnl >= 0;

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
          {formatSignedPnl(unrealizedPnl)}
          <span className="text-xs text-apex-muted/70">
            {" "}
            ({pnlPositive ? "+" : ""}
            {pnlPct.toFixed(1)}%)
          </span>
        </p>
      </div>

      <p className="text-xs text-apex-muted/75">
        Avg ₹{position.entryPrice.toLocaleString("en-IN")} · LTP ₹
        {currentPrice.toLocaleString("en-IN")}
      </p>
    </div>
  );
}

export default function TodayMonitorStrip({
  positions,
  openPnl,
  liveTicksById,
  loading = false,
  showWhenEmpty = false,
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
    if (!showWhenEmpty) {
      return null;
    }

    return (
      <div
        className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3"
        aria-label="Open position monitor"
      >
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Open positions
        </p>
        <p className="mt-2 text-xs text-apex-muted/70">
          No APEX-tracked open positions yet. After you buy through Today, they
          show here with live Zerodha P&amp;L.
        </p>
      </div>
    );
  }

  const headerPnl =
    openPnl ??
    positions.reduce((sum, position) => sum + position.unrealizedPnl, 0);

  return (
    <div
      className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-3 space-y-3"
      aria-label="Open position monitor"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Open positions
        </p>
        {headerPnl !== null && headerPnl !== undefined ? (
          <p
            className={
              headerPnl >= 0
                ? "text-xs text-emerald-200/90"
                : "text-xs text-amber-200/90"
            }
          >
            Open P&amp;L {formatSignedPnl(headerPnl)} · APEX-tracked
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
        Matches Zerodha Positions P&amp;L (LTP − avg) · APEX-tracked only · updates every 5s.
      </p>
    </div>
  );
}
