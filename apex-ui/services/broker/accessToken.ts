import { cookies } from "next/headers";
import { KITE_ACCESS_TOKEN_COOKIE } from "@/lib/broker/zerodhaSession";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";
import { getActiveBrokerConnection } from "@/services/broker/connections";

type Client = SupabaseClient<Database>;

export type ResolvedZerodhaAccessToken = {
  accessToken: string;
  source: "db" | "cookie";
};

async function readKiteAccessTokenCookie(): Promise<string | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(KITE_ACCESS_TOKEN_COOKIE)?.value?.trim();
  return token || null;
}

/** All non-duplicate Zerodha tokens available for this session. */
export async function listZerodhaAccessTokenCandidates(
  supabase: Client,
  userId: string,
): Promise<ResolvedZerodhaAccessToken[]> {
  const candidates: ResolvedZerodhaAccessToken[] = [];
  const seen = new Set<string>();

  const connection = await getActiveBrokerConnection(supabase, userId);
  if (connection?.status === "active" && connection.accessToken) {
    candidates.push({ accessToken: connection.accessToken, source: "db" });
    seen.add(connection.accessToken);
  }

  const cookieToken = await readKiteAccessTokenCookie();
  if (cookieToken && !seen.has(cookieToken)) {
    candidates.push({ accessToken: cookieToken, source: "cookie" });
  }

  return candidates;
}

/** Prefer stored broker connection token; fall back to the post-login HttpOnly cookie. */
export async function resolveZerodhaAccessToken(
  supabase: Client,
  userId: string,
): Promise<ResolvedZerodhaAccessToken | null> {
  const candidates = await listZerodhaAccessTokenCandidates(supabase, userId);
  return candidates[0] ?? null;
}

/** Alternate token source for retry when the primary Kite call fails auth. */
export async function resolveAlternateZerodhaAccessToken(
  supabase: Client,
  userId: string,
  used: ResolvedZerodhaAccessToken,
): Promise<ResolvedZerodhaAccessToken | null> {
  if (used.source === "db") {
    const cookieToken = await readKiteAccessTokenCookie();
    if (cookieToken && cookieToken !== used.accessToken) {
      return { accessToken: cookieToken, source: "cookie" };
    }
    return null;
  }

  const connection = await getActiveBrokerConnection(supabase, userId);
  if (
    connection?.status === "active" &&
    connection.accessToken &&
    connection.accessToken !== used.accessToken
  ) {
    return { accessToken: connection.accessToken, source: "db" };
  }

  return null;
}
