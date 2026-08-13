/** Investment journey copy — chart-backed paths, no return guarantees. */

export const JOURNEY_COPY = {
  panelTitle: "Your target path",
  panelSubtitle:
    "Trust the chart-backed plan — know how long to stay patient, and we stay on the path with you.",
  trustIndicatorsLine:
    "Indicators from past candles · entry, target, and wait window — not predictions.",
  patienceTitle: "Your patience window",
  suggestTitle: "Chart-backed path",
  suggestDescription:
    "From the last ~3 months of daily closes — support, resistance, and a target zone. Not a prediction.",
  stayOnPath: "Stay on this path with me",
  adjustManually: "Adjust target manually",
  loadingPlan: "Reading recent candles…",
  insufficientData:
    "Not enough price history to map a path yet. APEX will not suggest a target without a backtrace.",
  startTitle: "Set a target path",
  startDescription:
    "Only use manual targets if you are overriding the chart-backed plan.",
  horizonLongTerm: "Long-term",
  horizonLongTermHint: "Months · support to resistance from backtrace",
  horizonSwing: "Swing",
  horizonSwingHint: "2–6 weeks · tactical move from structure",
  targetLabel: "Target price (₹)",
  entryLabel: "Entry zone (₹)",
  amountLabel: "Amount in this plan (₹) — optional",
  swingWeeksLabel: "Swing window (weeks)",
  saveJourney: "Start this path",
  completeJourney: "I sold — close path",
  takeProfitTitle: "Target reached — book profits",
  takeProfitBody:
    "Price hit your chart target. Consider selling or trimming to lock gains before resetting the plan.",
  takeProfitAction: "Sell & take profit",
  takeProfitLater: "Hold for now",
  pauseJourney: "Path broken — pause and review",
  timeTargetTitle: "How long to wait",
  timeSuggestLead: "APEX suggests a wait window from the same candle backtrace — not a return promise.",
  timeSuggestUse: "Use APEX suggestion",
  timeAdjust: "Change wait time",
  waitPreviewLead:
    "Today says Wait — this path applies if entry confirms. No new trade until then.",
  stalePlanWarning:
    "Broker sync may be stale — refresh holdings before you act. The chart path below still comes from recent price candles.",
  currentPricePending: "Now — fetching live price…",
  timeTargetHint: "Override only if your plan differs from the chart-based estimate.",
  timeAmountLabel: "Duration",
  timeUnitLabel: "Unit",
  timeTargetBy: "Target by",
  timeProgressLabel: "Time on path",
  progressLabel: "Progress toward target",
  waitBarLabel: "Not in trade",
  waitBarHint: "Live price on the path — progress starts after you enter.",
  investedLabel: "In this plan",
  daysLabel: "Days on path",
  disclaimer:
    "ESTIMATE · Levels come from past candles, not forecasts. Path ≠ guaranteed return.",
  guidance: {
    planning:
      "Path mapped from recent candles. Wait for Today’s confirmation before acting.",
    waiting_entry:
      "Entry zone not confirmed yet. Stay patient — waiting is discipline, not failure.",
    in_position:
      "You’re in the position. Hold patience until the date on this path unless support breaks.",
    on_path:
      "On path toward target. Stay patient — don’t chase; review only at checkpoints.",
    near_target:
      "Near the chart target zone. Decide: take profit, trim, or reset the path.",
    target_reached:
      "Target reached on the path above. Book profits — sell or trim before you close this path.",
    review:
      "Price broke below backtrace support — thesis may be broken. Pause and review before adding.",
  },
  path: {
    plan: "Path mapped from candles",
    wait: "Wait for entry",
    enter: "Enter in zone",
    hold: "Hold the plan",
    checkpoint: "Mid-path check",
    target: "Target review",
  },
} as const;

export function runJourneyCopySelfCheck(): void {
  if (!JOURNEY_COPY.disclaimer.toLowerCase().includes("not forecasts")) {
    throw new Error("Journey copy self-check failed: disclaimer");
  }

  if (!JOURNEY_COPY.stayOnPath.length) {
    throw new Error("Journey copy self-check failed: stayOnPath");
  }

  if (!JOURNEY_COPY.currentPricePending.includes("Now")) {
    throw new Error("Journey copy self-check failed: currentPricePending");
  }

  if (!JOURNEY_COPY.waitBarLabel.length) {
    throw new Error("Journey copy self-check failed: waitBarLabel");
  }
}
