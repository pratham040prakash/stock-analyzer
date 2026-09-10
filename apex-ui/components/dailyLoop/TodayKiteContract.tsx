"use client";

import type { TodayContract } from "@/lib/dailyLoop/todayContract";

type Props = {
  contract: TodayContract;
  compact?: boolean;
};

export default function TodayKiteContract({ contract, compact = false }: Props) {
  const headline =
    compact && contract.watchSymbol && contract.gapLabel
      ? `${contract.watchSymbol} · ${contract.gapLabel}`
      : contract.kiteLine;

  if (compact) {
    return (
      <section
        aria-label="Today's Kite rule"
        className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.06] px-4 py-3"
      >
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-emerald-100/70">
          Today
        </p>
        <p className="mt-1 text-base font-semibold tabular-nums leading-snug tracking-tight text-white">
          {headline}
        </p>
      </section>
    );
  }

  return (
    <section
      aria-label="Today's Kite rule"
      className="rounded-[28px] border border-emerald-400/20 bg-emerald-400/[0.07] px-5 py-5"
    >
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-emerald-100/70">
        In Kite today
      </p>
      <p className="mt-2 text-lg font-semibold leading-snug tracking-tight text-apex-text">
        {contract.kiteLine}
      </p>
    </section>
  );
}
