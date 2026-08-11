"use client";

import Link from "next/link";
import type { AllocationPolicySummary } from "@/services/portfolio/allocationPolicy";

export default function AllocationHoldingsDrift({
  allocation,
}: {
  allocation: AllocationPolicySummary;
}) {
  const rows = allocation.holdings
    .slice()
    .sort((a, b) => Math.abs(b.drift_pct) - Math.abs(a.drift_pct))
    .slice(0, 8);

  if (rows.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Holding drift vs policy
      </p>
      <ul className="space-y-2">
        {rows.map((row) => (
          <li
            key={row.tradingsymbol}
            className="flex flex-wrap items-center justify-between gap-2 text-sm"
          >
            <Link
              href={`/app/research?symbol=${encodeURIComponent(row.tradingsymbol)}`}
              className="font-medium text-apex-text/90 hover:text-blue-100"
            >
              {row.tradingsymbol}
            </Link>
            <span className="text-xs text-apex-muted/80">
              {row.allocation_pct.toFixed(1)}% · {row.bucket} · drift{" "}
              <span
                className={
                  Math.abs(row.drift_pct) > 5
                    ? "text-amber-200/85"
                    : "text-apex-muted/60"
                }
              >
                {row.drift_pct > 0 ? "+" : ""}
                {row.drift_pct}%
              </span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
