"use client";

import { useEffect, useState } from "react";
import { getMarketOrderBlockReason } from "@/lib/broker/marketSession";

const DEFAULT_POLL_MS = 60_000;

/** Re-evaluate NSE session gates on an interval so pre-market UI unlocks at 9:15 IST. */
export function useMarketSession(pollMs = DEFAULT_POLL_MS) {
  const [blockReason, setBlockReason] = useState<string | null>(() =>
    getMarketOrderBlockReason(),
  );

  useEffect(() => {
    const refresh = () => {
      setBlockReason(getMarketOrderBlockReason());
    };

    refresh();
    const intervalId = window.setInterval(refresh, pollMs);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [pollMs]);

  return {
    blockReason,
    canPlaceMarketOrder: blockReason === null,
  };
}
