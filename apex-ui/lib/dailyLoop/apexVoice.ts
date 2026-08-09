import type { UserIntent } from "@/types/intent";
import type { ExecutionPlanMarketRegime } from "@/services/execution/executionPlanEngine";

export type IntentEnding =
  | "worth tracking"
  | "not ready yet"
  | "wait for clarity"
  | "avoid for now"
  | "patience matters";

const FORBIDDEN_PATTERNS =
  /\b(good|bad|high probability|strong buy|weak setup)\b/i;

export function resolveIntentEnding(
  alignmentScore: number,
  intent?: UserIntent,
): IntentEnding {
  if (alignmentScore > 80) {
    return "worth tracking";
  }

  if (alignmentScore >= 65) {
    return "not ready yet";
  }

  if (intent === "protect") {
    return "avoid for now";
  }

  return "patience matters";
}

export function formatJudgment(judgment: string, ending: IntentEnding): string {
  return `${judgment} — ${ending}`;
}

export function sanitizeVoiceText(text: string): string {
  return text.replace(FORBIDDEN_PATTERNS, "").replace(/\s{2,}/g, " ").trim();
}

export function voiceRegimeObservation(regime: ExecutionPlanMarketRegime): string {
  if (regime === "Favorable") {
    return "Conditions lean supportive.";
  }

  if (regime === "Neutral") {
    return "Conditions are mixed.";
  }

  return "Conditions are defensive.";
}

export function voiceRegimeJudgment(
  regime: ExecutionPlanMarketRegime,
  intent?: UserIntent,
): string {
  if (regime === "Favorable") {
    return formatJudgment("The backdrop allows selective action", "worth tracking");
  }

  if (regime === "Neutral") {
    return formatJudgment("The backdrop offers no edge yet", "patience matters");
  }

  if (intent === "protect") {
    return formatJudgment("The backdrop argues for defense", "avoid for now");
  }

  return formatJudgment("The backdrop argues for restraint", "patience matters");
}

export function voiceStructureObservation(structureScore?: number): string | null {
  if (structureScore === undefined) {
    return null;
  }

  if (structureScore >= 70) {
    return "Price structure is clean.";
  }

  if (structureScore >= 50) {
    return "Price structure is unsettled.";
  }

  return "Price structure is fragile.";
}

export function voiceStructureJudgment(
  structureScore?: number,
  intent?: UserIntent,
): string | null {
  if (structureScore === undefined) {
    return null;
  }

  if (structureScore >= 70) {
    return formatJudgment("The chart supports attention", resolveIntentEnding(82, intent));
  }

  if (structureScore >= 50) {
    return formatJudgment("The chart needs more proof", "not ready yet");
  }

  return formatJudgment("The chart lacks clarity", resolveIntentEnding(55, intent));
}

export function voiceSignalObservation(agreement?: boolean): string | null {
  if (agreement === undefined) {
    return null;
  }

  return agreement
    ? "Trend and momentum agree."
    : "Trend and momentum diverge.";
}

export function voiceSignalJudgment(
  agreement?: boolean,
  intent?: UserIntent,
): string | null {
  if (agreement === undefined) {
    return null;
  }

  if (agreement) {
    return formatJudgment("The setup is internally consistent", "worth tracking");
  }

  return formatJudgment("The setup is not coherent yet", resolveIntentEnding(60, intent));
}

export function voiceRiskObservation(riskOk?: boolean): string | null {
  if (riskOk === false) {
    return "Portfolio risk is elevated.";
  }

  return null;
}

export function voiceRiskJudgment(intent?: UserIntent): string {
  return formatJudgment(
    "Capital needs room before new risk",
    intent === "protect" ? "avoid for now" : "patience matters",
  );
}

export function voiceConfidenceContext(
  level: "Strong" | "Moderate" | "Weak",
  regime: ExecutionPlanMarketRegime,
  hasConviction: boolean,
): string {
  const posture =
    level === "Strong"
      ? "Conviction is clear"
      : level === "Moderate"
        ? "Conviction is forming"
        : "Conviction is thin";

  const backdrop =
    regime === "Favorable"
      ? "tailwinds present"
      : regime === "Neutral"
        ? "conditions mixed"
        : "headwinds dominate";

  const convictionNote = hasConviction ? " · execution posture set" : "";

  return `${posture} · ${backdrop}${convictionNote}`;
}

type HeroSignatureInput = {
  intent: UserIntent;
  action: string;
  seed: string;
};

export function getApexHeroSignature({
  intent,
  action,
  seed,
}: HeroSignatureInput): string | null {
  let hash = 0;

  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash + seed.charCodeAt(index)) % 997;
  }

  if (hash % 5 !== 0) {
    return null;
  }

  if (
    intent === "protect" ||
    action === "wait" ||
    action === "hold" ||
    action === "explore"
  ) {
    return "APEX is protecting your capital today.";
  }

  return "APEX is staying patient with you.";
}

export const EXPLORE_EMPTY_HEADLINE = "Nothing is clean today.";
export const EXPLORE_EMPTY_BODY = "Wait.";
