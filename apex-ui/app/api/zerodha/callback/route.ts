import { NextResponse } from "next/server";
import { authError, authLog } from "@/lib/auth/log";
import {
  exchangeRequestToken,
  KITE_ACCESS_TOKEN_COOKIE,
  kiteAccessTokenCookieOptions,
} from "@/lib/broker/zerodhaSession";
import { isTokenEncryptionConfigured } from "@/lib/crypto/encrypt";
import { resolveAppBaseUrl } from "@/lib/env/config";
import { hasActiveBrokerConnection, upsertBrokerConnection } from "@/services/broker/connections";
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

function mapZerodhaError(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("checksum") || lower.includes("api_secret")) {
    return "Broker credentials mismatch. Check ZERODHA_API_KEY and ZERODHA_API_SECRET on Vercel.";
  }
  if (lower.includes("token") && lower.includes("invalid")) {
    return "Login link expired. Click Connect Zerodha again.";
  }
  return message;
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const requestToken = url.searchParams.get("request_token");
  const baseUrl = resolveAppBaseUrl(url.origin) || url.origin;

  if (!requestToken) {
    return redirectHome(baseUrl, {
      zerodha_error: "Missing broker login token. Try connecting again.",
    });
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const redirectUrl = new URL("/login", baseUrl);
    redirectUrl.searchParams.set("next", "/api/zerodha/login");
    return NextResponse.redirect(redirectUrl);
  }

  if (!isTokenEncryptionConfigured()) {
    return redirectHome(baseUrl, {
      zerodha_error:
        "Server encryption is not configured. Set TOKEN_ENCRYPTION_KEY on Vercel.",
    });
  }

  try {
    const alreadyConnected = await hasActiveBrokerConnection(supabase, user.id);
    if (alreadyConnected) {
      authLog("Zerodha callback: already connected", { userId: user.id });
      return redirectHome(baseUrl, { zerodha: "connected" });
    }

    const accessToken = await exchangeRequestToken(requestToken);
    await upsertBrokerConnection(supabase, user.id, "zerodha", accessToken);

    const res = redirectHome(baseUrl, { zerodha: "connected" });
    res.cookies.set(
      KITE_ACCESS_TOKEN_COOKIE,
      accessToken,
      kiteAccessTokenCookieOptions,
    );

    try {
      const syncResult = await syncUserPortfolio(supabase, user.id);
      if (syncResult.status !== "OK") {
        authError("Zerodha connected but portfolio sync deferred", {
          status: syncResult.status,
          message:
            syncResult.status === "ERROR" ? syncResult.message : syncResult.status,
        });
        res.headers.set("x-apex-sync", syncResult.status);
      } else {
        authLog("Zerodha callback complete", { userId: user.id });
      }
    } catch (syncErr) {
      authError("Zerodha connected but portfolio sync failed", {
        message:
          syncErr instanceof Error ? syncErr.message : "Unknown sync error",
      });
    }

    return res;
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Token exchange failed";
    authError("Zerodha callback failed", { message });
    return redirectHome(baseUrl, {
      zerodha_error: mapZerodhaError(message),
    });
  }
}
