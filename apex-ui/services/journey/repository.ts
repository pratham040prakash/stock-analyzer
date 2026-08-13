import type {
  JourneyChartBasis,
  JourneyHorizon,
  JourneyStatus,
  JourneyTimeUnit,
  StoredInvestmentJourney,
} from "@/types/investmentJourney";
import type { Database, Json } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;
type JourneyRow = Database["public"]["Tables"]["investment_journeys"]["Row"];

const SYMBOL_PATTERN = /^[A-Z0-9&.-]{1,20}$/;

function parseHorizon(value: string): JourneyHorizon | null {
  return value === "swing" || value === "long_term" ? value : null;
}

function parseStatus(value: string): JourneyStatus | null {
  return value === "active" || value === "completed" || value === "paused"
    ? value
    : null;
}

function parseTimeUnit(value: string | null): JourneyTimeUnit | undefined {
  if (value === "days" || value === "weeks" || value === "years") {
    return value;
  }

  return undefined;
}

function parseChartBasis(value: Json | null): JourneyChartBasis | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return undefined;
  }

  const record = value as Record<string, unknown>;
  const lookbackDays = record.lookbackDays;
  const backtraceSummary = record.backtraceSummary;
  const suggestedAt = record.suggestedAt;

  if (
    typeof lookbackDays !== "number" ||
    typeof backtraceSummary !== "string" ||
    typeof suggestedAt !== "string"
  ) {
    return undefined;
  }

  return {
    lookbackDays,
    backtraceSummary,
    suggestedAt,
    supportLevelInr:
      typeof record.supportLevelInr === "number"
        ? record.supportLevelInr
        : undefined,
    resistanceLevelInr:
      typeof record.resistanceLevelInr === "number"
        ? record.resistanceLevelInr
        : undefined,
    structureScore:
      typeof record.structureScore === "number"
        ? record.structureScore
        : undefined,
    suggestedWaitDays:
      typeof record.suggestedWaitDays === "number"
        ? record.suggestedWaitDays
        : undefined,
    timeSuggestionRationale:
      typeof record.timeSuggestionRationale === "string"
        ? record.timeSuggestionRationale
        : undefined,
    timeWaitLabel:
      typeof record.timeWaitLabel === "string" ? record.timeWaitLabel : undefined,
  };
}

function mapRow(row: JourneyRow): StoredInvestmentJourney {
  const horizon = parseHorizon(row.horizon);
  const status = parseStatus(row.status);

  if (!horizon || !status) {
    throw new Error("Invalid investment journey row");
  }

  return {
    id: row.id,
    symbol: row.symbol.trim().toUpperCase(),
    horizon,
    targetPriceInr: Math.round(Number(row.target_price_inr)),
    entryPriceInr:
      row.entry_price_inr === null
        ? undefined
        : Math.round(Number(row.entry_price_inr)),
    investedAmountInr:
      row.invested_amount_inr === null
        ? undefined
        : Math.round(Number(row.invested_amount_inr)),
    startedAt: row.started_at,
    targetBy: row.target_by ?? undefined,
    targetDurationAmount: row.target_duration_amount ?? undefined,
    targetDurationUnit: parseTimeUnit(row.target_duration_unit ?? null),
    status,
    notes: row.notes ?? undefined,
    suggestedByApex: row.suggested_by_apex,
    chartBasis: parseChartBasis(row.chart_basis),
  };
}

export function normalizeJourneySymbol(symbol: string): string | null {
  const normalized = symbol.trim().toUpperCase();
  return SYMBOL_PATTERN.test(normalized) ? normalized : null;
}

export async function getActiveJourneyForSymbolFromDb(
  supabase: Client,
  userId: string,
  symbol: string,
): Promise<StoredInvestmentJourney | null> {
  const normalized = normalizeJourneySymbol(symbol);
  if (!normalized) {
    return null;
  }

  const { data, error } = await supabase
    .from("investment_journeys")
    .select("*")
    .eq("user_id", userId)
    .eq("symbol", normalized)
    .eq("status", "active")
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return mapRow(data);
}

export async function upsertActiveJourney(
  supabase: Client,
  userId: string,
  journey: StoredInvestmentJourney,
): Promise<StoredInvestmentJourney> {
  const normalized = normalizeJourneySymbol(journey.symbol);
  const horizon = parseHorizon(journey.horizon);
  const status = parseStatus(journey.status);

  if (!normalized || !horizon || !status) {
    throw new Error("Invalid investment journey payload");
  }

  const existing = await getActiveJourneyForSymbolFromDb(
    supabase,
    userId,
    normalized,
  );

  const payload = {
    symbol: normalized,
    horizon,
    target_price_inr: journey.targetPriceInr,
    entry_price_inr: journey.entryPriceInr ?? null,
    invested_amount_inr: journey.investedAmountInr ?? null,
    started_at: journey.startedAt,
    target_by: journey.targetBy ?? null,
    target_duration_amount: journey.targetDurationAmount ?? null,
    target_duration_unit: journey.targetDurationUnit ?? null,
    status,
    notes: journey.notes ?? null,
    suggested_by_apex: journey.suggestedByApex ?? false,
    chart_basis: (journey.chartBasis ?? null) as Json,
    updated_at: new Date().toISOString(),
  };

  if (existing) {
    const { data, error } = await supabase
      .from("investment_journeys")
      .update(payload)
      .eq("id", existing.id)
      .eq("user_id", userId)
      .select("*")
      .single();

    if (error || !data) {
      throw error ?? new Error("Could not update investment journey");
    }

    return mapRow(data);
  }

  const { data, error } = await supabase
    .from("investment_journeys")
    .insert({ ...payload, user_id: userId })
    .select("*")
    .single();

  if (error || !data) {
    throw error ?? new Error("Could not upsert investment journey");
  }

  return mapRow(data);
}

export async function updateJourneyStatus(
  supabase: Client,
  userId: string,
  journeyId: string,
  status: JourneyStatus,
): Promise<StoredInvestmentJourney | null> {
  if (!parseStatus(status)) {
    throw new Error("Invalid journey status");
  }

  const { data, error } = await supabase
    .from("investment_journeys")
    .update({
      status,
      updated_at: new Date().toISOString(),
    })
    .eq("user_id", userId)
    .eq("id", journeyId)
    .select("*")
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return mapRow(data);
}

export function runInvestmentJourneyRepositorySelfCheck(): void {
  const sample: StoredInvestmentJourney = {
    id: "00000000-0000-4000-8000-000000000001",
    symbol: "TCS",
    horizon: "swing",
    targetPriceInr: 4200,
    entryPriceInr: 4000,
    startedAt: "2026-08-01",
    targetBy: "2026-09-01",
    status: "active",
  };

  if (normalizeJourneySymbol("tcs") !== "TCS") {
    throw new Error("Investment journey repository self-check failed: symbol");
  }

  if (sample.targetPriceInr <= sample.entryPriceInr!) {
    throw new Error("Investment journey repository self-check failed: sample");
  }
}
