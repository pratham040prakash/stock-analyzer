"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import DecisionReceiptCard from "@/components/receipts/DecisionReceiptCard";
import BrokerReconcilePanel from "@/components/review/BrokerReconcilePanel";
import WeeklyReviewHero from "@/components/review/WeeklyReviewHero";
import WeeklyReviewStrip from "@/components/dailyLoop/WeeklyReviewStrip";
import DisciplineHistoryStrip from "@/components/dailyLoop/DisciplineHistoryStrip";
import { ApexShell } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { buildLastNIstDays } from "@/lib/dailyLoop/disciplineHistoryMerge";
import { buildDisciplineProcessScore } from "@/services/review/disciplineScore";
import type {
  DecisionHistoryResponse,
  DisciplineHistoryEntry,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";
import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";

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

type ReceiptsResponse = {
  status: string;
  receipts: DecisionReceiptRow[];
};

type ReconcileResponse = {
  status: string;
  synced: boolean;
  message: string;
};

type StreakResponse = {
  status: string;
  streak?: { streakCount?: number };
};

export default function ReviewPageClient({ userName }: Props) {
  const [tab, setTab] = useState<"weekly" | "receipts">("weekly");
  const [history, setHistory] = useState<DisciplineHistoryEntry[]>([]);
  const [summary, setSummary] = useState<DisciplineHistorySummary>(
    EMPTY_SUMMARY,
  );
  const [receipts, setReceipts] = useState<DecisionReceiptRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [reconcileSynced, setReconcileSynced] = useState<boolean | null>(null);
  const [reconcileMessage, setReconcileMessage] = useState<string | null>(null);
  const [streakCount, setStreakCount] = useState(0);

  const loadHistory = useCallback(async () => {
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
  }, []);

  const loadStreak = useCallback(async () => {
    const response = await apiFetch("/api/discipline/streak", {
      cache: "no-store",
    });
    const data = await parseApiJson<StreakResponse>(response, "Discipline streak");

    if (response.ok && data?.streak) {
      setStreakCount(data.streak.streakCount ?? 0);
    }
  }, []);

  const loadReceipts = useCallback(async () => {
    const response = await apiFetch("/api/receipts?days=30", {
      cache: "no-store",
    });
    const data = await parseApiJson<ReceiptsResponse>(response, "Receipts");

    if (response.ok && data?.receipts) {
      setReceipts(data.receipts);
    }
  }, []);

  const reconcileBroker = useCallback(async () => {
    const response = await apiFetch("/api/review/reconcile", {
      method: "POST",
    });
    const data = await parseApiJson<ReconcileResponse>(response, "Reconcile");

    setReconcileSynced(data?.synced ?? false);
    if (data?.message) {
      setReconcileMessage(data.message);
    }

    await Promise.all([loadHistory(), loadReceipts(), loadStreak()]);
  }, [loadHistory, loadReceipts, loadStreak]);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      await reconcileBroker();
      setLoading(false);
    })();
  }, [reconcileBroker]);

  const processScore = useMemo(
    () => buildDisciplineProcessScore(summary, streakCount),
    [summary, streakCount],
  );

  const days = buildLastNIstDays(14);

  const dismissReceipt = useCallback(async (id: string) => {
    await apiFetch("/api/receipts", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    setReceipts((current) => current.filter((row) => row.id !== id));
  }, []);

  return (
    <ApexShell>
      <ApexSurfaceNav />
      <WeeklyReviewHero
        userName={userName}
        summary={summary}
        processScore={processScore}
        reconcileMessage={reconcileMessage}
      />

      <BrokerReconcilePanel
        synced={reconcileSynced}
        message={reconcileMessage}
        loading={loading}
        onRetry={() => void reconcileBroker()}
      />

      <div className="my-4 flex gap-2">
        <button
          type="button"
          onClick={() => setTab("weekly")}
          className={
            tab === "weekly"
              ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-100"
              : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
          }
        >
          Weekly
        </button>
        <button
          type="button"
          onClick={() => setTab("receipts")}
          className={
            tab === "receipts"
              ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-100"
              : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
          }
        >
          Receipts
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading review…</p>
      ) : tab === "weekly" ? (
        <div className="space-y-4">
          <WeeklyReviewStrip history={history} summary={summary} days={days} />
          <DisciplineHistoryStrip days={days} history={history} />
        </div>
      ) : receipts.length === 0 ? (
        <p className="text-sm text-apex-muted/70">No receipts yet.</p>
      ) : (
        <div className="space-y-3">
          {receipts.map((receipt) => (
            <DecisionReceiptCard
              key={receipt.id}
              receipt={receipt}
              onDismiss={dismissReceipt}
            />
          ))}
        </div>
      )}
    </ApexShell>
  );
}
