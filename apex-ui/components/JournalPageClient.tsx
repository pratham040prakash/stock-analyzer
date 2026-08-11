"use client";

import { useCallback, useEffect, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import DecisionReceipt from "@/components/dailyLoop/DecisionReceipt";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";

type ReceiptsResponse = {
  status: string;
  receipts: DecisionReceiptRow[];
};

export default function JournalPageClient({ userName }: { userName: string }) {
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

      {loading ? (
        <p className="text-sm text-apex-muted/70">Loading journal…</p>
      ) : receipts.length === 0 ? (
        <p className="text-sm text-apex-muted/70">
          Receipts appear here after you act or log a broker fill on Today.
        </p>
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
                className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-1"
              >
                <p className="text-xs text-apex-muted/65">{receipt.receipt_date}</p>
                <p className="text-sm font-medium text-apex-text/90">
                  {receipt.verdict_word ?? receipt.execution_kind} · {receipt.symbol}
                </p>
                <p className="text-sm text-apex-muted/80">
                  {receipt.headline ?? receipt.subline ?? "Decision logged"}
                </p>
              </section>
            ),
          )}
        </div>
      )}
    </ApexShell>
  );
}
