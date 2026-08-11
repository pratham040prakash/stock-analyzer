import { apiError, apiOk } from "@/lib/api/response";
import { assembleMonthlyDoctor } from "@/services/review/assembleMonthlyDoctor";
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
    const doctor = await assembleMonthlyDoctor(supabase, user.id);
    return apiOk({ doctor });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load monthly doctor";
    return apiError(message, 500);
  }
}
