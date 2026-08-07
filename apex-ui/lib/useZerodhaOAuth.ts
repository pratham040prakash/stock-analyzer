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

/** Legacy fallback: forward homepage request_token hits to the server callback route. */
export function useZerodhaOAuth(): OAuthState {
  const [state, setState] = useState<OAuthState>({
    isCompletingOAuth: false,
    oauthError: null,
  });

  useEffect(() => {
    const requestToken = readRequestToken();
    if (!requestToken) return;

    setState({ isCompletingOAuth: true, oauthError: null });

    const params = new URLSearchParams(window.location.search);
    params.set("request_token", requestToken);
    window.location.replace(`/api/zerodha/callback?${params.toString()}`);
  }, []);

  return state;
}
