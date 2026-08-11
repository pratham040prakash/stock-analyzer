import type { MonthlyDoctorViewModel } from "@/types/monthlyDoctor";

export type MonthlyTrendLine = {
  label: string;
  value: string;
  direction: "up" | "down" | "flat";
};

export function buildMonthlyTrendLines(
  doctor: MonthlyDoctorViewModel,
  priorAligned: number,
  currentAligned: number,
  priorDeviated: number,
  currentDeviated: number,
): MonthlyTrendLine[] {
  const lines: MonthlyTrendLine[] = [];

  const alignedDelta = currentAligned - priorAligned;
  lines.push({
    label: "Plan alignment",
    value:
      alignedDelta === 0
        ? `${currentAligned} aligned days (flat vs last month)`
        : `${currentAligned} aligned days (${alignedDelta > 0 ? "+" : ""}${alignedDelta} vs last month)`,
    direction: alignedDelta > 0 ? "up" : alignedDelta < 0 ? "down" : "flat",
  });

  const deviatedDelta = currentDeviated - priorDeviated;
  lines.push({
    label: "Deviations",
    value:
      deviatedDelta === 0
        ? `${currentDeviated} deviation days (flat vs last month)`
        : `${currentDeviated} deviation days (${deviatedDelta > 0 ? "+" : ""}${deviatedDelta} vs last month)`,
    direction: deviatedDelta > 0 ? "down" : deviatedDelta < 0 ? "up" : "flat",
  });

  if (doctor.allocation) {
    lines.push({
      label: "Core drift",
      value: `${doctor.allocation.drift.core > 0 ? "+" : ""}${doctor.allocation.drift.core.toFixed(0)}% vs policy`,
      direction:
        Math.abs(doctor.allocation.drift.core) >= 10
          ? "down"
          : Math.abs(doctor.allocation.drift.core) <= 3
            ? "up"
            : "flat",
    });
  }

  return lines;
}

export function runMonthlyTrendsSelfCheck(): void {
  const lines = buildMonthlyTrendLines(
    {
      built_at: new Date().toISOString(),
      month_label: "Test",
      headline: "Test",
      summary: "Test",
      concentration_warning: null,
      sacred_core_ok: true,
      allocation: {
        targets: { core: 70, tactical: 20, cash: 10 },
        actual: { core: 65, tactical: 25, cash: 10 },
        drift: { core: 5, tactical: -2, cash: -3 },
        holdings: [],
        cash_available_inr: 0,
        policy_note: "Test",
      },
      health: [],
      action_items: [],
      trends: [],
    },
    2,
    4,
    1,
    0,
  );

  if (lines.length < 2) {
    throw new Error("Monthly trends self-check failed");
  }
}
