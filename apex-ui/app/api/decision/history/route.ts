import { apiError, apiOk } from "@/lib/api/response";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
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
  const daysParam = Number(searchParams.get("days") ?? "7");
  const days = Number.isFinite(daysParam)
    ? Math.min(7, Math.max(1, Math.round(daysParam)))
    : 7;

  const result = await getDisciplineHistory(supabase, user.id, days);

  return apiOk({
    history: result.history,
    summary: result.summary,
    days: result.days,
  });
}
