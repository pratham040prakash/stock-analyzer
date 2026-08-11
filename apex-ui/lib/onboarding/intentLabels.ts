import type { UserIntent } from "@/types/intent";

/** UI-only labels — API values remain grow | protect | explore */
export const INTENT_UI_LABELS: Record<
  UserIntent,
  { label: string; hint: string; tagline: string }
> = {
  grow: {
    label: "Deploy tactical",
    hint: "Act when setup confirms",
    tagline: "Tactical deployment decision",
  },
  protect: {
    label: "Protect capital",
    hint: "Safety before new risk",
    tagline: "Capital protection decision",
  },
  explore: {
    label: "Stay in cash",
    hint: "Watch without deploying",
    tagline: "Capital stays idle",
  },
};

export function getIntentUiLabel(intent: UserIntent): string {
  return INTENT_UI_LABELS[intent].label;
}
