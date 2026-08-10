import { apiError, apiOk } from "@/lib/api/response";
import { getOpenMonitorPositions } from "@/services/monitor/openPositions";
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

  const { positions, dayPnl } = await getOpenMonitorPositions(supabase, user.id);

  return apiOk({
    positions,
    dayPnl,
  });
}
