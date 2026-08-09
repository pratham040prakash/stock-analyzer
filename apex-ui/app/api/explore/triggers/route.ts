import { apiError, apiOk } from "@/lib/api/response";
import { normalizeSymbol } from "@/lib/stockPool";
import { getExploreLiveTriggers } from "@/services/explore/liveTriggers";
import type { StockPick } from "@/types/decision";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

type TriggersRequest = {
  picks?: StockPick[];
};

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: TriggersRequest;

  try {
    body = (await request.json()) as TriggersRequest;
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  const picks = (body.picks ?? [])
    .filter((pick) => pick?.stock)
    .slice(0, 5)
    .map((pick) => ({
      ...pick,
      stock: normalizeSymbol(pick.stock),
    }));

  if (picks.length === 0) {
    return apiOk({ triggers: [] });
  }

  const triggers = await getExploreLiveTriggers(supabase, user.id, picks);

  return apiOk({ triggers });
}
