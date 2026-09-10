"use client";

import type { TodayContract } from "@/lib/dailyLoop/todayContract";

type Props = {
  contract: TodayContract;
};

export default function TodayKiteContract({ contract }: Props) {
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
      <p className="mt-2 text-sm leading-relaxed text-apex-muted/85">
        {contract.rule}
      </p>
    </section>
  );
}
