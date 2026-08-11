"use client";

import type { PlannedVsActualRow } from "@/types/plannedVsActual";

function statusTone(status: PlannedVsActualRow["status"]): string {
  switch (status) {
    case "aligned":
    case "wait_ok":
      return "text-emerald-200/90";
    case "deviated":
      return "text-amber-200/90";
    default:
      return "text-apex-muted/80";
  }
}

export default function PlannedVsActualTable({ rows }: { rows: PlannedVsActualRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-apex-muted/70">
        No planned vs actual rows yet — log decisions and connect broker.
      </p>
    );
  }

  return (
    <section
      aria-label="Planned vs actual"
      className="rounded-xl border border-apex-border/15 bg-white/[0.02] overflow-hidden"
    >
      <div className="px-4 py-3 border-b border-apex-border/10">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Planned vs actual
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-xs">
          <thead className="text-apex-muted/70">
            <tr>
              <th className="px-4 py-2 font-medium">Date</th>
              <th className="px-4 py-2 font-medium">Symbol</th>
              <th className="px-4 py-2 font-medium">Planned</th>
              <th className="px-4 py-2 font-medium">Actual</th>
              <th className="px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.date} className="border-t border-apex-border/10">
                <td className="px-4 py-2 text-apex-text/85">{row.date}</td>
                <td className="px-4 py-2 text-apex-text/85">{row.symbol ?? "—"}</td>
                <td className="px-4 py-2 capitalize text-apex-muted/85">
                  {row.planned_action}
                </td>
                <td className="px-4 py-2 capitalize text-apex-muted/85">
                  {row.actual_action ?? "—"}
                </td>
                <td className={`px-4 py-2 ${statusTone(row.status)}`}>
                  {row.status_label}
                  {row.pnl !== null ? ` · ₹${row.pnl.toLocaleString("en-IN")}` : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
