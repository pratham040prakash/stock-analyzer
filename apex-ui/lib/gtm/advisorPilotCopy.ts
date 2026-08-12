/** T4-3 — RIA / advisor B2B pilot copy (receipts + review seats). */

export const ADVISOR_PILOT_COPY = {
  panelTitle: "Advisor review pack",
  panelBody:
    "Export a read-only markdown bundle for your RIA or coach — weekly discipline summary plus recent decision receipts.",
  seatsLabel: "Pilot includes {seats} review seat{seatSuffix} per advisor.",
  seatsDetail:
    "Seats are read-only review access for an external advisor — not trading or execution.",
  exportButton: "Download advisor pack",
  exportHint: "Share the .md file over secure email — no leaderboard, no social feed.",
  settingsTitle: "Advisor pilot",
  settingsBody:
    "B2B pilot for RIAs reviewing client discipline. Export packs from Review or here.",
  packTitle: "APEX Advisor Review Pack",
  packIntro:
    "Read-only discipline record for advisor review. Broker truth and receipts — not tips or performance marketing.",
  emptyReceipts: "No decision receipts in this window yet.",
} as const;

export function formatAdvisorSeatsLabel(seats: number): string {
  const seatSuffix = seats === 1 ? "" : "s";
  return ADVISOR_PILOT_COPY.seatsLabel
    .replace("{seats}", String(seats))
    .replace("{seatSuffix}", seatSuffix);
}

export function runAdvisorPilotCopySelfCheck(): void {
  if (!ADVISOR_PILOT_COPY.panelTitle || !ADVISOR_PILOT_COPY.exportButton) {
    throw new Error("Advisor pilot copy self-check failed: missing labels");
  }

  const sample = formatAdvisorSeatsLabel(1);

  if (!sample.includes("1 review seat")) {
    throw new Error("Advisor pilot copy self-check failed: seats label");
  }
}
