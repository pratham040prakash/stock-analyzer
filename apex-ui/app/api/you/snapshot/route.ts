import { apiError, apiOk } from "@/lib/api/response";
import { assembleYouSnapshot } from "@/services/you/assembleYouSnapshot";
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

  try {
    const snapshot = await assembleYouSnapshot(supabase, user.id);
    return apiOk({ snapshot });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load You snapshot";
    return apiError(message, 500);
  }
}
