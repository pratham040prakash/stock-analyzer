"use client";

import { useEffect, useState } from "react";
import { isDev } from "@/lib/env";
import { isSystemConfigured, SYSTEM_CONFIG_INCOMPLETE_MESSAGE } from "@/lib/env/config";
import { apiFetch } from "@/lib/api/clientFetch";

export default function DevDebugBadge() {
  const [brokerConfigured, setBrokerConfigured] = useState(true);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!isDev) return;

    apiFetch("/api/zerodha/config", { method: "GET" })
      .then((res) => res.json())
      .then((data: { configured?: boolean }) => {
        setBrokerConfigured(Boolean(data.configured));
      })
      .catch(() => {
        setBrokerConfigured(false);
      })
      .finally(() => {
        setChecked(true);
      });
  }, []);

  if (!isDev || !checked) {
    return null;
  }

  const authConfigured = isSystemConfigured();
  const backendReady = authConfigured && brokerConfigured;

  if (backendReady) {
    return null;
  }

  return (
    <div
      className="fixed bottom-4 right-4 z-50 text-xs text-amber-300/90 bg-slate-900/95 border border-amber-500/25 px-3 py-2 rounded-lg shadow-lg pointer-events-none"
      aria-hidden
    >
      {SYSTEM_CONFIG_INCOMPLETE_MESSAGE}
    </div>
  );
}
