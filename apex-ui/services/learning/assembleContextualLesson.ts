import { buildPlannedVsActualRows } from "@/services/review/plannedVsActual";
import { listDecisionReceipts } from "@/services/receipts/persistReceipt";
import type { ContextualLessonViewModel } from "@/types/contextualLesson";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export async function assembleContextualLesson(
  supabase: Client,
  userId: string,
): Promise<ContextualLessonViewModel | null> {
  const [planned, receipts] = await Promise.all([
    buildPlannedVsActualRows(supabase, userId, 14),
    listDecisionReceipts(supabase, userId, 14),
  ]);

  const deviation = planned.rows.find((row) => row.status === "deviated");

  if (deviation) {
    return {
      built_at: new Date().toISOString(),
      headline: "Plan vs action drift",
      lesson: `On ${deviation.date}, the plan said ${deviation.planned_action} but action was ${deviation.actual_action ?? "—"}. Tighten the morning commit before the next session.`,
      source: "planned_vs_actual",
      receipt_id: null,
      review_href: "/app/review?tab=weekly",
    };
  }

  const waitThenAct = receipts.find(
    (row, index) =>
      row.execution_kind === "BUY" &&
      receipts.slice(index + 1).some((other) => other.execution_kind === "WAIT"),
  );

  if (waitThenAct) {
    return {
      built_at: new Date().toISOString(),
      headline: "WAIT before ACT",
      lesson: `Recent ${waitThenAct.symbol} activity followed a WAIT receipt — confirm size matched the thesis, not FOMO.`,
      source: "receipt_sequence",
      receipt_id: waitThenAct.id,
      review_href: `/app/review?tab=receipts&receipt=${encodeURIComponent(waitThenAct.id)}`,
    };
  }

  const followedWait = receipts.find((row) => row.execution_kind === "WAIT");

  if (followedWait) {
    return {
      built_at: new Date().toISOString(),
      headline: "Waiting is progress",
      lesson: `Your ${followedWait.symbol} WAIT receipt preserved capital — review it before changing stance.`,
      source: "receipt",
      receipt_id: followedWait.id,
      review_href: `/app/review?tab=receipts&receipt=${encodeURIComponent(followedWait.id)}`,
    };
  }

  return null;
}

export function runContextualLessonSelfCheck(): void {
  if (typeof assembleContextualLesson !== "function") {
    throw new Error("Contextual lesson self-check failed");
  }
}
