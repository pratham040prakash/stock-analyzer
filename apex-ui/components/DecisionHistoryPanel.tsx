"use client";

import DisciplineHistoryStrip, {
  formatDisciplineSummary,
} from "@/components/dailyLoop/DisciplineHistoryStrip";
import type {
  DisciplineHistoryEntry,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";
import {
  decisionActionLabel,
  type DecisionActionType,
} from "@/types/decision";
import { formatInr } from "@/lib/funds";
import { ApexBody, ApexCard, ApexEyebrow } from "@/components/ui/apex";

type Props = {
  history: DisciplineHistoryEntry[];
  summary: DisciplineHistorySummary;
  days: string[];
};

function formatHistoryDate(date: string): string {
  const entryDate = new Date(`${date}T00:00:00Z`);
  const today = new Date();
  const todayUtc = new Date(
    Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()),
  );
  const yesterdayUtc = new Date(todayUtc);
  yesterdayUtc.setUTCDate(yesterdayUtc.getUTCDate() - 1);

  if (entryDate.getTime() === todayUtc.getTime()) {
    return "Today";
  }

  if (entryDate.getTime() === yesterdayUtc.getTime()) {
    return "Yesterday";
  }

  return entryDate.toLocaleDateString("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

function historyLabel(entry: DisciplineHistoryEntry): string {
  const action = decisionActionLabel(entry.action as DecisionActionType);

  if (entry.stock) {
    return `${action} ${entry.stock}`;
  }

  return action;
}

function outcomeTone(outcome: DisciplineHistoryEntry["outcome"]): string {
  switch (outcome) {
    case "win":
      return "text-emerald-300/95";
    case "loss":
      return "text-amber-200/95";
    case "open":
      return "text-blue-100/90";
    case "wait":
    case "hold":
      return "text-apex-muted/80";
    default:
      return "text-apex-muted/70";
  }
}

function HistoryRow({ entry }: { entry: DisciplineHistoryEntry }) {
  return (
    <li className="border-b border-apex-border pb-3 last:border-0 last:pb-0">
      <div className="flex items-start justify-between gap-4">
        <div>
          <ApexBody>{formatHistoryDate(entry.date)}</ApexBody>
          <p className="mt-1 text-[13px] font-medium text-apex-text/90">
            {historyLabel(entry)}
          </p>
          {entry.source === "executed" ? (
            <p className="mt-0.5 text-[11px] uppercase tracking-wide text-apex-muted/55">
              Executed on Zerodha
            </p>
          ) : null}
        </div>
        <div className="text-right">
          <p className={`text-[13px] font-medium ${outcomeTone(entry.outcome)}`}>
            {entry.outcomeLabel}
          </p>
          {entry.pnl !== null &&
          entry.pnl !== undefined &&
          entry.outcome !== "open" ? (
            <p className={`mt-0.5 text-xs tabular-nums ${outcomeTone(entry.outcome)}`}>
              {entry.pnl >= 0 ? "+" : ""}
              {formatInr(entry.pnl)}
            </p>
          ) : null}
        </div>
      </div>
    </li>
  );
}

export default function DecisionHistoryPanel({
  history,
  summary,
  days,
}: Props) {
  return (
    <ApexCard hover={false} padding="compact">
      <ApexEyebrow className="mb-1">Last 7 days</ApexEyebrow>
      <p className="mb-4 text-sm text-apex-muted/75">
        {formatDisciplineSummary(summary)}
      </p>

      <DisciplineHistoryStrip days={days} history={history} />

      {history.length === 0 ? (
        <div className="mt-4 rounded-lg border border-apex-border/15 bg-white/[0.02] px-3 py-4">
          <p className="text-sm font-medium text-apex-text/90">
            No discipline history yet
          </p>
          <p className="mt-1 text-sm leading-snug text-apex-muted/75">
            Executed trades and wait decisions appear here once you act on Today.
          </p>
        </div>
      ) : (
        <ul className="mt-4 space-y-3 border-t border-apex-border/15 pt-4">
          {history.map((entry, index) => (
            <HistoryRow
              key={`${entry.date}:${entry.stock ?? "none"}:${entry.action}:${index}`}
              entry={entry}
            />
          ))}
        </ul>
      )}
    </ApexCard>
  );
}
