import type { DecisionEvidenceMetadata } from "@/types/decision";

const FORBIDDEN_AUTHORITY_KEYS = [
  "action",
  "daily_verdict",
  "tradingLocked",
  "symbol",
  "approved_size",
  "amount",
  "suggested_sell_percent",
] as const;

export type EvidenceContribution = {
  id: string;
  type: DecisionEvidenceMetadata["type"];
  source: string;
  summary: string;
  observed_at: string | null;
};

function isEvidenceType(
  value: unknown,
): value is DecisionEvidenceMetadata["type"] {
  return (
    value === "FACT" ||
    value === "ASSUMPTION" ||
    value === "ESTIMATE" ||
    value === "OPINION"
  );
}

/**
 * Optional pre-freeze evidence from TypeScript research or Python Alpha AI.
 * Providers may add labeled facts only. They cannot set action, verdict,
 * lock, symbol, or size — those stay with the TypeScript producer.
 */
export function sanitizeEvidenceContribution(
  raw: unknown,
): DecisionEvidenceMetadata | null {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return null;
  }

  const record = raw as Record<string, unknown>;
  for (const key of FORBIDDEN_AUTHORITY_KEYS) {
    if (key in record) {
      return null;
    }
  }

  if (
    typeof record.id !== "string" ||
    !record.id.trim() ||
    !isEvidenceType(record.type) ||
    typeof record.source !== "string" ||
    !record.source.trim() ||
    typeof record.summary !== "string" ||
    !record.summary.trim()
  ) {
    return null;
  }

  return {
    id: record.id.trim(),
    type: record.type,
    source: record.source.trim(),
    summary: record.summary.trim(),
    observed_at:
      typeof record.observed_at === "string" ? record.observed_at : null,
  };
}

export function mergeEvidenceContributions(
  existing: DecisionEvidenceMetadata[],
  contributions: unknown[],
): DecisionEvidenceMetadata[] {
  const merged = [...existing];
  const seen = new Set(existing.map((item) => item.id));

  for (const raw of contributions) {
    const item = sanitizeEvidenceContribution(raw);
    if (!item || seen.has(item.id)) {
      continue;
    }
    seen.add(item.id);
    merged.push(item);
  }

  return merged;
}

export function runEvidenceContributionSelfCheck(): void {
  const accepted = sanitizeEvidenceContribution({
    id: "research:1",
    type: "OPINION",
    source: "alpha_ai",
    summary: "Quality looks intact",
    observed_at: "2026-09-11T09:00:00.000Z",
  });
  if (!accepted) {
    throw new Error("Evidence contribution self-check failed: valid row rejected");
  }

  const hostile = sanitizeEvidenceContribution({
    id: "research:hostile",
    type: "FACT",
    source: "alpha_ai",
    summary: "Buy it",
    action: "buy",
    observed_at: "2026-09-11T09:00:00.000Z",
  });
  if (hostile) {
    throw new Error(
      "Evidence contribution self-check failed: authority fields must be rejected",
    );
  }

  const merged = mergeEvidenceContributions(
    [
      {
        id: "reason",
        type: "FACT",
        source: "decision_engine",
        summary: "Wait",
        observed_at: null,
      },
    ],
    [accepted, { id: "reason", type: "FACT", source: "dup", summary: "dup" }],
  );
  if (merged.length !== 2 || merged[0]?.id !== "reason") {
    throw new Error("Evidence contribution self-check failed: merge must keep producer rows");
  }
}
