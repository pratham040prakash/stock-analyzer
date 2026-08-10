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

/** Safely parse JSON API bodies — never throws on empty or invalid responses. */
export async function parseApiJson<T>(
  res: Response,
  label = "API",
): Promise<T | null> {
  console.log(`${label} response status:`, res.status);

  if (!res.ok) {
    console.error(`${label} failed`, res.status);
  }

  let text = "";
  try {
    text = await res.text();
  } catch (err) {
    console.error(`${label} failed to read response body`, err);
    return null;
  }

  if (!text.trim()) {
    console.error(`${label} returned empty body`);
    return null;
  }

  try {
    return JSON.parse(text) as T;
  } catch (err) {
    console.error(`${label} invalid JSON response`, err);
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

export async function apiFetchJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
  label = "API",
): Promise<{ response: Response; data: T | null }> {
  const response = await apiFetch(input, init);
  const data = await parseApiJson<T>(response, label);
  return { response, data };
}
