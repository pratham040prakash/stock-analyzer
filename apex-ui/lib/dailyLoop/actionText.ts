import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import { isSellAction, type DecisionActionType } from "@/types/decision";

type ActionTextDecision = {
  action: DecisionActionType | string;
  stock?: string;
};

export function getDecisionActionText(
  decision: ActionTextDecision,
  entryTiming: EntryTimingState,
): string {
  const action = decision.action;
  const stock = decision.stock;

  if (action === "buy" && stock) {
    return entryTiming.enter ? `Buy ${stock} today.` : `Prepare to buy ${stock}.`;
  }

  if (action === "wait" || action === "hold") {
    return "Stay in cash today.";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return stock ? `Reduce ${stock} today.` : "Reduce exposure today.";
  }

  if (action === "explore") {
    return "Watch the market today.";
  }

  return "Stay in cash today.";
}
