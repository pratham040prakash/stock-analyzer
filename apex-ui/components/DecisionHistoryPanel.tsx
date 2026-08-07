"use client";

import type { DecisionHistoryEntry } from "@/types/decisionHistory";
import {
  decisionActionLabel,
  displayConfidencePercent,
  type DecisionActionType,
} from "@/types/decision";

type Props = {
  history: DecisionHistoryEntry[];
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

function historyLabel(entry: DecisionHistoryEntry): string {
  const action = decisionActionLabel(entry.action as DecisionActionType);
  const confidence = displayConfidencePercent(entry.confidence);
  if (entry.stock) {
    return `${action} ${entry.stock} (${confidence}%)`;
  }
  return `${action} (${confidence}%)`;
}

function actionTone(action: DecisionActionType): string {
  switch (action) {
    case "reduce":
      return "text-amber-300";
    case "buy":
      return "text-teal-300";
    case "explore":
      return "text-purple-300";
    case "wait":
      return "text-gray-300";
    default:
      return "text-blue-200";
  }
}

export default function DecisionHistoryPanel({ history }: Props) {
  if (history.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-5 space-y-4">
      <p className="text-xs text-gray-400 uppercase tracking-wider">
        Past 3 days decisions
      </p>
      <ul className="space-y-3">
        {history.map((entry) => (
          <li
            key={entry.date}
            className="flex items-center justify-between gap-4 border-b border-white/5 last:border-0 pb-3 last:pb-0"
          >
            <span className="text-sm text-gray-500 shrink-0">
              {formatHistoryDate(entry.date)}
            </span>
            <span
              className={`text-sm font-medium text-right ${actionTone(entry.action)}`}
            >
              {historyLabel(entry)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
