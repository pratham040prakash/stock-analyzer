import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { createClient } from "@/lib/supabase/server";
import { repairStoredJourney } from "@/lib/journey/journeyPlanSanitize";
import {
  updateJourneyStatus,
  upsertActiveJourney,
} from "@/services/journey/repository";
import { resolveInvestmentJourneyDbError } from "@/services/journey/errors";
import type {
  JourneyStatus,
  StoredInvestmentJourney,
} from "@/types/investmentJourney";

function parseJourneyBody(body: unknown): StoredInvestmentJourney | null {
  if (!body || typeof body !== "object") {
    return null;
  }

  const record = body as Partial<StoredInvestmentJourney>;
  if (
    typeof record.symbol !== "string" ||
    typeof record.horizon !== "string" ||
    typeof record.targetPriceInr !== "number" ||
    typeof record.startedAt !== "string"
  ) {
    return null;
  }

  const journey: StoredInvestmentJourney = {
    id: typeof record.id === "string" ? record.id : `journey_${Date.now()}`,
    symbol: record.symbol,
    horizon: record.horizon === "swing" ? "swing" : "long_term",
    targetPriceInr: Math.round(record.targetPriceInr),
    entryPriceInr:
      typeof record.entryPriceInr === "number"
        ? Math.round(record.entryPriceInr)
        : undefined,
    investedAmountInr:
      typeof record.investedAmountInr === "number"
        ? Math.round(record.investedAmountInr)
        : undefined,
    startedAt: record.startedAt,
    targetBy: typeof record.targetBy === "string" ? record.targetBy : undefined,
    targetDurationAmount:
      typeof record.targetDurationAmount === "number"
        ? record.targetDurationAmount
        : undefined,
    targetDurationUnit:
      record.targetDurationUnit === "days" ||
      record.targetDurationUnit === "weeks" ||
      record.targetDurationUnit === "years"
        ? record.targetDurationUnit
        : undefined,
    status:
      record.status === "completed" || record.status === "paused"
        ? record.status
        : "active",
    notes: typeof record.notes === "string" ? record.notes : undefined,
    suggestedByApex: record.suggestedByApex === true,
    chartBasis:
      record.chartBasis && typeof record.chartBasis === "object"
        ? record.chartBasis
        : undefined,
  };

  return repairStoredJourney(journey);
}

function parseStatus(value: unknown): JourneyStatus | null {
  return value === "active" || value === "completed" || value === "paused"
    ? value
    : null;
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return apiError("Invalid request body", 400);
  }

  const parsed = parseJourneyBody(body);
  if (!parsed || parsed.targetPriceInr <= 0) {
    return apiError("Invalid journey payload", 400);
  }

  parsed.status = "active";

  if (
    parsed.entryPriceInr !== undefined &&
    parsed.targetPriceInr <= parsed.entryPriceInr
  ) {
    return apiError("Target must be above entry", 400);
  }

  try {
    const journey = await upsertActiveJourney(supabase, user.id, parsed);
    return NextResponse.json({ journey });
  } catch (error) {
    const resolved = resolveInvestmentJourneyDbError(error);
    return apiError(resolved.message, resolved.status);
  }
}

export async function PATCH(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: { id?: unknown; status?: unknown };

  try {
    body = (await request.json()) as { id?: unknown; status?: unknown };
  } catch {
    return apiError("Invalid request body", 400);
  }

  if (typeof body.id !== "string" || !body.id.trim()) {
    return apiError("id is required", 400);
  }

  const status = parseStatus(body.status);
  if (!status || status === "active") {
    return apiError("status must be completed or paused", 400);
  }

  try {
    const journey = await updateJourneyStatus(
      supabase,
      user.id,
      body.id.trim(),
      status,
    );

    if (!journey) {
      return apiError("Journey not found", 404);
    }

    return NextResponse.json({ journey });
  } catch (error) {
    const resolved = resolveInvestmentJourneyDbError(error);
    return apiError(resolved.message, resolved.status);
  }
}
