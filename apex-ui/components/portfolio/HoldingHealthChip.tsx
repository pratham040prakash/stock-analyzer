"use client";

import type { HoldingHealthChip } from "@/services/portfolio/holdingHealth";

function tone(grade: HoldingHealthChip["grade"]): string {
  switch (grade) {
    case "Strong":
      return "border-emerald-500/25 bg-emerald-500/10 text-emerald-100";
    case "Watch":
      return "border-amber-500/25 bg-amber-500/10 text-amber-100";
    default:
      return "border-red-500/25 bg-red-500/10 text-red-100";
  }
}

export default function HoldingHealthChipView({ chip }: { chip: HoldingHealthChip }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-medium ${tone(chip.grade)}`}
      title={chip.reason}
    >
      {chip.symbol} · {chip.grade} · {chip.score}
    </span>
  );
}

export function HoldingHealthList({ chips }: { chips: HoldingHealthChip[] }) {
  if (chips.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Holding health
      </p>
      <div className="flex flex-wrap gap-2">
        {chips.map((chip) => (
          <HoldingHealthChipView key={chip.symbol} chip={chip} />
        ))}
      </div>
    </section>
  );
}
