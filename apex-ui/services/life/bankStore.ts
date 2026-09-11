import type { SupabaseClient } from "@supabase/supabase-js";
import type {
  BankConsentStatus,
  BankMonthReview,
  StoredBankConsentStatus,
} from "@/lib/life/bankAggregator";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type LifeBankConsent = {
  userId: string;
  consentId: string;
  status: BankConsentStatus;
  mobileLast4: string;
  review: BankMonthReview | null;
  fetchedAt: string | null;
};

function asStatus(value: string | null): BankConsentStatus {
  if (
    value === "pending" ||
    value === "active" ||
    value === "fetched" ||
    value === "failed" ||
    value === "rejected"
  ) {
    return value;
  }
  return "off";
}

function reviewFromRow(row: Database["public"]["Tables"]["life_bank_consents"]["Row"]): BankMonthReview | null {
  if (row.row_count <= 0 && row.salary_inr <= 0 && row.needs_inr <= 0) {
    return null;
  }
  return {
    salaryInr: row.salary_inr,
    needsInr: row.needs_inr,
    leaksInr: row.leaks_inr,
    emiInr: row.emi_inr,
    rowCount: row.row_count,
  };
}

export async function readLifeBankConsent(
  supabase: Client,
  userId: string,
): Promise<LifeBankConsent | null> {
  const { data, error } = await supabase
    .from("life_bank_consents")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return {
    userId: data.user_id,
    consentId: data.consent_id,
    status: asStatus(data.status),
    mobileLast4: data.mobile_last4,
    review: reviewFromRow(data),
    fetchedAt: data.fetched_at,
  };
}

export async function readLifeBankConsentById(
  supabase: Client,
  consentId: string,
): Promise<LifeBankConsent | null> {
  const { data, error } = await supabase
    .from("life_bank_consents")
    .select("*")
    .eq("consent_id", consentId)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return {
    userId: data.user_id,
    consentId: data.consent_id,
    status: asStatus(data.status),
    mobileLast4: data.mobile_last4,
    review: reviewFromRow(data),
    fetchedAt: data.fetched_at,
  };
}

export async function upsertLifeBankConsent(
  supabase: Client,
  input: {
    userId: string;
    consentId: string;
    status: StoredBankConsentStatus;
    mobileLast4?: string;
    review?: BankMonthReview | null;
  },
): Promise<void> {
  const { error } = await supabase.from("life_bank_consents").upsert(
    {
      user_id: input.userId,
      consent_id: input.consentId,
      status: input.status,
      mobile_last4: input.mobileLast4 ?? "",
      salary_inr: input.review?.salaryInr ?? 0,
      needs_inr: input.review?.needsInr ?? 0,
      leaks_inr: input.review?.leaksInr ?? 0,
      emi_inr: input.review?.emiInr ?? 0,
      row_count: input.review?.rowCount ?? 0,
      fetched_at: input.review && input.review.rowCount > 0 ? new Date().toISOString() : null,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" },
  );

  if (error) {
    throw new Error(error.message);
  }
}

export async function markLifeBankConsent(
  supabase: Client,
  consentId: string,
  patch: {
    status?: StoredBankConsentStatus;
    review?: BankMonthReview | null;
  },
): Promise<LifeBankConsent | null> {
  const current = await readLifeBankConsentById(supabase, consentId);
  if (!current) {
    return null;
  }

  await upsertLifeBankConsent(supabase, {
    userId: current.userId,
    consentId,
    status: patch.status ?? (current.status === "off" ? "pending" : current.status),
    mobileLast4: current.mobileLast4,
    review: patch.review ?? current.review,
  });
  return readLifeBankConsentById(supabase, consentId);
}
