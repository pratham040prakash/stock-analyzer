import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  EXPLORE_EMPTY_HEADLINE,
  formatJudgment,
} from "@/lib/dailyLoop/apexVoice";
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
    return "What is interesting today";
  }

  if (intent === "protect") {
    if (action === "wait" || action === "hold") {
      return EXPLORE_EMPTY_HEADLINE;
    }

    if (isSellAction(action as DecisionActionType) || action === "sell") {
      return stock
        ? formatJudgment(`Trim ${stock} to protect capital`, "worth tracking")
        : formatJudgment("Trim exposure to protect capital", "worth tracking");
    }

    if (action === "buy" && stock) {
      return formatJudgment(`${stock} must confirm first`, "not ready yet");
    }

    return EXPLORE_EMPTY_HEADLINE;
  }

  if (action === "buy" && stock) {
    return entryTiming.enter
      ? formatJudgment(`Stage entry in ${stock}`, "worth tracking")
      : formatJudgment(`${stock} needs confirmation`, "not ready yet");
  }

  if (action === "wait" || action === "hold") {
    return EXPLORE_EMPTY_HEADLINE;
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return stock
      ? formatJudgment(`Reduce ${stock} today`, "worth tracking")
      : formatJudgment("Reduce exposure today", "worth tracking");
  }

  if (action === "explore") {
    return "What is interesting today";
  }

  return EXPLORE_EMPTY_HEADLINE;
}
