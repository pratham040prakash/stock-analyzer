import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  getOperatingProfileFromDb,
  upsertOperatingProfile,
} from "@/services/operatingProfile/repository";
import {
  isOperatingProfileComplete,
  parseInvestmentStyle,
  type OperatingProfile,
} from "@/types/operatingProfile";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const profile = await getOperatingProfileFromDb(supabase, user.id);

  return NextResponse.json({
    profile,
    complete: isOperatingProfileComplete(profile),
  });
}

type OperatingProfileRequest = {
  investmentStyle?: string;
  intradayAcknowledged?: boolean;
};

export async function PUT(req: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: OperatingProfileRequest;

  try {
    body = (await req.json()) as OperatingProfileRequest;
  } catch {
    return apiError("Invalid request body", 400);
  }

  const investmentStyle = parseInvestmentStyle(body.investmentStyle);

  if (!investmentStyle) {
    return apiError("investmentStyle is required", 400);
  }

  if (body.intradayAcknowledged !== true) {
    return apiError("intradayAcknowledged must be true before using Today", 400);
  }

  const profile: OperatingProfile = {
    investmentStyle,
    intradayAcknowledgedAt: new Date().toISOString(),
  };

  await upsertOperatingProfile(supabase, user.id, profile);

  return NextResponse.json({
    profile,
    complete: true,
  });
}
