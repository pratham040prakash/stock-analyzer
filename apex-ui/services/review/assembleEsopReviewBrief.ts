import { describeInvestmentStyle } from "@/lib/dailyLoop/operatingManualCopy";
import { formatDisciplineSummary } from "@/lib/dailyLoop/disciplineHistoryMerge";
import { buildWeeklyReviewHeadline } from "@/lib/dailyLoop/weeklyReview";
import { ESOP_REVIEW_PERSONA_COPY } from "@/lib/gtm/esopReviewPersonaCopy";
import type { DisciplineHistorySummary } from "@/types/decisionHistory";
import type { InvestmentStyle } from "@/types/operatingProfile";

export type EsopReviewBriefInput = {
  investorLabel: string;
  investmentStyle: InvestmentStyle | null;
  summary: DisciplineHistorySummary;
  streakCount: number;
  reviewWeeklyUrl: string;
  reviewQuarterlyUrl: string;
  generatedAt?: string;
};

export type EsopReviewBrief = {
  generated_at: string;
  investor_label: string;
  investment_style_line: string;
  week_headline: string;
  share_text: string;
  markdown: string;
};

function resolveStyleLine(style: InvestmentStyle | null): string {
  if (!style) {
    return "Set your investment style in You → Settings to align ESOP with long-term core.";
  }

  return describeInvestmentStyle(style);
}

function buildShareText(input: EsopReviewBriefInput): string {
  const weekHeadline = buildWeeklyReviewHeadline(input.summary);
  const summaryLine = formatDisciplineSummary(input.summary);
  const streakLine =
    input.streakCount > 0
      ? `${input.streakCount} day discipline streak`
      : "Building a daily discipline streak";

  return [
    ESOP_REVIEW_PERSONA_COPY.briefIntro,
    "",
    `Style: ${resolveStyleLine(input.investmentStyle)}`,
    weekHeadline,
    summaryLine,
    streakLine,
    "",
    ESOP_REVIEW_PERSONA_COPY.cadenceWeekly,
    ESOP_REVIEW_PERSONA_COPY.cadenceQuarterly,
    "",
    ESOP_REVIEW_PERSONA_COPY.holdCoreRule,
    "",
    `Weekly review: ${input.reviewWeeklyUrl}`,
    `Quarterly review: ${input.reviewQuarterlyUrl}`,
  ].join("\n");
}

export function assembleEsopReviewBrief(input: EsopReviewBriefInput): EsopReviewBrief {
  const generatedAt = input.generatedAt ?? new Date().toISOString();
  const weekHeadline = buildWeeklyReviewHeadline(input.summary);
  const summaryLine = formatDisciplineSummary(input.summary);
  const styleLine = resolveStyleLine(input.investmentStyle);
  const shareText = buildShareText(input);

  const markdown = [
    `# ${ESOP_REVIEW_PERSONA_COPY.briefTitle}`,
    "",
    `- **Investor:** ${input.investorLabel}`,
    `- **Generated:** ${generatedAt}`,
    `- **Style:** ${styleLine}`,
    "",
    ESOP_REVIEW_PERSONA_COPY.briefIntro,
    "",
    "## Review cadence",
    `- ${ESOP_REVIEW_PERSONA_COPY.cadenceWeekly}`,
    `- ${ESOP_REVIEW_PERSONA_COPY.cadenceQuarterly}`,
    "",
    "## Weekly discipline",
    `- **Headline:** ${weekHeadline}`,
    `- **Summary:** ${summaryLine}`,
    `- **Streak:** ${input.streakCount} day${input.streakCount === 1 ? "" : "s"}`,
    "",
    "## ESOP holder rules",
    ESOP_REVIEW_PERSONA_COPY.holdCoreRule,
    "",
    ESOP_REVIEW_PERSONA_COPY.antiTrading,
    "",
    `_Personal ESOP review brief · APEX discipline infrastructure · Not investment advice._`,
  ].join("\n");

  return {
    generated_at: generatedAt,
    investor_label: input.investorLabel,
    investment_style_line: styleLine,
    week_headline: weekHeadline,
    share_text: shareText,
    markdown,
  };
}

export function downloadEsopReviewBriefMarkdown(brief: EsopReviewBrief): void {
  const blob = new Blob([brief.markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const dateKey = brief.generated_at.slice(0, 10);
  anchor.href = url;
  anchor.download = `apex-esop-review-${dateKey}.md`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function runEsopReviewBriefSelfCheck(): void {
  const brief = assembleEsopReviewBrief({
    investorLabel: "Arjun",
    investmentStyle: "long_term_only",
    streakCount: 5,
    reviewWeeklyUrl: "https://apex.example/app/review?tab=weekly",
    reviewQuarterlyUrl: "https://apex.example/app/review?tab=quarterly",
    summary: {
      wins: 0,
      losses: 0,
      open: 0,
      waitDays: 5,
      executedDays: 0,
      followedDays: 3,
    },
    generatedAt: "2026-08-11T10:00:00.000Z",
  });

  if (!brief.markdown.includes("Review cadence") || !brief.share_text.includes("Weekly review:")) {
    throw new Error("ESOP review brief self-check failed: markdown shape");
  }

  if (!brief.investment_style_line.includes("Long-term")) {
    throw new Error("ESOP review brief self-check failed: style line");
  }
}
