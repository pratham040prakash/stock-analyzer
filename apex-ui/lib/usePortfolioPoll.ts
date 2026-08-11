"use client";

import { useEffect } from "react";
import { LIVE_KITE_REFRESH_MS } from "@/lib/liveKiteRefresh";

type Options = {
  enabled: boolean;
  onRefresh: () => void | Promise<void>;
};

/** Silent holdings refresh — same cadence as Open P&L (live Kite quotes). */
export function usePortfolioPoll({ enabled, onRefresh }: Options) {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void onRefresh();
    }, LIVE_KITE_REFRESH_MS);

    return () => window.clearInterval(intervalId);
  }, [enabled, onRefresh]);
}
