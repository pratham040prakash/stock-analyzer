"use client";

import { useEffect, useRef } from "react";
import { LIVE_KITE_REFRESH_MS } from "@/lib/liveKiteRefresh";

type Options = {
  enabled: boolean;
  onRefresh: () => void | Promise<void>;
};

/** Silent holdings refresh — same cadence as Open P&L (live Kite quotes). */
export function usePortfolioPoll({ enabled, onRefresh }: Options) {
  const onRefreshRef = useRef(onRefresh);
  onRefreshRef.current = onRefresh;

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void onRefreshRef.current();
    }, LIVE_KITE_REFRESH_MS);

    return () => window.clearInterval(intervalId);
  }, [enabled]);
}
