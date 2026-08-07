import { apiError, apiOk } from "@/lib/api/response";
import { authError, authLog } from "@/lib/auth/log";
import {
  resolveAuthCallbackUrl,
  SYSTEM_CONFIG_INCOMPLETE_MESSAGE,
} from "@/lib/env/config";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/server";

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export async function POST(request: Request) {
  if (!isSupabaseConfigured()) {
    return apiError(SYSTEM_CONFIG_INCOMPLETE_MESSAGE, 503);
  }

  let body: { email?: string };
  try {
    body = await request.json();
  } catch {
    return apiError("Invalid request body", 400);
  }

  const email = body.email?.trim() ?? "";
  if (!email || !isValidEmail(email)) {
    return apiError("Enter a valid email", 400);
  }

  const origin = new URL(request.url).origin;
  const emailRedirectTo = resolveAuthCallbackUrl(origin);
  authLog("Email OTP request (server)", { emailRedirectTo });

  try {
    const supabase = await createClient();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo,
        shouldCreateUser: true,
      },
    });

    if (error) {
      authError("Email OTP request failed", { message: error.message });
      return apiError(error.message, 400);
    }

    authLog("Email OTP sent (server)", { emailRedirectTo });
    return apiOk({ redirectTo: emailRedirectTo });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Unable to send login link.";
    authError("Email OTP exception", { message });
    return apiError(message, 500);
  }
}
