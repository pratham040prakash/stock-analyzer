"use client";

import Link from "next/link";
import DecisionReceipt from "@/components/dailyLoop/DecisionReceipt";
import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";
import type { BrokerFillSummary } from "@/services/trade/logTradeFill";

type Props = {
  receipt: DecisionReceiptRow;
  onDismiss?: (id: string) => void;
};

function hasFill(receipt: DecisionReceiptRow): receipt is DecisionReceiptRow & {
  order_id: string;
  fill_side: "buy" | "sell";
  fill_quantity: number;
} {
  return (
    Boolean(receipt.order_id) &&
    (receipt.fill_side === "buy" || receipt.fill_side === "sell") &&
    typeof receipt.fill_quantity === "number"
  );
}

function proofHref(receipt: DecisionReceiptRow): string | null {
  if (receipt.brief_snapshot) {
    return `/app?receipt=${encodeURIComponent(receipt.id)}`;
  }

  return `/app/journal?receipt=${encodeURIComponent(receipt.id)}`;
}

export default function DecisionReceiptCard({ receipt, onDismiss }: Props) {
  if (hasFill(receipt)) {
    const fill: BrokerFillSummary = {
      orderId: receipt.order_id,
      quantity: Number(receipt.fill_quantity),
      side: receipt.fill_side,
      price:
        receipt.fill_price !== null ? Number(receipt.fill_price) : undefined,
    };

    return (
      <div className="space-y-2">
        <DecisionReceipt
          symbol={receipt.symbol}
          executionKind={
            receipt.execution_kind as "BUY" | "SELL" | "WAIT" | "OBSERVE"
          }
          fill={fill}
          trustDelta={receipt.trust_delta ?? undefined}
          onDismiss={onDismiss ? () => onDismiss(receipt.id) : undefined}
        />
        <ProofLink receipt={receipt} />
      </div>
    );
  }

  const kind = receipt.execution_kind;
  const label =
    kind === "WAIT"
      ? "Wait logged"
      : kind === "OBSERVE"
        ? "Observe logged"
        : "Decision logged";

  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Decision receipt
          </p>
          <p className="text-sm font-semibold text-apex-text/95">
            {label} · {receipt.symbol}
          </p>
          <p className="text-xs text-apex-muted/75 mt-1">
            {receipt.verdict_word ?? kind} · {receipt.receipt_date}
          </p>
        </div>
        {onDismiss ? (
          <button
            type="button"
            onClick={() => onDismiss(receipt.id)}
            className="text-xs text-apex-muted transition-colors hover:text-apex-text"
          >
            Dismiss
          </button>
        ) : null}
      </div>
      {receipt.headline ? (
        <p className="text-sm text-apex-text/85">{receipt.headline}</p>
      ) : null}
      {receipt.subline ? (
        <p className="text-xs text-apex-muted/75">{receipt.subline}</p>
      ) : null}
      {typeof receipt.trust_delta === "number" && receipt.trust_delta !== 0 ? (
        <p className="text-xs text-apex-muted/80">
          Trust {receipt.trust_delta > 0 ? "↑" : "↓"}{" "}
          {Math.abs(receipt.trust_delta)}
        </p>
      ) : null}
      <ProofLink receipt={receipt} />
    </section>
  );
}

function ProofLink({ receipt }: { receipt: DecisionReceiptRow }) {
  const href = proofHref(receipt);

  if (!href) {
    return null;
  }

  return (
    <Link
      href={href}
      className="inline-flex text-xs text-blue-200/90 transition-colors hover:text-blue-100"
    >
      View proof snapshot →
    </Link>
  );
}
