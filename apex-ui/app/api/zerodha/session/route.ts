import { apiError, apiOk } from "@/lib/api/response";
import {
  exchangeRequestToken,
  KITE_ACCESS_TOKEN_COOKIE,
  kiteAccessTokenCookieOptions,
} from "@/lib/broker/zerodhaSession";
import { isTokenEncryptionConfigured } from "@/lib/crypto/encrypt";
import { upsertBrokerConnection } from "@/services/broker/connections";
import { syncUserPortfolio } from "@/services/portfolio/sync";
import { createClient } from "@/lib/supabase/server";

type SessionRequest = {
  request_token?: string;
};

export async function POST(req: Request) {
  let body: SessionRequest;

  try {
    body = (await req.json()) as SessionRequest;
  } catch {
    return apiError("Invalid request body", 400);
  }

  const requestToken = body.request_token?.trim();

  if (!requestToken) {
    return apiError("Missing request_token", 400);
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  if (!isTokenEncryptionConfigured()) {
    return apiError("TOKEN_ENCRYPTION_KEY is not configured", 500);
  }

  try {
    const accessToken = await exchangeRequestToken(requestToken);

    await upsertBrokerConnection(supabase, user.id, "zerodha", accessToken);

    const syncResult = await syncUserPortfolio(supabase, user.id);

    const res = apiOk({ sync: syncResult.status });

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
