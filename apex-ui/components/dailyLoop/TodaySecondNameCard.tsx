"use client";

import Link from "next/link";
import type { SecondNameWatch } from "@/lib/dailyLoop/secondNameToday";

type Props = {
  watch: SecondNameWatch;
  kiteLine?: string;
};

export default function TodaySecondNameCard({ watch, kiteLine }: Props) {
  const bandLine =
    watch.triggerLabel && watch.killLabel
      ? `${watch.triggerLabel} · Drop below ${watch.killLabel}`
      : watch.triggerLabel;

  return (
    <section className="relative overflow-hidden rounded-[28px] border border-white/[0.08] bg-gradient-to-b from-violet-400/[0.08] to-transparent px-5 py-5 sm:px-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(167,139,250,0.14),transparent_46%)]" />

      <div className="relative">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-apex-muted/70">
          In Kite · {watch.eyebrow}
        </p>
        <p className="mt-1 text-lg font-semibold tracking-tight text-apex-text">
          {watch.symbol}
        </p>
      </div>

      <div className="relative mt-5 text-center">
        {watch.gapLabel ? (
          <p className="text-3xl font-semibold tracking-tight text-apex-text sm:text-4xl">
            {watch.gapLabel}
          </p>
        ) : watch.lastLabel ? (
          <p className="text-3xl font-semibold tracking-tight text-apex-text sm:text-4xl">
            {watch.lastLabel}
          </p>
        ) : null}
        {bandLine ? (
          <p className="mt-2 text-sm text-violet-100/85">{bandLine}</p>
        ) : null}
        {watch.lastLabel && watch.gapLabel ? (
          <p className="mt-1 text-xs text-apex-muted/70">Last {watch.lastLabel}</p>
        ) : null}
      </div>

      {kiteLine && (watch.dead || watch.through) ? (
        <p className="relative mt-5 text-sm leading-relaxed text-apex-text/90">
          {kiteLine}
        </p>
      ) : null}
      {watch.dead ? null : (
        <p className="relative mt-5 text-sm text-apex-muted/85">
          {watch.ticketLabel} → {watch.leftoverLabel}
        </p>
      )}
      {watch.whyLine ? (
        <p className="relative mt-2 text-sm text-apex-muted/75">{watch.whyLine}</p>
      ) : null}
      <Link
        href={`/app/research?symbol=${encodeURIComponent(watch.symbol)}`}
        className="relative mt-4 inline-flex text-xs text-apex-muted/70 underline-offset-2 hover:text-apex-text hover:underline"
      >
        Research {watch.symbol} →
      </Link>
    </section>
  );
}
