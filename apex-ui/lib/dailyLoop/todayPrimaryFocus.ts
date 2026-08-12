import type { CapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import type { UserIntent } from "@/types/intent";
import {
  buildTodayWaitInsight,
  type TodayWaitInsight,
} from "@/lib/dailyLoop/todayWaitInsight";

export function resolvePrimaryTradeSymbol(input: {
  stock?: string;
  growDecision: CapitalDecision;
}): string | undefined {
  if (input.stock?.trim()) {
    return input.stock.trim().toUpperCase();
  }

  const primary =
    input.growDecision.actions.find((item) => item.isPrimary) ??
    input.growDecision.actions.find((item) => item.action === "WAIT") ??
    input.growDecision.actions.find((item) => item.action === "BUY");

  return primary?.symbol?.trim().toUpperCase();
}

export function buildAlignedWaitInsight(input: {
  intent: UserIntent;
  primarySymbol?: string;
  growDecision: CapitalDecision;
  protectDecision: CapitalDecision;
  openHoldingsCount?: number;
}): TodayWaitInsight | null {
  if (input.intent === "explore") {
    return null;
  }

  if (input.intent === "protect" && input.openHoldingsCount === 0) {
    const base = buildTodayWaitInsight({
      intent: input.intent,
      capitalDecision: input.protectDecision,
    });

    if (!base) {
      return {
        title: "Protect mode — cash only today",
        symbol: input.primarySymbol,
        blocker: "No open positions — capital stays in cash.",
        unlock: "Trade when a setup confirms and risk limits allow.",
        footnote: input.primarySymbol
          ? `Watching ${input.primarySymbol} — no new risk until you hold a position to trim.`
          : "No trim needed until you hold positions.",
      };
    }

    return {
      ...base,
      title: "Protect mode — cash only today",
      symbol: input.primarySymbol ?? base.symbol,
      blocker: "No open positions — capital stays in cash.",
      unlock: base.unlock || "Trade when a setup confirms and risk limits allow.",
      footnote: input.primarySymbol
        ? `Watching ${input.primarySymbol}. ${base.footnote ?? ""}`.trim()
        : base.footnote,
    };
  }

  const decision =
    input.intent === "protect" ? input.protectDecision : input.growDecision;
  const base = buildTodayWaitInsight({
    intent: input.intent,
    capitalDecision: decision,
  });

  if (!base) {
    return null;
  }

  const primary = input.primarySymbol;
  const protectSell = input.protectDecision.actions.find(
    (item) => item.action === "SELL",
  );

  if (input.intent === "protect" && protectSell) {
    return {
      ...base,
      title: "Portfolio risk — trim first",
      symbol: protectSell.symbol,
      blocker: protectSell.reason.missing || base.blocker,
      unlock: protectSell.reason.confirm || base.unlock,
      footnote:
        primary && primary !== protectSell.symbol.toUpperCase()
          ? `Next trade candidate: ${primary}. ${protectSell.reason.timing}`
          : protectSell.reason.timing || base.footnote,
    };
  }

  if (input.intent === "protect" && primary) {
    const protectWait = input.protectDecision.actions.find(
      (item) => item.action === "WAIT" && item.symbol.toUpperCase() === primary,
    );

    if (protectWait) {
      return {
        ...base,
        title: "Protect mode — no new risk today",
        symbol: primary,
        blocker: protectWait.reason.missing,
        unlock: protectWait.reason.confirm,
        footnote: protectWait.reason.timing,
      };
    }
  }

  if (input.intent === "grow" && primary) {
    const growWait = input.growDecision.actions.find(
      (item) =>
        item.action === "WAIT" && item.symbol.toUpperCase() === primary,
    );
    const growBuy = input.growDecision.actions.find(
      (item) => item.action === "BUY" && item.symbol.toUpperCase() === primary,
    );
    const focus = growWait ?? growBuy;

    if (focus) {
      return {
        ...base,
        title:
          focus.action === "BUY"
            ? "Trade mode — entry when confirmed"
            : "Trade mode — waiting for confirmation",
        symbol: primary,
        blocker: focus.reason.missing,
        unlock: focus.reason.confirm,
        footnote: focus.reason.timing,
      };
    }
  }

  if (primary && !base.symbol) {
    return { ...base, symbol: primary };
  }

  if (primary && base.symbol && base.symbol.toUpperCase() !== primary) {
    return {
      ...base,
      symbol: primary,
      footnote: base.footnote ?? `Aligned to today's primary setup: ${primary}.`,
    };
  }

  return base;
}

export function runTodayPrimaryFocusSelfCheck(): void {
  const grow = {
    mode: "grow" as const,
    actions: [
      {
        symbol: "DIVISLAB",
        action: "WAIT" as const,
        deployPercentage: 0,
        isPrimary: true,
        reason: {
          missing: "Breakout not confirmed.",
          confirm: "Buy above ₹8,585 on volume.",
          timing: "1–2 sessions",
        },
      },
    ],
  } as CapitalDecision;

  const protect = {
    mode: "protect" as const,
    actions: [
      {
        symbol: "GRASIM",
        action: "SELL" as const,
        deployPercentage: 25,
        isPrimary: true,
        reason: {
          missing: "Concentration not cleared.",
          confirm: "Trim before new buys.",
          timing: "Today",
        },
      },
    ],
  } as CapitalDecision;

  const protectInsight = buildAlignedWaitInsight({
    intent: "protect",
    primarySymbol: "DIVISLAB",
    growDecision: grow,
    protectDecision: protect,
  });

  if (
    protectInsight?.symbol !== "GRASIM" ||
    !protectInsight.footnote?.includes("DIVISLAB")
  ) {
    throw new Error("Today primary focus self-check failed: protect align");
  }

  const tradeInsight = buildAlignedWaitInsight({
    intent: "grow",
    primarySymbol: "DIVISLAB",
    growDecision: grow,
    protectDecision: protect,
  });

  if (tradeInsight?.symbol !== "DIVISLAB") {
    throw new Error("Today primary focus self-check failed: trade align");
  }

  const cashProtect = buildAlignedWaitInsight({
    intent: "protect",
    primarySymbol: "DIVISLAB",
    growDecision: grow,
    protectDecision: protect,
    openHoldingsCount: 0,
  });

  if (cashProtect?.blocker !== "No open positions — capital stays in cash.") {
    throw new Error("Today primary focus self-check failed: cash protect");
  }
}
