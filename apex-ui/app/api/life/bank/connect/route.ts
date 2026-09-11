import { apiError, apiOk } from "@/lib/api/response";
import {
  mobileLast4,
  normalizeIndianMobile,
  readSetuConfig,
} from "@/lib/life/bankAggregator";
import { createBankConsent } from "@/lib/life/setuClient";
import { upsertLifeBankConsent } from "@/services/life/bankStore";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const config = readSetuConfig();
  if (!config.configured) {
    return apiError("Bank rail is not configured.", 503);
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: { mobile?: string };
  try {
    body = (await request.json()) as { mobile?: string };
  } catch {
    return apiError("Invalid request body", 400);
  }

  const mobile = normalizeIndianMobile(body.mobile ?? "");
  if (!mobile) {
    return apiError("Enter the 10-digit mobile on the bank account.", 400);
  }

  try {
    const consent = await createBankConsent(mobile);
    await upsertLifeBankConsent(supabase, {
      userId: user.id,
      consentId: consent.consentId,
      status: "pending",
      mobileLast4: mobileLast4(mobile),
    });
    return apiOk({ url: consent.url, consentId: consent.consentId });
  } catch {
    return apiError("The bank rail would not open a consent screen.", 502);
  }
}
