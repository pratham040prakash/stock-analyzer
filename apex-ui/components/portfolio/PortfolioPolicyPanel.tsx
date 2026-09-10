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
  if (youngBook || (!allocation && !health && !sector)) {
    return null;
  }

  return (
    <details className="rounded-[28px] border border-white/[0.08] bg-white/[0.03] px-5 py-4">
      <summary className="cursor-pointer select-none text-sm font-medium text-apex-text/90">
        How this sits vs policy
      </summary>

      <div className="mt-4 space-y-5">
        {health ? (
          <p className="text-sm text-apex-muted/85">{health.headline}</p>
        ) : null}

        {allocation ? (
          <div className="space-y-3">
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
                  <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.08]">
                    <div
                      className="h-full rounded-full bg-white/45"
                      style={{ width: `${Math.max(4, Math.min(100, actual))}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}

        {sector ? (
          <p className="text-xs leading-relaxed text-apex-muted/75">
            {sector.policy_note}
          </p>
        ) : null}
      </div>
    </details>
  );
}
