import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  listInvestmentTheses,
  upsertInvestmentThesis,
} from "@/services/thesis/thesisRepository";
import type { InvestmentThesisInput } from "@/types/investmentThesis";
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
    const theses = await listInvestmentTheses(supabase, user.id);
    return NextResponse.json({ status: "ok", theses });
  } catch (error) {
    return apiError(
      error instanceof Error ? error.message : "Could not load theses",
      500,
    );
  }
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: InvestmentThesisInput;

  try {
    body = (await request.json()) as InvestmentThesisInput;
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  try {
    const thesis = await upsertInvestmentThesis(supabase, user.id, body);

    if (!thesis) {
      return apiError("symbol and thesis required", 400);
    }

    return NextResponse.json({ status: "ok", thesis });
  } catch (error) {
    return apiError(
      error instanceof Error ? error.message : "Could not save thesis",
      500,
    );
  }
}
