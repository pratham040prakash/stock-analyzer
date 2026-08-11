const DEFAULT_INIT: RequestInit = {
  credentials: "include",
  cache: "no-store",
};

/** Same-origin API calls that must send Supabase session cookies. */
export function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  return fetch(input, {
    ...DEFAULT_INIT,
    ...init,
    credentials: init?.credentials ?? DEFAULT_INIT.credentials,
    cache: init?.cache ?? DEFAULT_INIT.cache,
  });
}

const isDevLogging =
  typeof process !== "undefined" && process.env.NODE_ENV === "development";

/** Safely parse JSON API bodies — never throws on empty or invalid responses. */
export async function parseApiJson<T>(
  res: Response,
  label = "API",
): Promise<T | null> {
  if (isDevLogging) {
    console.log(`${label} response status:`, res.status);
  }

  if (!res.ok && isDevLogging) {
    console.error(`${label} failed`, res.status);
  }

  let text = "";
  try {
    text = await res.text();
  } catch (err) {
    if (isDevLogging) {
      console.error(`${label} failed to read response body`, err);
    }
    return null;
  }

  if (!text.trim()) {
    if (isDevLogging) {
      console.error(`${label} returned empty body`);
    }
    return null;
  }

  try {
    return JSON.parse(text) as T;
  } catch (err) {
    if (isDevLogging) {
      console.error(`${label} invalid JSON response`, err);
    }
    return null;
  }
}

type ApiEnvelope = {
  status?: string;
  message?: string;
};

/** Read server error text from APEX API envelopes. */
export function readApiErrorMessage(
  data: ApiEnvelope | null | undefined,
  fallback: string,
): string {
  if (data?.status === "error" && typeof data.message === "string" && data.message) {
    return data.message;
  }

  return fallback;
}

export type TradeExecutionError = {
  message: string;
  needsZerodhaReconnect: boolean;
};

/** Map trade API failures to user-facing copy and reconnect affordances. */
export function readTradeExecutionError(
  res: Response,
  data: ApiEnvelope | null | undefined,
  fallback: string,
): TradeExecutionError {
  const message = readApiErrorMessage(data, fallback);
  const needsZerodhaReconnect =
    res.status === 401 ||
    res.status === 409 ||
    /session expired|not connected|reconnect/i.test(message);

  return { message, needsZerodhaReconnect };
}

export function runTradeExecutionErrorSelfCheck(): void {
  const expired = readTradeExecutionError(
    { status: 401 } as Response,
    { status: "error", message: "Zerodha session expired — reconnect to trade" },
    "fallback",
  );
  if (!expired.needsZerodhaReconnect) {
    throw new Error("Trade error self-check failed: expired session must prompt reconnect");
  }

  const marketClosed = readTradeExecutionError(
    { status: 400 } as Response,
    { status: "error", message: "Market is closed. NSE cash orders execute 9:15 AM – 3:30 PM IST, Monday–Friday." },
    "fallback",
  );
  if (marketClosed.needsZerodhaReconnect) {
    throw new Error("Trade error self-check failed: market closed must not prompt reconnect");
  }
}

export async function apiFetchJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
  label = "API",
): Promise<{ response: Response; data: T | null }> {
  const response = await apiFetch(input, init);
  const data = await parseApiJson<T>(response, label);
  return { response, data };
}
