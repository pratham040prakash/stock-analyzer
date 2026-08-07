import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { authError, authLog } from "@/lib/auth/log";
import {
  resolveAppBaseUrl,
  SYSTEM_CONFIG_INCOMPLETE_MESSAGE,
} from "@/lib/env/config";
import { validateSupabaseEnv } from "@/lib/supabase/env";

function safeNextPath(next: string | null): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) {
    return "/";
  }
  return next;
}

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const baseUrl = resolveAppBaseUrl(requestUrl.origin);
  const code = requestUrl.searchParams.get("code");
  const next = safeNextPath(requestUrl.searchParams.get("next"));
  const oauthError = requestUrl.searchParams.get("error");
  const errorDescription = requestUrl.searchParams.get("error_description");

  if (!validateSupabaseEnv()) {
    authError("Callback failed: Supabase ENV missing");
    return NextResponse.redirect(
      `${baseUrl}/login?error=${encodeURIComponent(SYSTEM_CONFIG_INCOMPLETE_MESSAGE)}`,
    );
  }

  if (oauthError) {
    authError("OAuth callback error", { oauthError, errorDescription });
    return NextResponse.redirect(
      `${baseUrl}/login?error=${encodeURIComponent(errorDescription ?? oauthError)}`,
    );
  }

  if (!code) {
    authError("Callback missing auth code");
    return NextResponse.redirect(`${baseUrl}/login?error=auth_callback_failed`);
  }

  const redirectUrl = `${baseUrl}${next}`;
  const response = NextResponse.redirect(redirectUrl);

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options);
          });
        },
      },
    },
  );

  const { data, error } = await supabase.auth.exchangeCodeForSession(code);

  // Allow @supabase/ssr cookie adapter to flush before redirect (serverless).
  await Promise.resolve();

  if (!error && data.session) {
    authLog("Session created via callback", {
      userId: data.session.user.id,
    });
    return response;
  }

  authError("exchangeCodeForSession failed", {
    message: error?.message ?? "Unknown error",
  });
  return NextResponse.redirect(
    `${baseUrl}/login?error=${encodeURIComponent(error?.message ?? "auth_callback_failed")}`,
  );
}
