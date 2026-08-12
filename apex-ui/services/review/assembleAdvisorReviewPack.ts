import { formatDisciplineSummary } from "@/lib/dailyLoop/disciplineHistoryMerge";
import { ADVISOR_PILOT_COPY } from "@/lib/gtm/advisorPilotCopy";
import { buildWeeklyReviewHeadline } from "@/lib/dailyLoop/weeklyReview";
import { exportReceiptMarkdown } from "@/services/receipts/exportReceiptMarkdown";
import type { DecisionReceiptRow } from "@/services/receipts/persistReceipt";
import type { DisciplineHistorySummary } from "@/types/decisionHistory";

export type AdvisorReviewPackInput = {
  clientLabel: string;
  seats: number;
  receipts: DecisionReceiptRow[];
  summary: DisciplineHistorySummary;
  streakCount: number;
  generatedAt?: string;
};

export type AdvisorReviewPack = {
  generated_at: string;
  client_label: string;
  seats: number;
  receipt_count: number;
  week_headline: string;
  markdown: string;
};

export function assembleAdvisorReviewPack(
  input: AdvisorReviewPackInput,
): AdvisorReviewPack {
  const generatedAt = input.generatedAt ?? new Date().toISOString();
  const weekHeadline = buildWeeklyReviewHeadline(input.summary);
  const summaryLine = formatDisciplineSummary(input.summary);
  const activeReceipts = input.receipts.filter((row) => !row.dismissed_at);

  const lines: string[] = [
    `# ${ADVISOR_PILOT_COPY.packTitle}`,
    "",
    `- **Client:** ${input.clientLabel}`,
    `- **Generated:** ${generatedAt}`,
    `- **Review seats (pilot):** ${input.seats}`,
    "",
    ADVISOR_PILOT_COPY.packIntro,
    "",
    "## Weekly discipline",
    `- **Headline:** ${weekHeadline}`,
    `- **Summary:** ${summaryLine}`,
    `- **Streak:** ${input.streakCount} day${input.streakCount === 1 ? "" : "s"}`,
    "",
    "## Decision receipts",
    "",
  ];

  if (activeReceipts.length === 0) {
    lines.push(ADVISOR_PILOT_COPY.emptyReceipts, "");
  } else {
    for (const receipt of activeReceipts) {
      lines.push(exportReceiptMarkdown(receipt), "", "---", "");
    }
  }

  lines.push(
    "_Read-only advisor pack · APEX discipline infrastructure · Not investment advice._",
  );

  return {
    generated_at: generatedAt,
    client_label: input.clientLabel,
    seats: input.seats,
    receipt_count: activeReceipts.length,
    week_headline: weekHeadline,
    markdown: lines.join("\n"),
  };
}

export function downloadAdvisorReviewPackMarkdown(
  pack: AdvisorReviewPack,
): void {
  const blob = new Blob([pack.markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const dateKey = pack.generated_at.slice(0, 10);
  anchor.href = url;
  anchor.download = `apex-advisor-pack-${dateKey}.md`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function runAdvisorReviewPackSelfCheck(): void {
  const pack = assembleAdvisorReviewPack({
    clientLabel: "Pilot Client",
    seats: 1,
    streakCount: 3,
    summary: {
      wins: 1,
      losses: 0,
      open: 0,
      waitDays: 4,
      executedDays: 1,
      followedDays: 2,
    },
    receipts: [
      {
        id: "r1",
        receipt_date: "2026-08-11",
        symbol: "JIOFIN",
        execution_kind: "WAIT",
        verdict_word: "WAIT",
        headline: "Wait day",
        subline: "No tactical action",
        trust_score: 72,
        trust_delta: 1,
        order_id: null,
        fill_side: null,
        fill_quantity: null,
        fill_price: null,
        fill_amount: null,
        brief_snapshot: null,
        dismissed_at: null,
        created_at: "2026-08-11T10:00:00.000Z",
      },
    ],
    generatedAt: "2026-08-11T10:00:00.000Z",
  });

  if (!pack.markdown.includes("Weekly discipline") || pack.receipt_count !== 1) {
    throw new Error("Advisor review pack self-check failed: markdown shape");
  }
}
