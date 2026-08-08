"use client";

import type { DecisionHistoryEntry } from "@/types/decisionHistory";
import {
  decisionActionLabel,
  type DecisionActionType,
} from "@/types/decision";
import { ApexBody, ApexCard, ApexEyebrow } from "@/components/ui/apex";

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
  if (entry.stock) {
    return `${action} ${entry.stock}`;
  }
  return action;
}

function actionTone(action: DecisionActionType): string {
  switch (action) {
    case "reduce":
    case "sell":
      return "text-red-300";
    case "buy":
      return "text-emerald-300";
    case "explore":
      return "text-blue-200";
    case "wait":
      return "text-apex-muted";
    default:
      return "text-apex-text";
  }
}

export default function DecisionHistoryPanel({ history }: Props) {
  if (history.length === 0) {
    return null;
  }

  return (
    <ApexCard hover={false} padding="compact">
      <ApexEyebrow className="mb-4">Recent decisions</ApexEyebrow>
      <ul className="space-y-3">
        {history.map((entry) => (
          <li
            key={entry.date}
            className="flex items-center justify-between gap-4 border-b border-apex-border pb-3 last:border-0 last:pb-0"
          >
            <ApexBody>{formatHistoryDate(entry.date)}</ApexBody>
            <span
              className={`text-[13px] font-medium text-right ${actionTone(entry.action)}`}
            >
              {historyLabel(entry)}
            </span>
          </li>
        ))}
      </ul>
    </ApexCard>
  );
}
