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
