import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assembleReviewCadencePackage } from "@/services/review/assembleReviewCadence";
import { buildReviewDigest } from "@/services/review/reviewDigest";
import { sendReviewDigest } from "@/services/review/sendReviewDigest";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const channelParam = searchParams.get("channel");
  const channel =
    channelParam === "email" || channelParam === "telegram"
      ? channelParam
      : "none";

  const review = await assembleReviewCadencePackage(supabase, user.id);
  const digest = buildReviewDigest(review, channel);

  return NextResponse.json({ status: "ok", digest });
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let channel: "email" | "telegram" | "none" = "telegram";

  try {
    const body = (await request.json()) as { channel?: string };
    if (body.channel === "email" || body.channel === "telegram") {
      channel = body.channel;
    }
  } catch {
    // default channel
  }

  const review = await assembleReviewCadencePackage(supabase, user.id);
  const digest = buildReviewDigest(review, channel);
  const delivery = await sendReviewDigest(digest);

  return NextResponse.json({
    status: "ok",
    digest,
    delivery,
  });
}
