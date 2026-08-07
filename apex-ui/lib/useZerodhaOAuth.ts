"use client";

import { useEffect, useState } from "react";

type OAuthState = {
  isCompletingOAuth: boolean;
};

function readRequestToken(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("request_token");
}

/** Legacy fallback: forward homepage request_token hits to the server callback route. */
export function useZerodhaOAuth(): OAuthState {
  const [isCompletingOAuth, setIsCompletingOAuth] = useState(
    () => Boolean(readRequestToken()),
  );

  useEffect(() => {
    const requestToken = readRequestToken();
    if (!requestToken) return;

    setIsCompletingOAuth(true);

    const params = new URLSearchParams(window.location.search);
    params.set("request_token", requestToken);
    window.location.replace(`/api/zerodha/callback?${params.toString()}`);
  }, []);

  return { isCompletingOAuth };
}
