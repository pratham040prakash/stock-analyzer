import type { DailyDecisionOutput } from "@/types/decision";
import type { Intent } from "@/types/intent";

export function buildUnconnectedWaitDecision(
  intent: Intent,
): DailyDecisionOutput {
  return {
    decision: "WAIT",
    action: "wait",
    intent,
    confidence: 82,
    reason:
      "Zerodha is optional to start. Today stays on Wait until Kite is linked to your real portfolio.",
    message: "You're set up — connect Zerodha when you want live holdings.",
    suggestion: "Continue without Kite, then connect later.",
    confidence_factors: [
      "No broker link yet — APEX will not size a live trade",
      "Capital context and style are enough to start the daily loop",
      "Connect Zerodha anytime for holdings, cash, and receipts",
    ],
    actions: [
      "Use Today to learn Wait · Trade · Pause",
      "Connect Zerodha when you want broker-verified holdings",
    ],
  };
}

export function runUnconnectedTodayDecisionSelfCheck(): void {
  const decision = buildUnconnectedWaitDecision("protect");

  if (decision.action !== "wait" || decision.decision !== "WAIT") {
    throw new Error("Unconnected Today self-check failed: must Wait");
  }

  if (decision.intent !== "protect") {
    throw new Error("Unconnected Today self-check failed: intent");
  }
}
