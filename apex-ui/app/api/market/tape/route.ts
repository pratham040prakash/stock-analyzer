import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { getTapeRegimeSafe } from "@/services/market/regime";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const tape = await getTapeRegimeSafe();

  return NextResponse.json(
    { status: "ok", tape },
    { headers: { "Cache-Control": "no-store, must-revalidate" } },
  );
}
