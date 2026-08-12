"use client";

import type { TodayDataFreshness } from "@/lib/dailyLoop/todayDataFreshness";

type Props = {
  freshness: TodayDataFreshness;
};

export default function TodaySyncStatusBanner({ freshness }: Props) {
  if (!freshness.isStale) {
    return null;
  }

  return (
    <div
      className="rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-3"
      role="status"
      aria-live="polite"
    >
      <p className="text-sm font-medium text-amber-100/95">{freshness.headline}</p>
      <p className="mt-1 text-xs leading-snug text-amber-100/75">{freshness.detail}</p>
      <a
        href={freshness.reconnectHref}
        className="mt-2 inline-block text-xs font-medium text-amber-50 underline underline-offset-2 hover:text-white"
      >
        Reconnect Zerodha
      </a>
    </div>
  );
}
