"use client";

import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import WeeklyReviewStrip from "@/components/dailyLoop/WeeklyReviewStrip";
import DisciplineHistoryStrip from "@/components/dailyLoop/DisciplineHistoryStrip";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { buildLastNIstDays } from "@/lib/dailyLoop/disciplineHistoryMerge";
import type {
  DecisionHistoryResponse,
  DisciplineHistoryEntry,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";
import { useCallback, useEffect, useState } from "react";

const EMPTY_SUMMARY: DisciplineHistorySummary = {
  wins: 0,
  losses: 0,
  open: 0,
  waitDays: 0,
  executedDays: 0,
  followedDays: 0,
};

type Props = {
  userName: string;
};

export default function ReviewPageClient({ userName }: Props) {
  const [history, setHistory] = useState<DisciplineHistoryEntry[]>([]);
  const [summary, setSummary] = useState<DisciplineHistorySummary>(
    EMPTY_SUMMARY,
  );
  const [loading, setLoading] = useState(true);

  const loadHistory = useCallback(async () => {
    setLoading(true);

    try {
      const response = await apiFetch("/api/decision/history?days=14", {
        cache: "no-store",
      });
      const data = await parseApiJson<DecisionHistoryResponse>(
        response,
        "Decision history",
      );

      if (response.ok && data) {
        setHistory(data.history ?? []);
        setSummary(data.summary ?? EMPTY_SUMMARY);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const days = buildLastNIstDays(14);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Weekly review</ApexTitle>
          <p className="text-sm text-apex-muted">
            Discipline and outcomes for {userName} — last two weeks.
          </p>
        </div>
      </header>

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading review…</p>
      ) : (
        <div className="space-y-4">
          <WeeklyReviewStrip history={history} summary={summary} days={days} />
          <DisciplineHistoryStrip days={days} history={history} />
        </div>
      )}
    </ApexShell>
  );
}
