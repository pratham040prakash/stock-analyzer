import { apiError, apiOk } from "@/lib/api/response";
import { createClient } from "@/lib/supabase/server";
import {
  isAutoTradingEnabled,
  setAutoTradingEnabled,
} from "@/lib/tradingPreferences";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const enabled = await isAutoTradingEnabled(supabase, user.id);

  return apiOk({ autoTradingEnabled: enabled });
}

type AutoTradingRequest = {
  enabled?: boolean;
};

export async function PATCH(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: AutoTradingRequest;

  try {
    body = (await request.json()) as AutoTradingRequest;
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  if (typeof body.enabled !== "boolean") {
    return apiError("enabled must be a boolean", 400);
  }

  await setAutoTradingEnabled(supabase, user.id, body.enabled);

  return apiOk({ autoTradingEnabled: body.enabled });
}
