/** Investment journey copy — plan-first, no return guarantees. */

export const JOURNEY_COPY = {
  panelTitle: "Your target path",
  panelSubtitle:
    "A plan you set — APEX stays with you until you review or reach the target.",
  startTitle: "Set a target path",
  startDescription:
    "Pick a price target and horizon. We track progress and guide the next step — not predict returns.",
  horizonLongTerm: "Long-term",
  horizonLongTermHint: "Months to years · accumulate in zones",
  horizonSwing: "Swing",
  horizonSwingHint: "2–6 weeks · tactical move only",
  targetLabel: "Target price (₹)",
  entryLabel: "Entry price (₹) — optional",
  amountLabel: "Amount in this plan (₹) — optional",
  swingWeeksLabel: "Swing window (weeks)",
  saveJourney: "Start this path",
  completeJourney: "Target reached — close path",
  pauseJourney: "Pause path",
  progressLabel: "Progress toward target",
  investedLabel: "In this plan",
  daysLabel: "Days on path",
  disclaimer:
    "ESTIMATE · Targets are your plan, not guarantees. Past path ≠ future results.",
  guidance: {
    planning:
      "Lock your target, then wait for Today’s confirmation before acting.",
    waiting_entry:
      "Entry not confirmed yet. Waiting is part of the path — not a failure.",
    in_position:
      "You’re in the position. Next checkpoint: hold the plan unless thesis breaks.",
    on_path:
      "You’re moving toward your target. Review at each checkpoint — don’t chase.",
    near_target:
      "Near your target zone. Decide: take profit, trim, or reset the plan.",
    target_reached:
      "Target zone reached. Close this path and record what you learned.",
    review:
      "Revisit your thesis before adding more. Protect capital first.",
  },
  path: {
    plan: "Plan locked",
    wait: "Wait for entry",
    enter: "Enter when confirmed",
    hold: "Hold the plan",
    checkpoint: "Mid-path check",
    target: "Target review",
  },
} as const;

export function runJourneyCopySelfCheck(): void {
  if (!JOURNEY_COPY.disclaimer.toLowerCase().includes("not guarantees")) {
    throw new Error("Journey copy self-check failed: disclaimer");
  }
}
