"use client";

import type { TodayDataFreshness } from "@/lib/dailyLoop/todayDataFreshness";
import { TODAY_SYNC_RECOVERY } from "@/lib/dailyLoop/todaySyncRecoveryCopy";

type Props = {
  freshness: TodayDataFreshness;
  onSoftRefresh?: () => void;
  refreshing?: boolean;
  autoRetryInProgress?: boolean;
  autoRetryDetail?: string;
};

export default function TodaySyncStatusBanner({
  freshness,
  onSoftRefresh,
  refreshing = false,
  autoRetryInProgress = false,
  autoRetryDetail,
}: Props) {
  if (autoRetryInProgress) {
    return (
      <div
        className="rounded-xl border border-apex-border/20 bg-white/[0.03] px-4 py-3"
        role="status"
        aria-live="polite"
      >
        <p className="text-sm font-medium text-apex-text/85">
          {TODAY_SYNC_RECOVERY.autoRetryLabel}
        </p>
        <p className="mt-1 text-xs leading-snug text-apex-muted/75">
          {autoRetryDetail ?? TODAY_SYNC_RECOVERY.autoRetryDetail}
        </p>
      </div>
    );
  }

  if (!freshness.isStale) {
    return null;
  }

  const showSoftRefresh =
    freshness.showSoftRefresh && typeof onSoftRefresh === "function";

  return (
    <div
      className="rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-3"
      role="status"
      aria-live="polite"
    >
      <p className="text-sm font-medium text-amber-100/95">{freshness.headline}</p>
      <p className="mt-1 text-xs leading-snug text-amber-100/75">{freshness.detail}</p>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        {showSoftRefresh ? (
          <button
            type="button"
            onClick={onSoftRefresh}
            disabled={refreshing}
            className="text-xs font-medium text-amber-50 underline underline-offset-2 hover:text-white disabled:cursor-wait disabled:opacity-70"
          >
            {refreshing
              ? TODAY_SYNC_RECOVERY.softRefreshLoading
              : freshness.softRefreshLabel}
          </button>
        ) : null}
        <a
          href={freshness.reconnectHref}
          className="text-xs font-medium text-amber-100/80 underline underline-offset-2 hover:text-amber-50"
        >
          {TODAY_SYNC_RECOVERY.reconnectLabel}
        </a>
      </div>
    </div>
  );
}
