import type { UserIntent } from "@/types/intent";

/** UI-only labels — API values remain grow | protect | explore */
export const INTENT_UI_LABELS: Record<
  UserIntent,
  { label: string; hint: string; tagline: string; lens: string }
> = {
  grow: {
    label: "Deploy",
    hint: "New buys when a setup confirms",
    tagline: "Today's deploy view",
    lens: "See what blocks your next entry",
  },
  protect: {
    label: "Risk",
    hint: "Trims and guards first",
    tagline: "Today's risk view",
    lens: "See guards and trim alerts",
  },
  explore: {
    label: "Ideas",
    hint: "Watchlist — cash stays put",
    tagline: "Today's ideas view",
    lens: "See what's building without deploying",
  },
};

export function getIntentUiLabel(intent: UserIntent): string {
  return INTENT_UI_LABELS[intent].label;
}
