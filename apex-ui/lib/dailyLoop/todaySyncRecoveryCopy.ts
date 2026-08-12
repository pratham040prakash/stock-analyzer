/** T7 — Today sync recovery: soft refresh before full reconnect. */

export const TODAY_SYNC_RECOVERY = {
  softRefreshLabel: "Refresh now",
  softRefreshLoading: "Refreshing…",
  reconnectLabel: "Reconnect Zerodha",
  portfolioStaleDetail:
    "Cash may still be accurate. Refresh holdings first — reconnect only if it still looks wrong.",
  pollErrorDetail: "Live quotes may lag. Refresh to retry before reconnecting.",
  fundsSyncDetailSuffix: "Refresh to retry, or reconnect if the issue persists.",
  autoRetryLabel: "Refreshing portfolio…",
  autoRetryDetail: "Checking for a fresh sync before showing a warning.",
} as const;

export function runTodaySyncRecoveryCopySelfCheck(): void {
  if (!TODAY_SYNC_RECOVERY.softRefreshLabel.includes("Refresh")) {
    throw new Error("Today sync recovery self-check failed: soft refresh label");
  }

  if (TODAY_SYNC_RECOVERY.portfolioStaleDetail.includes("Reconnect Zerodha")) {
    throw new Error(
      "Today sync recovery self-check failed: stale detail should not duplicate reconnect CTA",
    );
  }
}
