"use client";

import type { AllocationPolicySummary } from "@/services/portfolio/allocationPolicy";
import type { PortfolioHealthSummaryViewModel } from "@/services/portfolio/buildPortfolioHealthSummary";
import type { SectorCapSummary } from "@/services/portfolio/sectorCapPolicy";

type Props = {
  allocation?: AllocationPolicySummary | null;
  health?: PortfolioHealthSummaryViewModel | null;
  sector?: SectorCapSummary | null;
  youngBook?: boolean;
};

const BUCKETS: Array<{
  key: keyof AllocationPolicySummary["targets"];
  label: string;
}> = [
  { key: "core", label: "Core" },
  { key: "tactical", label: "Tactical" },
  { key: "cash", label: "Cash" },
];

export default function PortfolioPolicyPanel({
  allocation,
  health,
  sector,
  youngBook = false,
}: Props) {
  if (!allocation && !health && !sector) {
    return null;
  }

  return (
    <section
      aria-label="How this sits vs policy"
      className="rounded-[28px] border border-white/[0.08] bg-white/[0.03] px-5 py-5"
    >
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-apex-muted/70">
        Vs policy
      </p>
      {health && !youngBook ? (
        <p className="mt-2 text-sm text-apex-muted/85">{health.headline}</p>
      ) : null}

      {allocation ? (
        <div className="mt-4 space-y-3">
          {BUCKETS.map((row) => {
            const actual = allocation.actual[row.key];
            const target = allocation.targets[row.key];
            return (
              <div key={row.key}>
                <div className="mb-1.5 flex items-baseline justify-between gap-3 text-xs">
                  <span className="text-apex-text/85">{row.label}</span>
                  <span className="tabular-nums text-apex-muted/75">
                    {actual.toFixed(0)}% · {target}%
                  </span>
                </div>
                <div className="relative h-1.5 rounded-full bg-white/[0.08]">
                  <div
                    className="h-full rounded-full bg-white/45"
                    style={{ width: `${Math.max(4, Math.min(100, actual))}%` }}
                  />
                  <span
                    aria-hidden
                    className="absolute top-1/2 h-3 w-px -translate-y-1/2 bg-white/80"
                    style={{
                      left: `${Math.max(2, Math.min(98, target))}%`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {youngBook ? (
        <p className="mt-4 text-xs leading-relaxed text-apex-muted/75">
          Cash is the third name until a setup confirms.
        </p>
      ) : sector ? (
        <p className="mt-4 text-xs leading-relaxed text-apex-muted/75">
          {sector.policy_note}
        </p>
      ) : null}
    </section>
  );
}
