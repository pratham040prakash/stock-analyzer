"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import DecisionReceiptCard from "@/components/receipts/DecisionReceiptCard";
import ReceiptProofPanel from "@/components/receipts/ReceiptProofPanel";
import BrokerReconcilePanel from "@/components/review/BrokerReconcilePanel";
import MonthlyDoctorPanel from "@/components/review/MonthlyDoctorPanel";
import PlannedVsActualTable from "@/components/review/PlannedVsActualTable";
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
import type { MonthlyDoctorViewModel } from "@/types/monthlyDoctor";
import type {
  PlannedVsActualRow,
  PlannedVsActualSummary,
} from "@/types/plannedVsActual";

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

type ReviewTab = "weekly" | "monthly" | "receipts";

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

type PlannedResponse = {
  status: string;
  rows: PlannedVsActualRow[];
  summary: PlannedVsActualSummary;
};

type MonthlyResponse = {
  status: string;
  doctor: MonthlyDoctorViewModel;
};

export default function ReviewPageClient({ userName }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const highlightReceiptId = searchParams.get("receipt");
  const initialTab = searchParams.get("tab");
  const [tab, setTab] = useState<ReviewTab>(() => {
    if (initialTab === "monthly" || initialTab === "receipts") {
      return initialTab;
    }

    return "weekly";
  });
  const [history, setHistory] = useState<DisciplineHistoryEntry[]>([]);
  const [summary, setSummary] = useState<DisciplineHistorySummary>(
    EMPTY_SUMMARY,
  );
  const [receipts, setReceipts] = useState<DecisionReceiptRow[]>([]);
  const [plannedRows, setPlannedRows] = useState<PlannedVsActualRow[]>([]);
  const [monthlyDoctor, setMonthlyDoctor] = useState<MonthlyDoctorViewModel | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [monthlyLoading, setMonthlyLoading] = useState(false);
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

  const loadPlanned = useCallback(async () => {
    const response = await apiFetch("/api/review/planned?days=14", {
      cache: "no-store",
    });
    const data = await parseApiJson<PlannedResponse>(response, "Planned vs actual");

    if (response.ok && data?.rows) {
      setPlannedRows(data.rows);
    }
  }, []);

  const loadMonthly = useCallback(async () => {
    setMonthlyLoading(true);

    try {
      const response = await apiFetch("/api/review/monthly", {
        cache: "no-store",
      });
      const data = await parseApiJson<MonthlyResponse>(response, "Monthly doctor");

      if (response.ok && data?.doctor) {
        setMonthlyDoctor(data.doctor);
      }
    } finally {
      setMonthlyLoading(false);
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

    await Promise.all([
      loadHistory(),
      loadReceipts(),
      loadStreak(),
      loadPlanned(),
    ]);
  }, [loadHistory, loadPlanned, loadReceipts, loadStreak]);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      await reconcileBroker();
      await loadMonthly();
      setLoading(false);
    })();
  }, [loadMonthly, reconcileBroker]);

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

  useEffect(() => {
    const tabParam = searchParams.get("tab");

    if (tabParam === "monthly" || tabParam === "receipts" || tabParam === "weekly") {
      setTab(tabParam);
    }
  }, [searchParams]);

  const highlightedReceipt = useMemo(
    () => receipts.find((row) => row.id === highlightReceiptId) ?? null,
    [highlightReceiptId, receipts],
  );

  const selectTab = useCallback(
    (nextTab: ReviewTab) => {
      setTab(nextTab);
      const query = new URLSearchParams({ tab: nextTab });

      if (highlightReceiptId && nextTab === "receipts") {
        query.set("receipt", highlightReceiptId);
      }

      router.replace(`/app/review?${query.toString()}`, { scroll: false });
    },
    [highlightReceiptId, router],
  );

  const tabs: Array<{ key: ReviewTab; label: string }> = [
    { key: "weekly", label: "Weekly" },
    { key: "monthly", label: "Monthly" },
    { key: "receipts", label: "Receipts" },
  ];

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

      <div className="my-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => selectTab(item.key)}
            className={
              tab === item.key
                ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-100"
                : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
            }
          >
            {item.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading review…</p>
      ) : tab === "weekly" ? (
        <div className="space-y-4">
          <PlannedVsActualTable rows={plannedRows} />
          <WeeklyReviewStrip history={history} summary={summary} days={days} />
          <DisciplineHistoryStrip days={days} history={history} />
        </div>
      ) : tab === "monthly" ? (
        <MonthlyDoctorPanel
          doctor={
            monthlyDoctor ?? {
              built_at: new Date().toISOString(),
              month_label: "This month",
              headline: "Monthly review unavailable",
              summary: "Connect broker to run portfolio doctor.",
              concentration_warning: null,
              sacred_core_ok: true,
              allocation: null,
              health: [],
              action_items: [],
            }
          }
          loading={monthlyLoading}
        />
      ) : (
        <div className="space-y-3">
          {highlightedReceipt ? (
            <ReceiptProofPanel receipt={highlightedReceipt} />
          ) : null}
          {receipts.length === 0 ? (
            <p className="text-sm text-apex-muted/70">No receipts yet.</p>
          ) : (
            receipts.map((receipt) => (
              <DecisionReceiptCard
                key={receipt.id}
                receipt={receipt}
                onDismiss={dismissReceipt}
              />
            ))
          )}
        </div>
      )}
    </ApexShell>
  );
}
