import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  getFinancialProfileFromDb,
  upsertFinancialProfile,
} from "@/services/portfolio/repository";
import {
  type ExpenseRange,
  type FinancialProfile,
  type IncomeRange,
  getInvestableSurplus,
} from "@/lib/financialProfile";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const profile = await getFinancialProfileFromDb(supabase, user.id);

  if (!profile) {
    return NextResponse.json({ profile: null });
  }

  return NextResponse.json({
    profile,
    investableSurplus: getInvestableSurplus(profile),
  });
}

type FinancialProfileRequest = {
  incomeRange?: IncomeRange;
  expenseRange?: ExpenseRange;
};

export async function PUT(req: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: FinancialProfileRequest;

  try {
    body = (await req.json()) as FinancialProfileRequest;
  } catch {
    return apiError("Invalid request body", 400);
  }

  if (!body.incomeRange || !body.expenseRange) {
    return apiError("incomeRange and expenseRange are required", 400);
  }

  const profile: FinancialProfile = {
    incomeRange: body.incomeRange,
    expenseRange: body.expenseRange,
  };

  await upsertFinancialProfile(supabase, user.id, profile);

  return NextResponse.json({
    profile,
    investableSurplus: getInvestableSurplus(profile),
  });
}
