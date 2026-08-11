import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assembleContextualLesson } from "@/services/learning/assembleContextualLesson";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const lesson = await assembleContextualLesson(supabase, user.id);

  return NextResponse.json({ status: "ok", lesson });
}
