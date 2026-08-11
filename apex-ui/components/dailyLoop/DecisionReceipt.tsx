"use client";

import {
  describeBrokerFill,
  type BrokerFillSummary,
} from "@/services/trade/logTradeFill";

export type DecisionReceiptProps = {
  symbol: string;
  executionKind: "BUY" | "SELL" | "WAIT" | "OBSERVE";
  fill: BrokerFillSummary;
  trustDelta?: number;
  onDismiss?: () => void;
};

function TrustDelta({ delta }: { delta: number }) {
  if (delta > 0) {
    return <span className="text-emerald-300/90">Trust ↑ {delta}</span>;
  }

  if (delta < 0) {
    return <span className="text-amber-200/90">Trust ↓ {Math.abs(delta)}</span>;
  }

  return null;
}

export default function DecisionReceipt({
  symbol,
  executionKind,
  fill,
  trustDelta,
  onDismiss,
}: DecisionReceiptProps) {
  const actionLabel =
    executionKind === "SELL"
      ? "Trim logged"
      : executionKind === "BUY"
        ? "Entry logged"
        : "Order logged";

  return (
    <section
      aria-label="Decision receipt"
      className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-4 py-4 space-y-2"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-emerald-100/80">
            Decision receipt
          </p>
          <p className="text-sm font-semibold text-emerald-50/95">
            {actionLabel} · {symbol}
          </p>
        </div>
        {onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            className="text-xs text-emerald-100/70 transition-colors hover:text-emerald-50"
          >
            Dismiss
          </button>
        ) : null}
      </div>

      <p className="text-sm text-emerald-50/90">
        {describeBrokerFill(fill, symbol)}
      </p>
      <p className="text-xs text-emerald-100/70">Order ID {fill.orderId}</p>
      {typeof trustDelta === "number" ? (
        <p className="text-xs">
          <TrustDelta delta={trustDelta} />
        </p>
      ) : null}
    </section>
  );
}
