"use client";

import type { StarterBookHoldLines } from "@/lib/dailyLoop/firstBuyToday";

type Props = {
  lines: StarterBookHoldLines;
  hideCashFork?: boolean;
  compact?: boolean;
};

function toneClass(value: number | null): string {
  if (value === null || Math.abs(value) < 0.5) {
    return "text-apex-text";
  }

  return value > 0 ? "text-emerald-200" : "text-rose-200";
}

function badgeClass(value: number | null): string {
  if (value === null || Math.abs(value) < 0.5) {
    return "border-white/10 bg-white/[0.06] text-apex-text";
  }

  return value > 0
    ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-100"
    : "border-rose-400/25 bg-rose-400/10 text-rose-100";
}

function lastMarkPercent(pct: number | null): number {
  if (pct === null || !Number.isFinite(pct)) {
    return 50;
  }

  return Math.max(8, Math.min(92, 50 + pct * 8));
}

export default function TodayStarterHoldCard({
  lines,
  hideCashFork = false,
  compact = false,
}: Props) {
  const mark = lastMarkPercent(lines.vsBuyPct);

  return (
    <section
      className={`relative overflow-hidden border border-white/[0.08] bg-gradient-to-b from-sky-400/[0.08] to-transparent ${
        compact ? "rounded-2xl px-4 py-4" : "rounded-[28px] px-5 py-5 sm:px-6"
      }`}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(52,211,153,0.12),transparent_42%)]" />

      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-apex-muted/70">
            {lines.symbol}
          </p>
          <p className="mt-1 text-sm text-apex-muted/85">{lines.sharesLabel}</p>
        </div>
        {lines.dayPnlLabel ? (
          <p
            className={`rounded-full border px-3 py-1 text-[11px] font-medium ${badgeClass(lines.dayPnlInr)}`}
          >
            {lines.dayPnlLabel}
          </p>
        ) : null}
      </div>

      <div className={`relative text-center ${compact ? "mt-4" : "mt-6"}`}>
        {lines.lastLabel ? (
          <p
            className={`font-semibold tracking-tight ${
              compact ? "text-3xl" : "text-4xl sm:text-5xl"
            } ${toneClass(lines.vsBuyInr)}`}
          >
            {lines.lastLabel}
          </p>
        ) : (
          <p className="text-lg font-medium text-apex-text">{lines.position}</p>
        )}
        {lines.vsBuyLabel ? (
          <p className={`mt-2 text-sm ${toneClass(lines.vsBuyInr)}`}>{lines.vsBuyLabel}</p>
        ) : null}
      </div>

      <div className={`relative ${compact ? "mt-4" : "mt-6"}`}>
        <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.08]">
          <div
            className="h-full w-1.5 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.35)]"
            style={{ marginLeft: `calc(${mark}% - 3px)` }}
          />
        </div>
        <div className="mt-3 flex items-center justify-between gap-3 text-xs text-apex-muted/80">
          <span>{lines.avgLabel ?? "Your buy"}</span>
          {lines.stopLabel ? <span>{lines.stopLabel}</span> : null}
          {lines.holdLabel ? <span>Hold {lines.holdLabel}</span> : null}
        </div>
      </div>

      {!hideCashFork && (lines.cashLabel || lines.next) ? (
        <div className="relative mt-5 rounded-2xl border border-sky-300/15 bg-sky-400/[0.08] px-4 py-3">
          {lines.nextEyebrow ? (
            <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-sky-100/70">
              {lines.nextEyebrow}
            </p>
          ) : null}
          {lines.cashLabel ? (
            <p className="mt-1 text-xl font-semibold tracking-tight text-apex-text">
              {lines.cashLabel}
            </p>
          ) : null}
          {lines.next ? (
            <p className="mt-1 text-sm leading-relaxed text-apex-muted/85">{lines.next}</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
