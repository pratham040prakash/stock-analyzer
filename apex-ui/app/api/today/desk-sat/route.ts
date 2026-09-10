import { apiError, apiOk } from "@/lib/api/response";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { markDeskSat } from "@/lib/dailyLoop/deskHorizon";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import { readServerContract, writeServerContract } from "@/services/desk/contractStore";

export const dynamic = "force-dynamic";

export async function POST() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const desk = createAdminClient();
  const dateKey = tradingDateKey();
  const contract = await readServerContract(desk, user.id, dateKey);
  if (!contract) {
    return apiError("No contract today", 409);
  }

  const sat = markDeskSat();
  const saved = await writeServerContract(desk, user.id, {
    ...contract,
    deskSatAt: sat.deskSatAt,
  });

  return apiOk({ deskSatAt: sat.deskSatAt, line: sat.line, contract: saved });
}
