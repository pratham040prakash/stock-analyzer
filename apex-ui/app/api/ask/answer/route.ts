import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assembleAskAnswer } from "@/services/ask/assembleAskAnswer";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: { question?: string };

  try {
    body = (await request.json()) as { question?: string };
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  const question = body.question?.trim();

  if (!question || question.length > 500) {
    return apiError("Question required (max 500 chars)", 400);
  }

  const answer = await assembleAskAnswer(question);

  return NextResponse.json({ status: "ok", answer });
}
