import type { ReviewCadencePackage } from "@/types/reviewCadence";
import { buildDisciplineDigestLine } from "@/services/review/disciplineDigest";

export type ReviewDigestPayload = {
  built_at: string;
  channel: "none" | "email" | "telegram";
  subject: string;
  body: string;
  discipline_line: string;
  enabled: boolean;
};

export function buildReviewDigest(
  review: ReviewCadencePackage,
  channel: "email" | "telegram" | "none" = "none",
): ReviewDigestPayload {
  const enabled = process.env.APEX_REVIEW_DIGEST_ENABLED === "true";
  const resolvedChannel = enabled ? channel : "none";

  const subject = `APEX review · ${review.monthly.month_label}`;

  const disciplineLine = buildDisciplineDigestLine(review.weekly);

  const body = [
    disciplineLine,
    "",
    review.weekly.headline,
    "",
    `Monthly: ${review.monthly.headline}`,
    review.monthly.summary,
    "",
    `Quarterly (${review.quarterly.quarter_label}): ${review.quarterly.headline}`,
    review.quarterly.summary,
    "",
    "Open APEX Review for full detail.",
  ].join("\n");

  return {
    built_at: new Date().toISOString(),
    channel: resolvedChannel,
    subject,
    body,
    discipline_line: disciplineLine,
    enabled,
  };
}

export function runReviewDigestSelfCheck(): void {
  const digest = buildReviewDigest(
    {
      built_at: new Date().toISOString(),
      weekly: {
        headline: "Test",
        summary: {
          wins: 0,
          losses: 0,
          open: 0,
          waitDays: 0,
          executedDays: 0,
          followedDays: 0,
        },
        process_score: { score: 50, streakCount: 0, message: "Test" },
        planned_summary: {
          aligned: 1,
          deviated: 0,
          planned_only: 0,
          actual_only: 0,
        },
      },
      monthly: {
        built_at: new Date().toISOString(),
        month_label: "August 2026",
        headline: "Test",
        summary: "Test",
        concentration_warning: null,
        sacred_core_ok: true,
        allocation: null,
        health: [],
        action_items: [],
        trends: [],
      },
      quarterly: {
        built_at: new Date().toISOString(),
        quarter_label: "Q3 2026",
        headline: "Test",
        summary: "Test",
        discipline_score: 50,
        aligned_days: 1,
        deviated_days: 0,
        concentration_warning: null,
        sacred_core_ok: true,
        action_items: [],
        thesis_progress: [],
        goal_framing: "Test",
      },
    },
    "email",
  );

  if (!digest.subject.includes("APEX")) {
    throw new Error("Review digest self-check failed");
  }

  if (!digest.discipline_line.includes("days followed plan")) {
    throw new Error("Review digest self-check failed: discipline line");
  }
}
