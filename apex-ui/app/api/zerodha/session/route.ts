import { apiError, apiOk } from "@/lib/api/response";
import { brokerError, brokerLog } from "@/lib/broker/log";
import {
  exchangeRequestToken,
  KITE_ACCESS_TOKEN_COOKIE,
  kiteAccessTokenCookieOptions,
} from "@/lib/broker/zerodhaSession";
import { isTokenEncryptionConfigured } from "@/lib/crypto/encrypt";
import {
  getBrokerConnectionStatus,
  upsertBrokerConnection,
} from "@/services/broker/connections";
import { syncUserPortfolio } from "@/services/portfolio/sync";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

type SessionRequest = {
  request_token?: string;
};

export async function GET() {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return apiOk({ connected: false, authenticated: false });
    }

    const connection = await getBrokerConnectionStatus(supabase, user.id);

    brokerLog("Zerodha session status", {
      user_id: user.id,
      connected: connection.connected,
      kite_user_id: connection.kiteUserId,
    });

    return apiOk({
      connected: connection.connected,
      authenticated: true,
      status: connection.status,
      kite_user_id: connection.kiteUserId,
    });
  } catch (err) {
    brokerError("Zerodha session API error", {
      message: err instanceof Error ? err.message : "Unknown error",
    });

    return apiError("Internal server error", 500);
  }
}

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
    const session = await exchangeRequestToken(requestToken);

    await upsertBrokerConnection(supabase, user.id, "zerodha", {
      accessToken: session.accessToken,
      publicToken: session.publicToken,
      kiteUserId: session.kiteUserId,
    });

    const syncResult = await syncUserPortfolio(supabase, user.id);

    const res = apiOk({ connected: true, sync: syncResult.status });

    res.cookies.set(
      KITE_ACCESS_TOKEN_COOKIE,
      session.accessToken,
      kiteAccessTokenCookieOptions,
    );

    return res;
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Token exchange failed";
    return apiError(message, 502);
  }
}
