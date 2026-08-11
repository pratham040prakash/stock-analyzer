"use client";

import type { AllocationPolicySummary } from "@/services/portfolio/allocationPolicy";

export default function AllocationVsPolicy({
  allocation,
}: {
  allocation: AllocationPolicySummary;
}) {
  const rows: Array<{
    key: keyof AllocationPolicySummary["targets"];
    label: string;
  }> = [
    { key: "core", label: "Core" },
    { key: "tactical", label: "Tactical" },
    { key: "cash", label: "Cash" },
  ];

  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-3">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Allocation vs policy
        </p>
        <p className="text-xs text-apex-muted/75">{allocation.policy_note}</p>
      </div>
      <div className="space-y-2">
        {rows.map((row) => (
          <div
            key={row.key}
            className="flex items-center justify-between gap-3 text-sm"
          >
            <span className="text-apex-text/85">{row.label}</span>
            <span className="text-apex-muted/80">
              {allocation.actual[row.key].toFixed(1)}% / target{" "}
              {allocation.targets[row.key]}%
              <span
                className={
                  Math.abs(allocation.drift[row.key]) > 5
                    ? " text-amber-200/85"
                    : " text-apex-muted/60"
                }
              >
                {" "}
                ({allocation.drift[row.key] > 0 ? "+" : ""}
                {allocation.drift[row.key]}%)
              </span>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
