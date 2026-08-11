"use client";

import type { MorningBriefViewModel } from "@/types/morningBrief";
import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";

type Props = {
  receipt: DecisionReceiptRow;
};

function parseBrief(value: unknown): MorningBriefViewModel | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  return value as MorningBriefViewModel;
}

export default function ReceiptProofPanel({ receipt }: Props) {
  const brief = parseBrief(receipt.brief_snapshot);

  return (
    <section
      aria-label="Receipt proof"
      className="rounded-xl border border-blue-500/20 bg-blue-500/5 px-4 py-4 space-y-3"
    >
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-blue-100/70">
          Proof snapshot
        </p>
        <p className="text-sm font-semibold text-apex-text/95">
          {receipt.verdict_word ?? receipt.execution_kind} · {receipt.symbol}
        </p>
        <p className="text-xs text-apex-muted/75">{receipt.receipt_date}</p>
      </div>

      {receipt.headline ? (
        <p className="text-sm text-apex-text/90">{receipt.headline}</p>
      ) : null}

      {brief ? (
        <div className="space-y-2 text-sm text-apex-text/85">
          <p>
            <span className="text-apex-muted/70">Verdict · </span>
            {brief.decision.verdict_display}
          </p>
          <p>
            <span className="text-apex-muted/70">Reason · </span>
            {brief.decision.reason}
          </p>
          <p>
            <span className="text-apex-muted/70">Trust · </span>
            {brief.trust.trust_message}
          </p>
          {brief.evidence.key_reasons[0] ? (
            <p>
              <span className="text-apex-muted/70">Evidence · </span>
              {brief.evidence.key_reasons[0]}
            </p>
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-apex-muted/75">
          No brief snapshot stored — receipt captures discipline or fill metadata only.
        </p>
      )}
    </section>
  );
}
