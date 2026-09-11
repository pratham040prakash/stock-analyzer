import { apiError, apiOk } from "@/lib/api/response";
import { readSetuConfig, webhookSecretMatches } from "@/lib/life/bankAggregator";
import { applyBankNotification } from "@/services/life/bankPull";
import { createAdminClient } from "@/lib/supabase/admin";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const config = readSetuConfig();
  if (!config.configured) {
    return apiError("Bank rail is not configured.", 503);
  }

  const headerSecret =
    request.headers.get("x-setu-webhook-secret") ?? request.headers.get("authorization");
  if (!webhookSecretMatches(headerSecret, config.webhookSecret)) {
    return apiError("Invalid webhook signature", 401);
  }

  let payload: unknown;
  try {
    payload = (await request.json()) as unknown;
  } catch {
    return apiError("Invalid webhook payload", 400);
  }

  try {
    const result = await applyBankNotification(createAdminClient(), payload);
    return apiOk({
      handled: result.handled,
      bankStatus: result.status ?? null,
    });
  } catch {
    return apiError("Bank notification failed", 500);
  }
}
