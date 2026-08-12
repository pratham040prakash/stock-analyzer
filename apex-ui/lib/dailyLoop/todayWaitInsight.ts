import {
  buildCapitalDecision,
  type CapitalDecision,
} from "@/lib/dailyLoop/capitalDecision";
import type { UserIntent } from "@/types/intent";

export type TodayWaitInsight = {
  title: string;
  symbol?: string;
  blocker: string;
  unlock: string;
  footnote?: string;
};

export function buildTodayWaitInsight(input: {
  intent: UserIntent;
  capitalDecision: CapitalDecision;
}): TodayWaitInsight | null {
  const { intent, capitalDecision } = input;

  if (intent === "explore") {
    return null;
  }

  const sell = capitalDecision.actions.find((item) => item.action === "SELL");
  if (sell) {
    return {
      title: intent === "protect" ? "Protect first — trim required" : "Trim before you trade",
      symbol: sell.symbol,
      blocker:
        sell.reason.missing || "Concentration or risk limit needs a trim first.",
      unlock: sell.reason.confirm || "Complete the trim, then revisit Trade.",
      footnote: sell.postActionImpact,
    };
  }

  const wait = capitalDecision.actions.find((item) => item.action === "WAIT");
  if (wait) {
    return {
      title:
        intent === "protect"
          ? "Protect mode — no new risk today"
          : "Trade mode — waiting for confirmation",
      symbol: wait.symbol,
      blocker: wait.reason.missing,
      unlock: wait.reason.confirm,
      footnote: wait.reason.timing,
    };
  }

  if (capitalDecision.deploymentPercentage <= 0) {
    return {
      title:
        intent === "protect"
          ? "Capital is protected today"
          : "No setup ready to trade",
      blocker: "Nothing meets your entry rules yet.",
      unlock:
        intent === "protect"
          ? "Switch to Watch to see what's building, or check back tomorrow."
          : "Switch to Watch to track setups, or wait for tomorrow's scan.",
    };
  }

  return null;
}

export function runTodayWaitInsightSelfCheck(): void {
  const decision = buildCapitalDecision({
    intent: "grow",
    action: "wait",
    stock: "DIVISLAB",
    availableCash: 10_000,
    portfolioValue: 0,
    entryTiming: { enter: false },
  });

  const insight = buildTodayWaitInsight({
    intent: "grow",
    capitalDecision: decision,
  });

  if (!insight?.symbol || !insight.blocker.toLowerCase().includes("trigger")) {
    throw new Error("Today wait insight self-check failed");
  }
}
