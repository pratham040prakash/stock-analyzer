import {
  buildConsentBody,
  readSetuConfig,
  sixMonthDataRange,
} from "@/lib/life/bankAggregator";

type SetuConfig = ReturnType<typeof readSetuConfig>;

type TokenCache = { token: string; expiresAt: number };

let tokenCache: TokenCache | null = null;

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

async function readJson(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  try {
    return (JSON.parse(text) as Record<string, unknown>) ?? {};
  } catch {
    return { errorMsg: text.slice(0, 200) };
  }
}

function tokenFromAuth(body: Record<string, unknown>): string {
  const data = asRecord(body.data);
  const token =
    (typeof body.token === "string" && body.token) ||
    (typeof body.accessToken === "string" && body.accessToken) ||
    (typeof data?.token === "string" && data.token) ||
    (typeof data?.accessToken === "string" && data.accessToken) ||
    "";
  return token;
}

async function fetchAccessToken(config: SetuConfig): Promise<string> {
  if (tokenCache && tokenCache.expiresAt > Date.now() + 15_000) {
    return tokenCache.token;
  }

  const response = await fetch(config.authUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      clientID: config.clientId,
      secret: config.clientSecret,
    }),
  });
  const body = await readJson(response);
  const token = tokenFromAuth(body);
  if (!response.ok || !token) {
    throw new Error("Bank rail would not issue a session.");
  }

  const data = asRecord(body.data);
  const expiresIn = Number(data?.expiresIn ?? body.expiresIn ?? 1800);
  tokenCache = {
    token,
    expiresAt: Date.now() + Math.max(60, expiresIn) * 1000,
  };
  return token;
}

async function setuFetch(
  config: SetuConfig,
  path: string,
  init: RequestInit,
  retry = true,
): Promise<Record<string, unknown>> {
  const token = await fetchAccessToken(config);
  const response = await fetch(`${config.fiuBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "x-product-instance-id": config.productInstanceId,
      ...(init.headers ?? {}),
    },
  });

  if (response.status === 401 && retry) {
    tokenCache = null;
    return setuFetch(config, path, init, false);
  }

  const body = await readJson(response);
  if (!response.ok) {
    throw new Error("Bank rail rejected the request.");
  }
  return body;
}

export async function createBankConsent(mobile: string): Promise<{
  consentId: string;
  url: string;
}> {
  const config = readSetuConfig();
  if (!config.configured) {
    throw new Error("Bank rail is not configured.");
  }

  const body = await setuFetch(config, "/consents", {
    method: "POST",
    body: JSON.stringify(buildConsentBody(mobile)),
  });
  const consentId = String(body.id ?? "");
  const url = String(body.url ?? "");
  if (!consentId || !url) {
    throw new Error("Bank rail did not return a consent screen.");
  }
  return { consentId, url };
}

export async function createBankSession(consentId: string): Promise<string> {
  const config = readSetuConfig();
  const body = await setuFetch(config, "/sessions", {
    method: "POST",
    body: JSON.stringify({
      consentId,
      dataRange: sixMonthDataRange(),
      format: "json",
    }),
  });
  const sessionId = String(body.id ?? "");
  if (!sessionId) {
    throw new Error("Bank rail did not open a data session.");
  }
  return sessionId;
}

export async function fetchBankSession(sessionId: string): Promise<unknown> {
  const config = readSetuConfig();
  return setuFetch(config, `/sessions/${encodeURIComponent(sessionId)}`, {
    method: "GET",
  });
}
