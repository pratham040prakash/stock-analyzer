"use client";

import ProofStructurePanel from "@/components/proof/ProofStructurePanel";
import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";
import {
  parseReceiptSnapshot,
  quoteReceiptVerdict,
} from "@/services/receipts/snapshot";

type Props = {
  receipt: DecisionReceiptRow;
};

export default function ReceiptProofPanel({ receipt }: Props) {
  const snapshot = parseReceiptSnapshot(receipt.brief_snapshot);
  const brief = snapshot.brief;
  const quoted = quoteReceiptVerdict(snapshot);

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

      {quoted.source !== "none" ? (
        <div className="space-y-2 text-sm text-apex-text/85">
          <p>
            <span className="text-apex-muted/70">
              {quoted.source === "artifact" ? "Frozen verdict · " : "Verdict · "}
            </span>
            {quoted.verdict}
          </p>
          {quoted.reason ? (
            <p>
              <span className="text-apex-muted/70">Reason · </span>
              {quoted.reason}
            </p>
          ) : null}
          {brief ? (
            <p>
              <span className="text-apex-muted/70">Trust · </span>
              {brief.trust.trust_message}
            </p>
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-apex-muted/75">
          No brief snapshot stored — receipt captures discipline or fill metadata only.
        </p>
      )}
      {brief ? (
        <ProofStructurePanel brief={brief} artifact={snapshot.artifact} />
      ) : null}
    </section>
  );
}
