import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";
import {
  parseReceiptSnapshot,
  quoteReceiptVerdict,
} from "@/services/receipts/snapshot";

export type FamilyReadModelLine = {
  date: string;
  symbol: string;
  verdict: string;
  reason: string;
  source: "artifact" | "brief" | "receipt";
};

export type FamilyReadModel = {
  lines: FamilyReadModelLine[];
  share_lines: string[];
};

/**
 * Family / spouse / advisor blotter. Quotes frozen receipts only.
 * No recommendation logic — no Buy/Sell hunt, no new size.
 */
export function assembleFamilyReadModel(
  receipts: DecisionReceiptRow[],
): FamilyReadModel {
  const active = receipts.filter((row) => !row.dismissed_at);
  const lines: FamilyReadModelLine[] = active.map((receipt) => {
    const quoted = quoteReceiptVerdict(parseReceiptSnapshot(receipt.brief_snapshot));
    return {
      date: receipt.receipt_date,
      symbol: receipt.symbol,
      verdict:
        quoted.source === "none"
          ? (receipt.verdict_word ?? receipt.execution_kind)
          : quoted.verdict,
      reason: quoted.reason || receipt.headline || receipt.subline || "",
      source: quoted.source === "none" ? "receipt" : quoted.source,
    };
  });

  return {
    lines,
    share_lines: lines.map(
      (line) => `${line.date} · ${line.symbol} · ${line.verdict}`,
    ),
  };
}

export function runFamilyReadModelSelfCheck(): void {
  const model = assembleFamilyReadModel([
    {
      id: "r1",
      receipt_date: "2026-09-10",
      symbol: "INFY",
      execution_kind: "WAIT",
      verdict_word: "WAIT",
      headline: "Waited",
      subline: "No trade",
      trust_score: null,
      trust_delta: null,
      order_id: null,
      fill_side: null,
      fill_quantity: null,
      fill_price: null,
      fill_amount: null,
      brief_snapshot: {
        schema: "apex.receipt.v1",
        artifact: null,
        brief: null,
      },
      dismissed_at: null,
      created_at: "2026-09-10T10:00:00.000Z",
    },
  ]);

  if (model.lines.length !== 1 || model.lines[0]?.verdict !== "WAIT") {
    throw new Error("Family read model self-check failed: must quote the receipt");
  }
  if (model.share_lines.some((line) => /buy|sell/i.test(line) && !/WAIT/i.test(line))) {
    throw new Error("Family read model self-check failed: must not invent a trade");
  }
}
