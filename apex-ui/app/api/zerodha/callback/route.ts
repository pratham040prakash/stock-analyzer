import { NextResponse } from "next/server";
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

function redirectHome(baseUrl: string, params?: Record<string, string>) {
  const url = new URL("/", baseUrl);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }
  return NextResponse.redirect(url);
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const requestToken = url.searchParams.get("request_token");
  const baseUrl = resolveAppBaseUrl(url.origin) || url.origin;

  if (!requestToken) {
    return redirectHome(baseUrl, { zerodha_error: "missing_request_token" });
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const redirectUrl = new URL("/login", baseUrl);
    redirectUrl.searchParams.set("next", "/");
    redirectUrl.searchParams.set(
      "zerodha",
      "Sign in to APEX first, then connect Zerodha again.",
    );
    return NextResponse.redirect(redirectUrl);
  }

  if (!isTokenEncryptionConfigured()) {
    return redirectHome(baseUrl, {
      zerodha_error: "token_encryption_not_configured",
    });
  }

  try {
    const accessToken = await exchangeRequestToken(requestToken);
    await upsertBrokerConnection(supabase, user.id, "zerodha", accessToken);
    await syncUserPortfolio(supabase, user.id);

    const res = redirectHome(baseUrl, { zerodha: "connected" });
    res.cookies.set(
      KITE_ACCESS_TOKEN_COOKIE,
      accessToken,
      kiteAccessTokenCookieOptions,
    );
    return res;
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Token exchange failed";
    return redirectHome(baseUrl, { zerodha_error: message });
  }
}
