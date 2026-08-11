import { assembleReviewCadencePackage } from "@/services/review/assembleReviewCadence";
import { buildReviewDigest } from "@/services/review/reviewDigest";
import { sendReviewDigest } from "@/services/review/sendReviewDigest";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type ReviewDigestCronResult = {
  enabled: boolean;
  users: number;
  sent: number;
  failed: number;
  ran_at: string;
};

export async function runReviewDigestCron(
  adminClient: Client,
): Promise<ReviewDigestCronResult> {
  const enabled = process.env.APEX_REVIEW_DIGEST_ENABLED === "true";
  const ranAt = new Date().toISOString();

  if (!enabled) {
    return { enabled: false, users: 0, sent: 0, failed: 0, ran_at: ranAt };
  }

  const channel =
    process.env.APEX_REVIEW_DIGEST_CHANNEL === "email" ? "email" : "telegram";

  const { data: connections, error } = await adminClient
    .from("broker_connections")
    .select("user_id")
    .eq("broker", "zerodha")
    .eq("status", "active");

  if (error) {
    throw new Error(error.message);
  }

  const userIds = [
    ...new Set((connections ?? []).map((row) => row.user_id).filter(Boolean)),
  ];

  let sent = 0;
  let failed = 0;

  for (const userId of userIds) {
    try {
      const review = await assembleReviewCadencePackage(adminClient, userId);
      const digest = buildReviewDigest(review, channel);
      const delivery = await sendReviewDigest(digest);

      if (delivery.sent) {
        sent += 1;
      } else {
        failed += 1;
      }
    } catch {
      failed += 1;
    }
  }

  return {
    enabled: true,
    users: userIds.length,
    sent,
    failed,
    ran_at: ranAt,
  };
}

export function runReviewDigestCronSelfCheck(): void {
  if (typeof runReviewDigestCron !== "function") {
    throw new Error("Review digest cron self-check failed");
  }
}
