import { NextResponse } from "next/server";
import { authError, authLog } from "@/lib/auth/log";
import {
  resolveAppBaseUrl,
  SYSTEM_CONFIG_INCOMPLETE_MESSAGE,
} from "@/lib/env/config";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const baseUrl = resolveAppBaseUrl(origin);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/";
  const oauthError = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");

  if (!isSupabaseConfigured()) {
    authError("Callback failed: Supabase ENV missing");
    return NextResponse.redirect(
      `${baseUrl}/login?error=${encodeURIComponent(SYSTEM_CONFIG_INCOMPLETE_MESSAGE)}`,
    );
  }

  if (oauthError) {
    authError("OAuth callback error", {
      oauthError,
      errorDescription,
    });
    return NextResponse.redirect(
      `${baseUrl}/login?error=${encodeURIComponent(errorDescription ?? oauthError)}`,
    );
  }

  if (code) {
    const supabase = await createClient();
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error && data.session) {
      authLog("Session created via callback", {
        userId: data.session.user.id,
      });
      return NextResponse.redirect(`${baseUrl}${next}`);
    }

    authError("exchangeCodeForSession failed", {
      message: error?.message ?? "Unknown error",
    });
    return NextResponse.redirect(
      `${baseUrl}/login?error=${encodeURIComponent(error?.message ?? "auth_callback_failed")}`,
    );
  }

  authError("Callback missing auth code");
  return NextResponse.redirect(`${baseUrl}/login?error=auth_callback_failed`);
}
