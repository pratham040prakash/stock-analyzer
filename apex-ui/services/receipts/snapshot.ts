import type { DailyDecisionArtifact } from "@/types/decision";
import { validateDailyDecisionArtifact } from "@/types/decision";
import type { MorningBriefViewModel } from "@/types/morningBrief";

export const RECEIPT_SNAPSHOT_SCHEMA = "apex.receipt.v1" as const;

export type ReceiptSnapshot = {
  schema: typeof RECEIPT_SNAPSHOT_SCHEMA;
  artifact: DailyDecisionArtifact | null;
  brief: MorningBriefViewModel | null;
};

function isBrief(value: unknown): value is MorningBriefViewModel {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return Boolean(
    candidate.decision &&
      typeof candidate.decision === "object" &&
      candidate.evidence &&
      typeof candidate.evidence === "object",
  );
}

export function buildReceiptSnapshot(input: {
  artifact?: DailyDecisionArtifact | null;
  brief?: MorningBriefViewModel | null;
}): ReceiptSnapshot {
  return {
    schema: RECEIPT_SNAPSHOT_SCHEMA,
    artifact: input.artifact && validateDailyDecisionArtifact(input.artifact)
      ? input.artifact
      : null,
    brief: input.brief ?? null,
  };
}

export function parseReceiptSnapshot(value: unknown): ReceiptSnapshot {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { schema: RECEIPT_SNAPSHOT_SCHEMA, artifact: null, brief: null };
  }

  const record = value as Record<string, unknown>;
  if (record.schema === RECEIPT_SNAPSHOT_SCHEMA) {
    return {
      schema: RECEIPT_SNAPSHOT_SCHEMA,
      artifact: validateDailyDecisionArtifact(record.artifact)
        ? record.artifact
        : null,
      brief: isBrief(record.brief) ? record.brief : null,
    };
  }

  if (isBrief(value)) {
    return { schema: RECEIPT_SNAPSHOT_SCHEMA, artifact: null, brief: value };
  }

  return { schema: RECEIPT_SNAPSHOT_SCHEMA, artifact: null, brief: null };
}

export function quoteReceiptVerdict(snapshot: ReceiptSnapshot): {
  verdict: string;
  reason: string;
  source: "artifact" | "brief" | "none";
} {
  if (snapshot.artifact) {
    return {
      verdict: snapshot.artifact.daily_verdict,
      reason: snapshot.artifact.decision_metadata.reason,
      source: "artifact",
    };
  }
  if (snapshot.brief) {
    return {
      verdict: snapshot.brief.decision.verdict_display,
      reason: snapshot.brief.decision.reason,
      source: "brief",
    };
  }
  return { verdict: "—", reason: "", source: "none" };
}

export function runReceiptSnapshotSelfCheck(): void {
  const now = "2026-09-11T09:00:00.000Z";
  const artifact: DailyDecisionArtifact = {
    schema_version: "1",
    decision_id: "2026-09-11:rcpt",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "protect",
    action: "wait",
    symbol: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "none",
    },
    approved_size: { kind: "none" },
    daily_verdict: "wait",
    tradingLocked: true,
    entryConfirmed: false,
    capital_state: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "unknown",
    },
    broker_state: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "unknown",
    },
    market_state: {
      status: "unknown",
      value: null,
      observed_at: null,
      reason: "unknown",
    },
    source_timestamps: {
      portfolio: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      capital: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      broker: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      market: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
      entry: {
        status: "unknown",
        value: null,
        observed_at: null,
        reason: "unknown",
      },
    },
    evidence_ids: ["reason"],
    evidence: [
      {
        id: "reason",
        type: "FACT",
        source: "decision_engine",
        summary: "Wait",
        observed_at: now,
      },
    ],
    blockers: ["Wait"],
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision",
      confidence: 50,
      reason: "Frozen wait",
      confidence_factors: [],
    },
    frozen_portfolio: { positions: [], total_value_inr: 0, pnl_inr: 0 },
    projection: {
      decision: "WAIT",
      action: "wait",
      confidence: 50,
      reason: "Frozen wait",
      confidence_factors: [],
      actions: [],
    },
  };

  const snapshot = buildReceiptSnapshot({ artifact });
  const parsed = parseReceiptSnapshot(snapshot);
  const quoted = quoteReceiptVerdict(parsed);
  if (quoted.source !== "artifact" || quoted.reason !== "Frozen wait") {
    throw new Error("Receipt snapshot self-check failed: must quote the artifact");
  }

  const legacy = parseReceiptSnapshot({
    status: "ok",
    meta: {
      built_at: now,
      scenario: "protect",
      market: "flat",
      session_phase: "open",
    },
    decision: {
      verdict: "wait",
      verdict_display: "Wait",
      daily_verdict: "wait",
      verdict_key: "WAIT",
      reason: "Legacy brief",
      confidence_level: 50,
      confidence_band: "Low",
      last_updated: now,
      valid_until: now,
      cta_label: "Wait",
      cta_action: "wait",
      decision_id: "legacy",
      decision_source: "brief",
      headline: "Wait",
      subline: "Hold",
    },
    evidence: {
      key_reasons: [],
      supporting_signals: [],
      conflicting_signals: [],
      evidence_packet_id: "x",
      evidence_available: false,
      gap_note: "",
    },
    trust: {},
    opportunity: {},
    portfolio: {},
    risk: {},
    discipline: {},
    market: {},
    failure_message: null,
  });
  if (quoteReceiptVerdict(legacy).source !== "brief") {
    throw new Error("Receipt snapshot self-check failed: legacy brief must still parse");
  }
}
