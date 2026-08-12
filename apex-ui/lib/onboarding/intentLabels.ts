import type { UserIntent } from "@/types/intent";

/** UI-only labels — API values remain grow | protect | explore */
export const INTENT_UI_LABELS: Record<
  UserIntent,
  { label: string; hint: string; tagline: string; lens: string }
> = {
  grow: {
    label: "Trade",
    hint: "When a setup confirms",
    tagline: "Today's trade decision",
    lens: "See what blocks your next entry",
  },
  protect: {
    label: "Protect",
    hint: "Trim risk before new buys",
    tagline: "Today's risk decision",
    lens: "See guards and trim alerts",
  },
  explore: {
    label: "Watch",
    hint: "Track ideas — stay in cash",
    tagline: "Today's watchlist",
    lens: "See what's building without deploying",
  },
};

export function getIntentUiLabel(intent: UserIntent): string {
  return INTENT_UI_LABELS[intent].label;
}
