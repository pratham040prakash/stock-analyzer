"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import DecisionReceiptCard from "@/components/receipts/DecisionReceiptCard";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";

type ReceiptsResponse = {
  status: string;
  receipts: DecisionReceiptRow[];
};

type JournalTab = "all" | "fills" | "wait" | "dismissed";

export default function JournalPageClient({ userName }: { userName: string }) {
  const searchParams = useSearchParams();
  const highlightId = searchParams.get("receipt");
  const [tab, setTab] = useState<JournalTab>("all");
  const [receipts, setReceipts] = useState<DecisionReceiptRow[]>([]);
  const [loading, setLoading] = useState(true);

  const loadReceipts = useCallback(async () => {
    setLoading(true);

    try {
      const response = await apiFetch("/api/receipts?days=60", {
        cache: "no-store",
      });
      const data = await parseApiJson<ReceiptsResponse>(response, "Receipts");

      if (response.ok && data?.receipts) {
        setReceipts(data.receipts);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadReceipts();
  }, [loadReceipts]);

  const filtered = useMemo(() => {
    switch (tab) {
      case "fills":
        return receipts.filter(
          (row) =>
            row.execution_kind === "BUY" ||
            row.execution_kind === "SELL" ||
            Boolean(row.order_id && row.fill_quantity),
        );
      case "wait":
        return receipts.filter(
          (row) => row.execution_kind === "WAIT" || row.execution_kind === "OBSERVE",
        );
      case "dismissed":
        return receipts.filter((row) => Boolean(row.dismissed_at));
      default:
        return receipts.filter((row) => !row.dismissed_at);
    }
  }, [receipts, tab]);

  const dismissReceipt = useCallback(
    async (id: string) => {
      await apiFetch("/api/receipts", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      await loadReceipts();
    },
    [loadReceipts],
  );

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Journal</ApexTitle>
          <p className="text-sm text-apex-muted">
            Immutable decision receipts for {userName}.
          </p>
        </div>
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        {(
          [
            ["all", "Timeline"],
            ["fills", "Fills"],
            ["wait", "Wait / Observe"],
            ["dismissed", "Dismissed"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={
              tab === key
                ? "rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-100"
                : "rounded-lg border border-apex-border/20 px-3 py-1.5 text-xs text-apex-muted"
            }
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading journal…</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-apex-muted/70">
          Receipts appear here after you commit discipline or log a broker fill on
          Today.
        </p>
      ) : (
        <div className="space-y-3">
          {filtered.map((receipt) => (
            <div
              key={receipt.id}
              id={`receipt-${receipt.id}`}
              className={
                highlightId === receipt.id
                  ? "rounded-xl ring-1 ring-blue-400/40"
                  : undefined
              }
            >
              <DecisionReceiptCard
                receipt={receipt}
                onDismiss={tab === "dismissed" ? undefined : dismissReceipt}
              />
            </div>
          ))}
        </div>
      )}
    </ApexShell>
  );
}
