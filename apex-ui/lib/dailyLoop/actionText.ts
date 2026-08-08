import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { UserIntent } from "@/types/intent";

type ActionTextDecision = {
  action: DecisionActionType | string;
  stock?: string;
};

export function getDecisionActionText(
  decision: ActionTextDecision,
  entryTiming: EntryTimingState,
  intent: UserIntent,
): string {
  const action = decision.action;
  const stock = decision.stock;

  if (intent === "explore") {
    return "Watch and learn today.";
  }

  if (intent === "protect") {
    if (action === "wait" || action === "hold") {
      return "Stay in cash today.";
    }

    if (isSellAction(action as DecisionActionType) || action === "sell") {
      return stock ? `Protect capital — reduce ${stock}.` : "Protect capital today.";
    }

    if (action === "buy" && stock) {
      return `Only act if ${stock} confirms.`;
    }

    return "Stay in cash today.";
  }

  // grow
  if (action === "buy" && stock) {
    return entryTiming.enter
      ? `Deploy into ${stock} today.`
      : `Prepare to buy ${stock}.`;
  }

  if (action === "wait" || action === "hold") {
    return "Stay in cash today.";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return stock ? `Reduce ${stock} today.` : "Reduce exposure today.";
  }

  if (action === "explore") {
    return "Watch and learn today.";
  }

  return "Stay in cash today.";
}
