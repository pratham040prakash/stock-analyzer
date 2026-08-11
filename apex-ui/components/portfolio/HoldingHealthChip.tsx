"use client";

import Link from "next/link";
import { useState } from "react";
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

function HoldingHealthChipView({
  chip,
  linkResearch,
}: {
  chip: HoldingHealthChip;
  linkResearch?: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <span className="inline-flex flex-col gap-1">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-medium ${tone(chip.grade)}`}
      >
        {chip.symbol} · {chip.grade} · {chip.score}
      </button>
      {open ? (
        <span className="max-w-[16rem] rounded-lg border border-apex-border/15 bg-black/40 px-2 py-1 text-[11px] text-apex-muted/85">
          {chip.reason}
          {linkResearch ? (
            <>
              {" "}
              <Link
                href={`/app/research?symbol=${encodeURIComponent(chip.symbol)}`}
                className="text-blue-200/90 hover:text-blue-100"
              >
                Research →
              </Link>
            </>
          ) : null}
        </span>
      ) : null}
    </span>
  );
}

export function HoldingHealthList({
  chips,
  linkResearch,
}: {
  chips: HoldingHealthChip[];
  linkResearch?: boolean;
}) {
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
          <HoldingHealthChipView
            key={chip.symbol}
            chip={chip}
            linkResearch={linkResearch}
          />
        ))}
      </div>
    </section>
  );
}

export default HoldingHealthChipView;
