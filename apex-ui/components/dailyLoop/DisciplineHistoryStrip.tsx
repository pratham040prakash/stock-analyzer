"use client";

import type {
  DisciplineHistoryEntry,
} from "@/types/decisionHistory";

type Props = {
  days: string[];
  history: DisciplineHistoryEntry[];
};

function shortDayLabel(dateKey: string): string {
  const date = new Date(`${dateKey}T00:00:00Z`);

  return date.toLocaleDateString("en-IN", {
    weekday: "short",
    timeZone: "UTC",
  }).slice(0, 3);
}

function resolveDayStatus(
  dateKey: string,
  history: DisciplineHistoryEntry[],
): DisciplineHistoryEntry["outcome"] | "empty" {
  const entries = history.filter((entry) => entry.date === dateKey);

  if (entries.length === 0) {
    return "empty";
  }

  if (entries.some((entry) => entry.outcome === "loss")) {
    return "loss";
  }

  if (entries.some((entry) => entry.outcome === "win")) {
    return "win";
  }

  if (entries.some((entry) => entry.outcome === "open")) {
    return "open";
  }

  if (entries.some((entry) => entry.outcome === "followed")) {
    return "followed";
  }

  if (entries.some((entry) => entry.outcome === "wait")) {
    return "wait";
  }

  if (entries.some((entry) => entry.outcome === "hold")) {
    return "hold";
  }

  return entries[0]?.outcome ?? "none";
}

function statusClass(status: ReturnType<typeof resolveDayStatus>): string {
  if (status === "win") {
    return "border-emerald-400/35 bg-emerald-500/15 text-emerald-200/95";
  }

  if (status === "loss") {
    return "border-amber-400/35 bg-amber-500/15 text-amber-200/95";
  }

  if (status === "open") {
    return "border-blue-300/30 bg-blue-500/10 text-blue-100/90";
  }

  if (status === "followed") {
    return "border-teal-300/35 bg-teal-500/15 text-teal-100/95";
  }

  if (status === "wait" || status === "hold") {
    return "border-apex-border/25 bg-white/[0.03] text-apex-muted/80";
  }

  if (status === "none") {
    return "border-apex-border/20 bg-white/[0.02] text-apex-muted/70";
  }

  return "border-apex-border/15 bg-transparent text-apex-muted/45";
}

export default function DisciplineHistoryStrip({ days, history }: Props) {
  return (
    <div aria-label="Seven day discipline strip">
      <div className="grid grid-cols-7 gap-1.5">
        {days.map((day) => {
          const status = resolveDayStatus(day, history);

          return (
            <div key={day} className="text-center">
              <div
                className={[
                  "mx-auto flex h-8 w-8 items-center justify-center rounded-full border text-[11px] font-semibold",
                  statusClass(status),
                ].join(" ")}
                title={`${day} · ${status}`}
              >
                {shortDayLabel(day).charAt(0)}
              </div>
              <p className="mt-1 text-[10px] uppercase tracking-wide text-apex-muted/55">
                {shortDayLabel(day)}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
