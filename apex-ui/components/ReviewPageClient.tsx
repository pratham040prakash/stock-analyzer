"use client";

import { useCallback, useEffect, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import WeeklyReviewStrip from "@/components/dailyLoop/WeeklyReviewStrip";
import DisciplineHistoryStrip from "@/components/dailyLoop/DisciplineHistoryStrip";
import DecisionReceipt from "@/components/dailyLoop/DecisionReceipt";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { buildLastNIstDays } from "@/lib/dailyLoop/disciplineHistoryMerge";
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

export default function ReviewPageClient({ userName }: Props) {
  const [tab, setTab] = useState<"weekly" | "receipts">("weekly");
  const [history, setHistory] = useState<DisciplineHistoryEntry[]>([]);
  const [summary, setSummary] = useState<DisciplineHistorySummary>(
    EMPTY_SUMMARY,
  );
  const [receipts, setReceipts] = useState<DecisionReceiptRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [reconcileMessage, setReconcileMessage] = useState<string | null>(null);
  const [processScore, setProcessScore] = useState<number | null>(null);

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
      const followed = data.summary?.followedDays ?? 0;
      const waitDays = data.summary?.waitDays ?? 0;
      const total = Math.max(1, followed + waitDays + (data.summary?.executedDays ?? 0));
      setProcessScore(Math.round(((followed / total) * 55 + (waitDays / total) * 25)));
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

    if (data?.message) {
      setReconcileMessage(data.message);
    }

    await Promise.all([loadHistory(), loadReceipts()]);
  }, [loadHistory, loadReceipts]);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      await reconcileBroker();
      setLoading(false);
    })();
  }, [reconcileBroker]);

  const days = buildLastNIstDays(14);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Weekly review</ApexTitle>
          <p className="text-sm text-apex-muted">
            Discipline, receipts, and broker reconcile for {userName}.
          </p>
          {processScore !== null ? (
            <p className="text-xs text-apex-muted/75">
              Process discipline score · {processScore}/100
            </p>
          ) : null}
          {reconcileMessage ? (
            <p className="text-xs text-emerald-200/80">{reconcileMessage}</p>
          ) : null}
        </div>
      </header>

      <div className="mb-4 flex gap-2">
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
          {receipts.map((receipt) =>
            receipt.order_id &&
            receipt.fill_side &&
            typeof receipt.fill_quantity === "number" ? (
              <DecisionReceipt
                key={receipt.id}
                symbol={receipt.symbol}
                executionKind={
                  receipt.execution_kind as "BUY" | "SELL" | "WAIT" | "OBSERVE"
                }
                fill={{
                  orderId: receipt.order_id,
                  quantity: Number(receipt.fill_quantity),
                  side: receipt.fill_side as "buy" | "sell",
                  price:
                    receipt.fill_price !== null
                      ? Number(receipt.fill_price)
                      : undefined,
                }}
                trustDelta={receipt.trust_delta ?? undefined}
              />
            ) : (
              <section
                key={receipt.id}
                className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3"
              >
                <p className="text-sm font-medium text-apex-text/90">
                  {receipt.verdict_word ?? receipt.execution_kind} · {receipt.symbol}
                </p>
                <p className="text-xs text-apex-muted/75">
                  {receipt.headline ?? receipt.subline ?? receipt.receipt_date}
                </p>
              </section>
            ),
          )}
        </div>
      )}
    </ApexShell>
  );
}
