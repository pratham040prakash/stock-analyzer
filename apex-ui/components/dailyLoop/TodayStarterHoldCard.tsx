"use client";

import { useState } from "react";
import type { StarterBookHoldLines } from "@/lib/dailyLoop/firstBuyToday";

type Props = {
  lines: StarterBookHoldLines;
  hideCashFork?: boolean;
  compact?: boolean;
  yourCutInr?: number | null;
  cutSaving?: boolean;
  onSaveCut?: (cutInr: number) => void;
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

function YourCutField({
  yourCutInr,
  cutSaving,
  onSaveCut,
}: {
  yourCutInr?: number | null;
  cutSaving?: boolean;
  onSaveCut?: (cutInr: number) => void;
}) {
  const [draft, setDraft] = useState(
    yourCutInr && yourCutInr > 0 ? String(yourCutInr) : "",
  );

  if (!onSaveCut) {
    return null;
  }

  return (
    <form
      className="mt-3 flex items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        const cut = Number(draft.replace(/,/g, ""));
        if (!Number.isFinite(cut) || cut <= 0) {
          return;
        }
        onSaveCut(Math.round(cut));
      }}
    >
      <input
        type="text"
        inputMode="decimal"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        placeholder="Your line ₹"
        className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-apex-text outline-none placeholder:text-apex-muted/50"
        aria-label="Your hold line"
      />
      <button
        type="submit"
        disabled={cutSaving}
        className="shrink-0 rounded-xl border border-white/15 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-apex-text disabled:opacity-50"
      >
        {cutSaving ? "Saving" : "Set"}
      </button>
    </form>
  );
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
  yourCutInr = null,
  cutSaving = false,
  onSaveCut,
}: Props) {
  const mark = lastMarkPercent(lines.vsBuyPct);
  const showMark =
    !compact &&
    lines.vsBuyPct !== null &&
    Number.isFinite(lines.vsBuyPct) &&
    Math.abs(lines.vsBuyPct) >= 1;

  if (compact) {
    return (
      <section className="rounded-2xl border border-white/[0.10] bg-black/30 px-4 py-3.5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold tracking-[0.14em] text-white">
              {lines.symbol}
            </p>
            <p className="mt-1 text-xs tabular-nums text-apex-muted/80">
              {lines.sharesLabel}
            </p>
            <p className="mt-1 text-xs tabular-nums text-apex-muted/65">
              {lines.avgLabel ?? "Your buy"}
            </p>
          </div>
          <div className="text-right">
            {lines.lastLabel ? (
              <p
                className={`text-2xl font-semibold tabular-nums tracking-tight ${toneClass(lines.vsBuyInr)}`}
              >
                {lines.lastLabel}
              </p>
            ) : (
              <p className="text-sm font-medium text-apex-text">{lines.position}</p>
            )}
            {lines.vsBuyLabel ? (
              <p className={`mt-1 text-xs tabular-nums ${toneClass(lines.vsBuyInr)}`}>
                {lines.vsBuyLabel}
              </p>
            ) : null}
          </div>
        </div>
        {lines.holdRule ? (
          <p
            className={`mt-3 text-xs ${
              lines.ruleBroken ? "text-rose-200" : "text-apex-muted/75"
            }`}
          >
            {lines.holdRule}
          </p>
        ) : null}
        <YourCutField
          yourCutInr={yourCutInr}
          cutSaving={cutSaving}
          onSaveCut={onSaveCut}
        />
      </section>
    );
  }

  return (
    <section className="relative overflow-hidden rounded-[28px] border border-white/[0.08] bg-gradient-to-b from-sky-400/[0.08] to-transparent px-5 py-5 sm:px-6">
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

      <div className="relative mt-6 text-center">
        {lines.lastLabel ? (
          <p className={`text-4xl font-semibold tracking-tight sm:text-5xl ${toneClass(lines.vsBuyInr)}`}>
            {lines.lastLabel}
          </p>
        ) : (
          <p className="text-lg font-medium text-apex-text">{lines.position}</p>
        )}
        {lines.vsBuyLabel ? (
          <p className={`mt-2 text-sm ${toneClass(lines.vsBuyInr)}`}>{lines.vsBuyLabel}</p>
        ) : null}
      </div>

      <div className="relative mt-6">
        {showMark ? (
          <div className="mb-3 h-1.5 overflow-hidden rounded-full bg-white/[0.08]">
            <div
              className="h-full w-1.5 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.35)]"
              style={{ marginLeft: `calc(${mark}% - 3px)` }}
            />
          </div>
        ) : null}
        <div className="flex items-center justify-between gap-3 text-xs text-apex-muted/80">
          <span>{lines.avgLabel ?? "Your buy"}</span>
          {lines.stopLabel ? <span>{lines.stopLabel}</span> : null}
          {lines.holdLabel ? <span>Hold {lines.holdLabel}</span> : null}
        </div>
        <YourCutField
          yourCutInr={yourCutInr}
          cutSaving={cutSaving}
          onSaveCut={onSaveCut}
        />
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
