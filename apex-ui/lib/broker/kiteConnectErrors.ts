const NOT_ENABLED_PATTERNS = [
  "not enabled for the app",
  "user is not enabled",
] as const;

export const KITE_NOT_ENABLED_MESSAGE =
  "This Zerodha account is not enabled for APEX yet. Continue setup now — you can connect Kite later for live holdings.";

export function isKiteUserNotEnabledError(message: string): boolean {
  const lower = message.toLowerCase();
  return NOT_ENABLED_PATTERNS.some((pattern) => lower.includes(pattern));
}

export function mapKiteConnectError(message: string): string {
  if (isKiteUserNotEnabledError(message)) {
    return KITE_NOT_ENABLED_MESSAGE;
  }

  const lower = message.toLowerCase();
  if (lower.includes("checksum") || lower.includes("api_secret")) {
    return "Broker credentials mismatch. Check ZERODHA_API_KEY and ZERODHA_API_SECRET on Vercel.";
  }
  if (lower.includes("token") && lower.includes("invalid")) {
    return "Login link expired. Click Connect Zerodha again.";
  }

  return message;
}

export function runKiteConnectErrorsSelfCheck(): void {
  const mapped = mapKiteConnectError(
    "The user is not enabled for the app. InputException",
  );

  if (mapped !== KITE_NOT_ENABLED_MESSAGE) {
    throw new Error("Kite connect error self-check failed: not-enabled map");
  }

  if (!isKiteUserNotEnabledError('{"message":"The user is not enabled for the app."}')) {
    throw new Error("Kite connect error self-check failed: detect JSON page");
  }
}
