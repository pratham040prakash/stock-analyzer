import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assembleMorningBrief } from "@/services/brief/assembleMorningBrief";
import { createClient } from "@/lib/supabase/server";
import { parseUserIntent, resolveIntent } from "@/types/intent";
import type { MorningBriefResponse } from "@/types/morningBrief";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const intent = resolveIntent(parseUserIntent(searchParams.get("intent")));

  try {
    const brief = await assembleMorningBrief(supabase, user.id, intent);
    const payload: MorningBriefResponse = {
      status: brief.status,
      brief,
    };

    return NextResponse.json(payload, {
      headers: { "Cache-Control": "no-store, must-revalidate" },
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Could not assemble morning brief";

    const payload: MorningBriefResponse = {
      status: "error",
      brief: null,
      message,
    };

    return NextResponse.json(payload, { status: 500 });
  }
}
