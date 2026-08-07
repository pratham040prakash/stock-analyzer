import axios from "axios";
import { createHash } from "crypto";
import { brokerError, brokerLog } from "@/lib/broker/log";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";

export type KiteSessionData = {
  accessToken: string;
  publicToken: string;
  kiteUserId: string;
};

export async function exchangeRequestToken(
  requestToken: string,
): Promise<KiteSessionData> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    throw new Error(config.reason);
  }

  const apiKey = config.apiKey;
  const apiSecret = process.env.ZERODHA_API_SECRET?.trim();

  if (!apiSecret) {
    throw new Error("ZERODHA_API_SECRET is not configured");
  }

  brokerLog("Exchanging Zerodha request_token", {
    request_token: requestToken,
    api_key: apiKey,
  });

  const checksum = createHash("sha256")
    .update(apiKey + requestToken + apiSecret)
    .digest("hex");

  const body = new URLSearchParams({
    api_key: apiKey,
    request_token: requestToken,
    checksum,
  });

  try {
    const response = await axios.post(
      "https://api.kite.trade/session/token",
      body.toString(),
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-Kite-Version": "3",
        },
      },
    );

    brokerLog("Zerodha session/token response", {
      status: response.status,
      user_id: response.data?.data?.user_id,
      has_access_token: Boolean(response.data?.data?.access_token),
      has_public_token: Boolean(response.data?.data?.public_token),
    });

    const accessToken = response.data?.data?.access_token;
    const publicToken = response.data?.data?.public_token;
    const kiteUserId = response.data?.data?.user_id;

    if (typeof accessToken !== "string" || !accessToken) {
      throw new Error("Invalid token response from Zerodha");
    }

    if (typeof publicToken !== "string" || !publicToken) {
      throw new Error("Invalid public_token response from Zerodha");
    }

    if (kiteUserId === undefined || kiteUserId === null || kiteUserId === "") {
      throw new Error("Invalid user_id response from Zerodha");
    }

    return {
      accessToken,
      publicToken,
      kiteUserId: String(kiteUserId),
    };
  } catch (err) {
    if (axios.isAxiosError(err)) {
      brokerError("Zerodha session/token failed", {
        status: err.response?.status,
        data: err.response?.data,
      });
      const message =
        (err.response?.data as { message?: string } | undefined)?.message ??
        err.message;
      throw new Error(message);
    }

    brokerError("Zerodha session/token exception", {
      message: err instanceof Error ? err.message : "Unknown error",
    });
    throw err;
  }
}

export const KITE_ACCESS_TOKEN_COOKIE = "kite_access_token";

export const kiteAccessTokenCookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production" || Boolean(process.env.VERCEL),
  sameSite: "lax" as const,
  path: "/",
  maxAge: 60 * 60 * 24,
};
