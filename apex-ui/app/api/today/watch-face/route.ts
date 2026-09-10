import { apiError, apiOk } from "@/lib/api/response";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { watchFaceState } from "@/lib/dailyLoop/deskHorizon";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import { readServerContract } from "@/services/desk/contractStore";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const contract = await readServerContract(
    createAdminClient(),
    user.id,
    tradingDateKey(),
  );

  return apiOk({ face: watchFaceState(contract) });
}
