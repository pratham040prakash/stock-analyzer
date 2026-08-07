import axios from "axios";
import { createHash } from "crypto";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";

export async function exchangeRequestToken(
  requestToken: string,
): Promise<string> {
  const config = getZerodhaConfig();

  if (!config.configured) {
    throw new Error(config.reason);
  }

  const apiKey = config.apiKey;
  const apiSecret = process.env.ZERODHA_API_SECRET?.trim();

  if (!apiSecret) {
    throw new Error("ZERODHA_API_SECRET is not configured");
  }

  const checksum = createHash("sha256")
    .update(apiKey + requestToken + apiSecret)
    .digest("hex");

  const body = new URLSearchParams({
    api_key: apiKey,
    request_token: requestToken,
    checksum,
  });

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

  const accessToken = response.data?.data?.access_token;

  if (typeof accessToken !== "string" || !accessToken) {
    throw new Error("Invalid token response from Zerodha");
  }

  return accessToken;
}

export const KITE_ACCESS_TOKEN_COOKIE = "kite_access_token";

export const kiteAccessTokenCookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge: 60 * 60 * 24,
};
