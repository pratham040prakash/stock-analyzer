"use client";

import type { MonthlyDoctorViewModel } from "@/types/monthlyDoctor";
import Link from "next/link";
import AllocationVsPolicy from "@/components/portfolio/AllocationVsPolicy";
import { HoldingHealthList } from "@/components/portfolio/HoldingHealthChip";

type Props = {
  doctor: MonthlyDoctorViewModel;
  loading?: boolean;
};

export default function MonthlyDoctorPanel({ doctor, loading }: Props) {
  if (loading) {
    return <p className="text-sm text-apex-muted/70">Loading monthly review…</p>;
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-blue-500/15 bg-blue-500/5 px-4 py-4 space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Portfolio doctor · {doctor.month_label}
        </p>
        <p className="text-lg font-medium text-apex-text/95">{doctor.headline}</p>
        <p className="text-sm text-apex-muted/85">{doctor.summary}</p>
        {doctor.concentration_warning ? (
          <p className="text-sm text-amber-100/85">{doctor.concentration_warning}</p>
        ) : null}
        <p className="text-xs text-apex-muted/70">
          Sacred core check · {doctor.sacred_core_ok ? "Within bounds" : "Review concentration"}
        </p>
      </section>

      {doctor.allocation ? (
        <AllocationVsPolicy allocation={doctor.allocation} />
      ) : null}

      {doctor.health.length > 0 ? (
        <HoldingHealthList chips={doctor.health} linkResearch />
      ) : null}

      {doctor.action_items.length > 0 ? (
        <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Action items
          </p>
          <ul className="space-y-1 text-sm text-apex-text/85">
            {doctor.action_items.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {doctor.allocation?.holdings?.[0]?.tradingsymbol ? (
        <Link
          href={`/app/research?symbol=${encodeURIComponent(doctor.allocation.holdings[0].tradingsymbol)}`}
          className="inline-flex text-sm text-blue-200/90 hover:text-blue-100"
        >
          Research top holding →
        </Link>
      ) : null}
    </div>
  );
}
