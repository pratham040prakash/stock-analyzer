import { apiError } from "@/lib/api/response";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { closeLetterCalendarIcs } from "@/lib/dailyLoop/deskHorizon";
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

  const ics = closeLetterCalendarIcs(tradingDateKey());
  return new Response(ics, {
    status: 200,
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": 'attachment; filename="apex-close-letter.ics"',
    },
  });
}
