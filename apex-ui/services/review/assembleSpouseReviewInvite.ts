import { formatDisciplineSummary } from "@/lib/dailyLoop/disciplineHistoryMerge";
import { buildWeeklyReviewHeadline } from "@/lib/dailyLoop/weeklyReview";
import { SPOUSE_REVIEW_INVITE_COPY } from "@/lib/gtm/spouseReviewInviteCopy";
import type { DisciplineHistorySummary } from "@/types/decisionHistory";

export type SpouseReviewInviteInput = {
  investorLabel: string;
  summary: DisciplineHistorySummary;
  streakCount: number;
  howItWorksUrl: string;
  generatedAt?: string;
};

export type SpouseReviewInvite = {
  generated_at: string;
  investor_label: string;
  week_headline: string;
  share_text: string;
  mailto_subject: string;
  mailto_href: string;
  how_it_works_url: string;
};

function buildShareText(input: SpouseReviewInviteInput): string {
  const weekHeadline = buildWeeklyReviewHeadline(input.summary);
  const summaryLine = formatDisciplineSummary(input.summary);
  const streakLine =
    input.streakCount > 0
      ? `${input.streakCount} day discipline streak`
      : "Building a daily discipline streak";

  return [
    SPOUSE_REVIEW_INVITE_COPY.shareIntro,
    "",
    weekHeadline,
    summaryLine,
    streakLine,
    "",
    `How APEX works: ${input.howItWorksUrl}`,
    "",
    SPOUSE_REVIEW_INVITE_COPY.shareClosing,
  ].join("\n");
}

export function assembleSpouseReviewInvite(
  input: SpouseReviewInviteInput,
): SpouseReviewInvite {
  const generatedAt = input.generatedAt ?? new Date().toISOString();
  const shareText = buildShareText(input);
  const mailtoSubject = SPOUSE_REVIEW_INVITE_COPY.mailSubject;
  const mailtoHref = `mailto:?subject=${encodeURIComponent(mailtoSubject)}&body=${encodeURIComponent(shareText)}`;

  return {
    generated_at: generatedAt,
    investor_label: input.investorLabel,
    week_headline: buildWeeklyReviewHeadline(input.summary),
    share_text: shareText,
    mailto_subject: mailtoSubject,
    mailto_href: mailtoHref,
    how_it_works_url: input.howItWorksUrl,
  };
}

export function runSpouseReviewInviteSelfCheck(): void {
  const invite = assembleSpouseReviewInvite({
    investorLabel: "Meera",
    streakCount: 4,
    howItWorksUrl: "https://apex.example/app/you/how-it-works",
    summary: {
      wins: 1,
      losses: 0,
      open: 0,
      waitDays: 4,
      executedDays: 1,
      followedDays: 2,
    },
    generatedAt: "2026-08-11T10:00:00.000Z",
  });

  if (!invite.share_text.includes("weekly review summary")) {
    throw new Error("Spouse review invite self-check failed: share intro");
  }

  if (!invite.mailto_href.startsWith("mailto:")) {
    throw new Error("Spouse review invite self-check failed: mailto href");
  }

  if (!invite.share_text.includes("Most days, waiting is the win")) {
    throw new Error("Spouse review invite self-check failed: anti-FOMO closing");
  }
}
