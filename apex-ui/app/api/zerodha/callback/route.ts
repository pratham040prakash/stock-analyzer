import { NextResponse } from "next/server";
import { brokerError, brokerLog } from "@/lib/broker/log";
import {
  exchangeRequestToken,
  KITE_ACCESS_TOKEN_COOKIE,
  kiteAccessTokenCookieOptions,
} from "@/lib/broker/zerodhaSession";
import { isTokenEncryptionConfigured } from "@/lib/crypto/encrypt";
import { resolveAppBaseUrl } from "@/lib/env/config";
import {
  hasActiveBrokerConnection,
  mapBrokerDbError,
  upsertBrokerConnection,
} from "@/services/broker/connections";
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
  const mapped = mapBrokerDbError(message);
  if (mapped !== message) return mapped;

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

  brokerLog("Zerodha callback hit", {
    has_request_token: Boolean(requestToken),
    origin: url.origin,
  });

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
    brokerError("Zerodha callback without Supabase session");
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
      brokerLog("Zerodha callback: already connected", { userId: user.id });
      return redirectHome(baseUrl, { zerodha: "connected" });
    }

    const session = await exchangeRequestToken(requestToken);

    await upsertBrokerConnection(supabase, user.id, "zerodha", {
      accessToken: session.accessToken,
      publicToken: session.publicToken,
      kiteUserId: session.kiteUserId,
    });

    const res = redirectHome(baseUrl, { zerodha: "connected" });
    res.cookies.set(
      KITE_ACCESS_TOKEN_COOKIE,
      session.accessToken,
      kiteAccessTokenCookieOptions,
    );

    try {
      const syncResult = await syncUserPortfolio(supabase, user.id);
      if (syncResult.status !== "OK") {
        brokerError("Zerodha connected but portfolio sync deferred", {
          userId: user.id,
          status: syncResult.status,
          message:
            syncResult.status === "ERROR" ? syncResult.message : syncResult.status,
        });
      } else {
        brokerLog("Zerodha callback complete", { userId: user.id });
      }
    } catch (syncErr) {
      brokerError("Zerodha connected but portfolio sync failed", {
        userId: user.id,
        message:
          syncErr instanceof Error ? syncErr.message : "Unknown sync error",
      });
    }

    return res;
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Token exchange failed";
    brokerError("Zerodha callback failed", { userId: user.id, message });
    return redirectHome(baseUrl, {
      zerodha_error: mapZerodhaError(message),
    });
  }
}
