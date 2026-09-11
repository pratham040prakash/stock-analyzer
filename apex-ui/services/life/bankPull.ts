import type { SupabaseClient } from "@supabase/supabase-js";
import {
  reviewBankPayload,
  type BankMonthReview,
} from "@/lib/life/bankAggregator";
import { createBankSession, fetchBankSession } from "@/lib/life/setuClient";
import { markLifeBankConsent } from "@/services/life/bankStore";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export function sessionReady(status: string): boolean {
  return status === "COMPLETED" || status === "PARTIAL";
}

export async function startBankSession(
  supabase: Client,
  consentId: string,
): Promise<void> {
  await createBankSession(consentId);
  await markLifeBankConsent(supabase, consentId, { status: "active" });
}

export async function storeBankSession(
  supabase: Client,
  consentId: string,
  sessionId: string,
): Promise<BankMonthReview | null> {
  const payload = await fetchBankSession(sessionId);
  const review = reviewBankPayload(payload);
  if (review.rowCount <= 0) {
    await markLifeBankConsent(supabase, consentId, { status: "failed" });
    return null;
  }

  await markLifeBankConsent(supabase, consentId, {
    status: "fetched",
    review,
  });
  return review;
}

export async function applyBankNotification(
  supabase: Client,
  payload: unknown,
): Promise<{ handled: boolean; status?: string }> {
  const body = asRecord(payload);
  if (!body) {
    return { handled: false };
  }

  const type = String(body.type ?? "");
  const consentId = String(body.consentId ?? "");
  if (!consentId) {
    return { handled: false };
  }

  if (type === "CONSENT_STATUS_UPDATE" || type === "CONSENT_STATUS") {
    const status = String(asRecord(body.data)?.status ?? body.status ?? "").toUpperCase();
    if (status === "ACTIVE" || status === "APPROVED") {
      await startBankSession(supabase, consentId);
      return { handled: true, status: "active" };
    }
    if (status === "REJECTED" || status === "REVOKED") {
      await markLifeBankConsent(supabase, consentId, { status: "rejected" });
      return { handled: true, status: "rejected" };
    }
    return { handled: true, status: status.toLowerCase() };
  }

  if (type === "FI_DATA_READY") {
    const review = reviewBankPayload(body);
    if (review.rowCount <= 0) {
      await markLifeBankConsent(supabase, consentId, { status: "failed" });
      return { handled: true, status: "failed" };
    }
    await markLifeBankConsent(supabase, consentId, { status: "fetched", review });
    return { handled: true, status: "fetched" };
  }

  if (type === "SESSION_STATUS_UPDATE") {
    const status = String(asRecord(body.data)?.status ?? body.status ?? "").toUpperCase();
    const sessionId = String(body.dataSessionId ?? asRecord(body.data)?.id ?? "");
    if (sessionReady(status) && sessionId) {
      await storeBankSession(supabase, consentId, sessionId);
      return { handled: true, status: "fetched" };
    }
    if (status === "FAILED" || status === "EXPIRED") {
      await markLifeBankConsent(supabase, consentId, { status: "failed" });
      return { handled: true, status: "failed" };
    }
    return { handled: true, status: status.toLowerCase() };
  }

  if (type === "FI_DATA_FAILED") {
    await markLifeBankConsent(supabase, consentId, { status: "failed" });
    return { handled: true, status: "failed" };
  }

  return { handled: false };
}

export function runBankPullSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Bank pull self-check failed: ${message}`);
    }
  };
  assert(sessionReady("COMPLETED"), "Completed session must fetch");
  assert(sessionReady("PARTIAL"), "Partial session must still fetch ready accounts");
  assert(!sessionReady("PENDING"), "Pending session must wait");
}
