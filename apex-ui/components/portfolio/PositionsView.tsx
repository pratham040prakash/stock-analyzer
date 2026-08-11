"use client";

import type { OpenMonitorPosition } from "@/services/monitor/openPositions";

function formatSigned(value: number): string {
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

export default function PositionsView({
  positions,
  loading = false,
}: {
  positions: OpenMonitorPosition[];
  loading?: boolean;
}) {
  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-3">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Open positions
      </p>
      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading positions…</p>
      ) : positions.length === 0 ? (
        <p className="text-sm text-apex-muted/70">No open intraday positions.</p>
      ) : (
        <div className="space-y-2">
          {positions.map((position) => (
            <div
              key={position.id}
              className="flex flex-wrap items-baseline justify-between gap-2 rounded-lg border border-apex-border/10 px-3 py-2"
            >
              <div>
                <p className="text-sm font-medium text-apex-text/90">
                  {position.stock} · {position.quantity}
                </p>
                <p className="text-xs text-apex-muted/70">
                  Stop {position.stopStatus} · {position.distanceToStopPct.toFixed(1)}% to stop
                </p>
              </div>
              <p
                className={
                  position.unrealizedPnl >= 0
                    ? "text-sm text-emerald-200/90"
                    : "text-sm text-amber-200/90"
                }
              >
                {formatSigned(position.unrealizedPnl)}
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
