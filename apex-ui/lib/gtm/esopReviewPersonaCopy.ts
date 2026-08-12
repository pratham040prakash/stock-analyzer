/** T4-5 — Corporate ESOP holder: long-term + review persona copy. */

export const ESOP_REVIEW_PERSONA_COPY = {
  panelTitle: "ESOP review rhythm",
  panelBody:
    "Treat vested ESOP like sacred core — review on a calendar, not on every tick. Weekly discipline plus quarterly allocation checks beat panic sells.",
  settingsTitle: "ESOP review persona",
  settingsBody:
    "Long-term holder playbook for vested grants. Process and review cadence — not daily trading tips.",
  briefTitle: "APEX ESOP Review Brief",
  briefIntro:
    "Personal discipline brief for corporate ESOP holders. Sacred core stays off Today; review weekly and quarterly — not on every drawdown.",
  cadenceWeekly: "Weekly — discipline summary and receipts (Review → Weekly).",
  cadenceQuarterly: "Quarterly — allocation drift and doctor alerts (Review → Quarterly).",
  holdCoreRule:
    "Do not trim vested ESOP on fear. If concentration rises, plan a staged review — not an intraday reaction.",
  antiTrading:
    "Not employer stock tips, not exercise timing advice — discipline infrastructure only.",
  copyButton: "Copy review summary",
  copySuccess: "ESOP review summary copied.",
  downloadButton: "Download ESOP brief",
  downloadHint: "Markdown for your CA or personal records — no leaderboard.",
  howItWorksCardTitle: "Corporate ESOP holders",
  howItWorksCardBody:
    "Vested grants belong in long-term core. APEX keeps them off Today’s tactical verdicts so you review on a schedule — weekly discipline, quarterly allocation — instead of panic-selling on volatility.",
} as const;

export function runEsopReviewPersonaCopySelfCheck(): void {
  if (
    !ESOP_REVIEW_PERSONA_COPY.panelTitle ||
    !ESOP_REVIEW_PERSONA_COPY.briefTitle ||
    !ESOP_REVIEW_PERSONA_COPY.holdCoreRule
  ) {
    throw new Error("ESOP review persona copy self-check failed: missing labels");
  }

  if (!ESOP_REVIEW_PERSONA_COPY.antiTrading.includes("Not employer stock tips")) {
    throw new Error("ESOP review persona copy self-check failed: anti-trading line");
  }
}
