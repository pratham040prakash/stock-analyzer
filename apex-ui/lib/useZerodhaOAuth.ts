"use client";

import { useEffect, useState } from "react";

type OAuthState = {
  isCompletingOAuth: boolean;
  oauthError: string | null;
};

function readRequestToken(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("request_token");
}

export function useZerodhaOAuth(): OAuthState {
  const [state, setState] = useState<OAuthState>({
    isCompletingOAuth: false,
    oauthError: null,
  });

  useEffect(() => {
    const requestToken = readRequestToken();
    if (!requestToken) return;

    let cancelled = false;

    async function completeLogin() {
      setState({ isCompletingOAuth: true, oauthError: null });

      try {
        const res = await fetch("/api/zerodha/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ request_token: requestToken }),
        });

        const data = (await res.json().catch(() => null)) as {
          error?: string;
        } | null;

        if (!res.ok) {
          throw new Error(data?.error ?? "Session creation failed");
        }

        if (cancelled) return;

        window.history.replaceState({}, "", "/");
        window.location.reload();
      } catch (err) {
        if (cancelled) return;

        const message =
          err instanceof Error ? err.message : "OAuth connection failed";
        console.error("OAuth error:", err);
        setState({ isCompletingOAuth: false, oauthError: message });
      }
    }

    void completeLogin();

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
