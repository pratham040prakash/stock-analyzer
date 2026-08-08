import type { UserIntent } from "@/types/intent";

type HeroToneInput = {
  intent: UserIntent;
  action: string;
};

export function getHeroTone({ intent, action }: HeroToneInput): string {
  if (intent === "explore") {
    return "Observe without pressure — clarity beats speed.";
  }

  if (intent === "protect") {
    if (action === "sell" || action === "reduce") {
      return "Protecting what you've built comes first.";
    }

    if (action === "buy") {
      return "Only exceptional setups clear the bar today.";
    }

    return "Nothing strong enough deserves risk.";
  }

  if (action === "buy") {
    return "A clear setup — move with intention, not urgency.";
  }

  return "Calm conditions matter more than action.";
}
