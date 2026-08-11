import { apiError, apiOk } from "@/lib/api/response";
import {
  commitDisciplineStreak,
  getDisciplineStreak,
} from "@/services/discipline/streak";
import {
  maybeOfferPremiumTrialAfterWaitReceipt,
  resolvePremiumTrialView,
} from "@/services/subscription/conversionFunnel";
import { createClient } from "@/lib/supabase/server";
import type { UserIntent } from "@/types/intent";

export const dynamic = "force-dynamic";

const VALID_INTENTS = new Set<UserIntent>(["grow", "protect", "explore"]);

function isValidIntent(value: unknown): value is UserIntent {
  return typeof value === "string" && VALID_INTENTS.has(value as UserIntent);
}

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  try {
    const streak = await getDisciplineStreak(supabase, user.id);
    return apiOk({ streak });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load discipline streak";
    return apiError(message, 500);
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

  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  if (!body || typeof body !== "object") {
    return apiError("Invalid request body", 400);
  }

  const { intent, action, stock } = body as Record<string, unknown>;

  if (!isValidIntent(intent)) {
    return apiError("Invalid intent", 400);
  }

  if (typeof action !== "string" || action.trim().length === 0) {
    return apiError("Invalid action", 400);
  }

  if (stock !== undefined && stock !== null && typeof stock !== "string") {
    return apiError("Invalid stock", 400);
  }

  try {
    const result = await commitDisciplineStreak(supabase, user.id, {
      intent,
      action: action.trim(),
      stock: typeof stock === "string" ? stock : undefined,
    });

    let trial = await resolvePremiumTrialView(supabase, user);

    if (result.receipt?.execution_kind === "WAIT" && result.receipt.id) {
      trial = await maybeOfferPremiumTrialAfterWaitReceipt(
        supabase,
        user,
        result.receipt.id,
      );
    }

    return apiOk({ streak: result.snapshot, trial });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to commit discipline";
    return apiError(message, 500);
  }
}
