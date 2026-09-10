import { apiError, apiOk } from "@/lib/api/response";
import { shiftIstDateKey, tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import {
  assembleYearBook,
  exportYearLetters,
  monthlyDoctorFromContracts,
  waitStreak,
} from "@/lib/dailyLoop/deskHorizon";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import { listContractHistory } from "@/services/desk/contractStore";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const dateKey = tradingDateKey();
  const history = await listContractHistory(
    createAdminClient(),
    user.id,
    shiftIstDateKey(dateKey, -200),
  );

  return apiOk({
    yearBook: assembleYearBook(history),
    letters: exportYearLetters(history),
    monthly: monthlyDoctorFromContracts(history),
    waitStreak: waitStreak(history),
  });
}
