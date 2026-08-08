import { formatJudgment } from "@/lib/dailyLoop/apexVoice";
import type { UserIntent } from "@/types/intent";

type HeroToneInput = {
  intent: UserIntent;
  action: string;
};

export function getHeroTone({ intent, action }: HeroToneInput): string {
  if (intent === "explore") {
    return "Observe the field. Act only when clarity arrives.";
  }

  if (intent === "protect") {
    if (action === "sell" || action === "reduce") {
      return "Reduce exposure before the market asks you to.";
    }

    if (action === "buy") {
      return "Only a rare setup clears the protection bar.";
    }

    return formatJudgment("Nothing is clean enough to risk capital", "patience matters");
  }

  if (action === "buy") {
    return "Move with intention. Not urgency.";
  }

  if (action === "wait" || action === "hold") {
    return formatJudgment("Conditions are not ready", "patience matters");
  }

  return formatJudgment("Calm beats action today", "patience matters");
}
