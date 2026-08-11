"use client";

import type { SectorCapSummary } from "@/services/portfolio/sectorCapPolicy";

type Props = {
  summary: SectorCapSummary;
  compact?: boolean;
  className?: string;
};

export default function SectorCapStrip({
  summary,
  compact = false,
  className = "",
}: Props) {
  if (summary.sectors.length === 0) {
    return null;
  }

  const tone = summary.breached
    ? "border-amber-500/25 bg-amber-500/10 text-amber-100/90"
    : summary.top_sector_pct >= summary.cap_pct - 5
      ? "border-amber-500/15 bg-amber-500/5 text-amber-100/85"
      : "border-apex-border/15 bg-white/[0.02] text-apex-text/85";

  return (
    <section
      aria-label="Sector concentration cap"
      className={`rounded-xl border px-4 py-3 text-xs ${tone} ${className}`.trim()}
    >
      <p className="font-medium text-apex-text/90">Sector cap</p>
      <p className="mt-1 leading-snug">{summary.policy_note}</p>
      {!compact ? (
        <ul className="mt-2 space-y-1 text-apex-muted/80">
          {summary.sectors.slice(0, 4).map((row) => (
            <li key={row.sector}>
              {row.sector} · {row.weight_pct.toFixed(1)}%
              {row.sector === summary.top_sector && summary.breached
                ? " · over cap"
                : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-apex-muted/75">
          Top sector {summary.top_sector} · {summary.top_sector_pct.toFixed(0)}% /{" "}
          {summary.cap_pct}% cap
        </p>
      )}
    </section>
  );
}
