import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type CdqsInterpretation =
  | "trustworthy"
  | "calibrating"
  | "trust_failure"
  | "insufficient_data";

export type CdqsSnapshot = {
  score: number | null;
  scorePercent: number | null;
  interpretation: CdqsInterpretation;
  headline: string;
  detail: string;
  matched: number;
  total: number;
  windowDays: number;
};

export const CDQS_WINDOW_DAYS = 90;
export const CDQS_MIN_SAMPLE = 3;

export type ConfidenceBand = "High" | "Moderate" | "Low";

export function confidenceBandFromLevel(level: number): ConfidenceBand {
  if (level >= 75) {
    return "High";
  }

  if (level >= 55) {
    return "Moderate";
  }

  return "Low";
}

/**
 * Whether a broker-verified closed trade matched the confidence we stated at entry.
 * See APEX-000 §12 — CDQS north star.
 */
export function outcomeMatchesConfidenceBand(
  confidence: number,
  pnl: number,
  entryPrice: number | null,
): boolean {
  if (!Number.isFinite(pnl)) {
    return false;
  }

  const band = confidenceBandFromLevel(confidence);

  if (band === "High") {
    return pnl >= 0;
  }

  if (band === "Low") {
    return true;
  }

  if (pnl >= 0) {
    return true;
  }

  if (entryPrice !== null && entryPrice > 0) {
    const lossPct = (Math.abs(pnl) / entryPrice) * 100;
    return lossPct <= 2;
  }

  return false;
}

export function interpretCdqsScore(score: number): CdqsInterpretation {
  if (score >= 0.8) {
    return "trustworthy";
  }

  if (score >= 0.6) {
    return "calibrating";
  }

  return "trust_failure";
}

export function buildCdqsCopy(input: {
  interpretation: CdqsInterpretation;
  scorePercent: number | null;
  matched: number;
  total: number;
}): { headline: string; detail: string } {
  switch (input.interpretation) {
    case "trustworthy":
      return {
        headline: "Recommendations match reality",
        detail: `${input.matched} of ${input.total} closed trades (${input.scorePercent}%) landed in the confidence band we stated — broker verified.`,
      };
    case "calibrating":
      return {
        headline: "Calibration in progress",
        detail: `${input.scorePercent}% of closed trades matched stated confidence (${input.matched}/${input.total}). Threshold tuning is active.`,
      };
    case "trust_failure":
      return {
        headline: "Trust needs repair",
        detail: `Only ${input.scorePercent}% of closed trades matched stated confidence (${input.matched}/${input.total}). We tighten framing before new acts.`,
      };
    case "insufficient_data":
      return {
        headline: "Not enough history yet",
        detail: `CDQS needs at least ${CDQS_MIN_SAMPLE} broker-verified closed trades. Keep following receipts — memory builds with each closed act.`,
      };
  }
}

export function computeCdqsFromRows(
  rows: Array<{
    confidence: number;
    pnl: number | null;
    entry_price: number | null;
  }>,
  windowDays = CDQS_WINDOW_DAYS,
): CdqsSnapshot {
  let matched = 0;
  let total = 0;

  for (const row of rows) {
    if (row.pnl === null || !Number.isFinite(Number(row.pnl))) {
      continue;
    }

    total += 1;

    if (
      outcomeMatchesConfidenceBand(
        Number(row.confidence),
        Number(row.pnl),
        row.entry_price !== null ? Number(row.entry_price) : null,
      )
    ) {
      matched += 1;
    }
  }

  if (total < CDQS_MIN_SAMPLE) {
    const copy = buildCdqsCopy({
      interpretation: "insufficient_data",
      scorePercent: null,
      matched,
      total,
    });

    return {
      score: null,
      scorePercent: null,
      interpretation: "insufficient_data",
      headline: copy.headline,
      detail: copy.detail,
      matched,
      total,
      windowDays,
    };
  }

  const score = matched / total;
  const scorePercent = Math.round(score * 100);
  const interpretation = interpretCdqsScore(score);
  const copy = buildCdqsCopy({
    interpretation,
    scorePercent,
    matched,
    total,
  });

  return {
    score,
    scorePercent,
    interpretation,
    headline: copy.headline,
    detail: copy.detail,
    matched,
    total,
    windowDays,
  };
}

export async function computeCdqsSnapshot(
  supabase: Client,
  userId: string,
  windowDays = CDQS_WINDOW_DAYS,
): Promise<CdqsSnapshot> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - windowDays);

  const { data, error } = await supabase
    .from("decision_memory")
    .select("confidence, pnl, entry_price, action, exit_price")
    .eq("user_id", userId)
    .eq("action", "buy")
    .not("exit_price", "is", null)
    .gte("updated_at", cutoff.toISOString())
    .order("updated_at", { ascending: false })
    .limit(200);

  if (error || !data) {
    return computeCdqsFromRows([], windowDays);
  }

  return computeCdqsFromRows(
    data.map((row) => ({
      confidence: Number(row.confidence),
      pnl: row.pnl !== null ? Number(row.pnl) : null,
      entry_price: row.entry_price !== null ? Number(row.entry_price) : null,
    })),
    windowDays,
  );
}

export function runCdqsSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`CDQS self-check failed: ${message}`);
    }
  };

  assert(
    outcomeMatchesConfidenceBand(80, 100, 1000),
    "High confidence win must match",
  );
  assert(
    !outcomeMatchesConfidenceBand(80, -50, 1000),
    "High confidence loss must not match",
  );
  assert(
    outcomeMatchesConfidenceBand(40, -200, 1000),
    "Low confidence loss stays in band",
  );
  assert(
    outcomeMatchesConfidenceBand(60, -10, 1000),
    "Moderate small loss must match",
  );

  const snapshot = computeCdqsFromRows([
    { confidence: 80, pnl: 100, entry_price: 1000 },
    { confidence: 80, pnl: 50, entry_price: 1000 },
    { confidence: 60, pnl: -10, entry_price: 1000 },
  ]);

  assert(snapshot.interpretation === "trustworthy", "3/3 must be trustworthy");
  assert(snapshot.scorePercent === 100, "Score percent must be 100");

  const sparse = computeCdqsFromRows([
    { confidence: 80, pnl: 100, entry_price: 1000 },
  ]);
  assert(sparse.interpretation === "insufficient_data", "Sparse sample must wait");
}
