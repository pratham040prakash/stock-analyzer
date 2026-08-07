import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  exchangeRequestToken,
  KITE_ACCESS_TOKEN_COOKIE,
  kiteAccessTokenCookieOptions,
} from "@/lib/broker/zerodhaSession";
import { isTokenEncryptionConfigured } from "@/lib/crypto/encrypt";
import { resolveAppBaseUrl } from "@/lib/env/config";
import { upsertBrokerConnection } from "@/services/broker/connections";
import { syncUserPortfolio } from "@/services/portfolio/sync";
import { createClient } from "@/lib/supabase/server";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const requestToken = url.searchParams.get("request_token");
  const baseUrl = resolveAppBaseUrl(url.origin);

  if (!requestToken) {
    return apiError("Missing request_token", 400);
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const redirectUrl = new URL("/login", baseUrl || url.origin);
    redirectUrl.searchParams.set("next", "/");
    return NextResponse.redirect(redirectUrl);
  }

  if (!isTokenEncryptionConfigured()) {
    return apiError("TOKEN_ENCRYPTION_KEY is not configured", 500);
  }

  try {
    const accessToken = await exchangeRequestToken(requestToken);
    await upsertBrokerConnection(supabase, user.id, "zerodha", accessToken);
    await syncUserPortfolio(supabase, user.id);

    const res = NextResponse.redirect(new URL("/", baseUrl || url.origin));
    res.cookies.set(
      KITE_ACCESS_TOKEN_COOKIE,
      accessToken,
      kiteAccessTokenCookieOptions,
    );
    return res;
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Token exchange failed";
    return apiError(message, 502);
  }
}
