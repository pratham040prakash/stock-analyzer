const PLACEHOLDER_VALUES = new Set([
  "",
  "your_api_key",
  "your_api_secret",
  "changeme",
  "replace_me",
]);

export type ZerodhaConfigStatus =
  | { configured: true; apiKey: string }
  | { configured: false; reason: string };

export function getZerodhaConfig(): ZerodhaConfigStatus {
  const apiKey = process.env.ZERODHA_API_KEY?.trim();
  const apiSecret = process.env.ZERODHA_API_SECRET?.trim();

  if (!apiKey || !apiSecret) {
    return {
      configured: false,
      reason:
        "ZERODHA_API_KEY and ZERODHA_API_SECRET must be set in environment variables",
    };
  }

  if (
    PLACEHOLDER_VALUES.has(apiKey) ||
    PLACEHOLDER_VALUES.has(apiSecret)
  ) {
    return {
      configured: false,
      reason:
        "Replace placeholder Zerodha credentials with your Kite Connect API key and secret",
    };
  }

  return { configured: true, apiKey };
}
