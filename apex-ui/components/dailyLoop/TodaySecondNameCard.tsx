"use client";

import Link from "next/link";
import type { SecondNameWatch } from "@/lib/dailyLoop/secondNameToday";

type Props = {
  watch: SecondNameWatch;
  kiteLine?: string;
};

function statusTone(watch: SecondNameWatch): string {
  if (watch.dead) {
    return "text-rose-200";
  }

  if (watch.through) {
    return "text-emerald-200";
  }

  return "text-white";
}

export default function TodaySecondNameCard({ watch, kiteLine }: Props) {
  const status = watch.dead ? "Lost" : watch.through ? "Through" : "Live";

  return (
    <section className="overflow-hidden rounded-[28px] border border-white/[0.12] bg-black/40 px-5 py-6 sm:px-6">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-apex-muted/70">
          {watch.eyebrow}
        </p>
        <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-apex-text/85">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              watch.dead
                ? "bg-rose-400"
                : watch.through
                  ? "bg-emerald-400"
                  : "bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,0.8)]"
            }`}
          />
          {status}
        </p>
      </div>

      <p className="mt-3 text-sm font-semibold tracking-[0.18em] text-apex-muted/80">
        {watch.symbol}
      </p>

      <div className="mt-6 text-center">
        {watch.gapLabel ? (
          <p
            className={`text-5xl font-semibold tabular-nums tracking-tight sm:text-6xl ${statusTone(watch)}`}
          >
            {watch.gapLabel}
          </p>
        ) : watch.lastLabel ? (
          <p className="text-5xl font-semibold tabular-nums tracking-tight text-white sm:text-6xl">
            {watch.lastLabel}
          </p>
        ) : null}
        {watch.lastLabel && watch.gapLabel ? (
          <p className="mt-2 text-xs tabular-nums text-apex-muted/70">
            Last {watch.lastLabel}
          </p>
        ) : null}
      </div>

      {watch.triggerLabel || watch.killLabel ? (
        <div className="mt-6 grid grid-cols-2 gap-3 border-y border-white/[0.08] py-4 text-sm">
          <div>
            <p className="text-[11px] uppercase tracking-[0.16em] text-apex-muted/65">
              Buy above
            </p>
            <p className="mt-1 font-medium tabular-nums text-apex-text">
              {watch.triggerLabel?.replace("Buy above ", "") ?? "—"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[11px] uppercase tracking-[0.16em] text-apex-muted/65">
              Drop below
            </p>
            <p className="mt-1 font-medium tabular-nums text-apex-text">
              {watch.killLabel ?? "—"}
            </p>
          </div>
        </div>
      ) : null}

      {kiteLine && (watch.dead || watch.through) ? (
        <p className="mt-4 text-sm leading-relaxed text-apex-text/90">{kiteLine}</p>
      ) : null}
      {watch.dead ? null : (
        <p className="mt-4 text-sm tabular-nums text-apex-text/90">
          {watch.ticketLabel} → {watch.leftoverLabel}
        </p>
      )}
      {watch.whyLine ? (
        <p className="mt-3 text-sm leading-relaxed text-apex-text/85">{watch.whyLine}</p>
      ) : null}
      <Link
        href={`/app/research?symbol=${encodeURIComponent(watch.symbol)}`}
        className="mt-4 inline-flex text-xs text-apex-muted/70 underline-offset-2 hover:text-apex-text hover:underline"
      >
        Research {watch.symbol} →
      </Link>
    </section>
  );
}
